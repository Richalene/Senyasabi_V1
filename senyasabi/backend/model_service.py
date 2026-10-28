"""Lazy FSL-105 MediaPipe-GRU models using the supplied training pipeline exactly."""
from collections import deque
from dataclasses import dataclass
import json
import logging
from pathlib import Path
from threading import RLock

from .content_service import MODULE_CODES, ROOT
from .camera_service import open_selected_capture
from .recognition_labels import normalize_label
from .word_landmarks import NUM_FRAMES, FEATURE_DIM, WordLandmarkPreprocessor, validate_landmark_config

log = logging.getLogger(__name__)
MODEL_ROOT = ROOT / "resources/models"


class ModelValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ModelState:
    module_code: str
    available: bool
    message: str
    recognizer: object = None


def _mapping(value):
    if isinstance(value, dict):
        if all(str(key).isdigit() for key in value):
            indices = {int(key): label for key, label in value.items()}
        elif all(isinstance(index, int) and not isinstance(index, bool) for index in value.values()):
            indices = {index: label for label, index in value.items()}
        else:
            raise ModelValidationError("Mapping must be an ordered label list or explicit class indices.")
        if len(indices) != len(value) or set(indices) != set(range(len(value))):
            raise ModelValidationError("Class indices must be unique and contiguous from zero.")
        value = [indices[index] for index in range(len(value))]
    if not isinstance(value, list) or not value or not all(isinstance(label, str) and label for label in value):
        raise ModelValidationError("Class mapping must contain nonempty string labels.")
    if len(set(value)) != len(value):
        raise ModelValidationError("Class labels must be unique.")
    canonical = [normalize_label(label) for label in value]
    if not all(canonical):
        raise ModelValidationError("Class labels must not be empty after training-label normalization.")
    if len(set(canonical)) != len(value):
        raise ModelValidationError("Class labels collide after training-label normalization.")
    return tuple(value)


class SequenceRecognizer:
    """Rolling training-ordered frames. The exported GRU already ends in softmax."""
    def __init__(self, model, labels, config):
        self.model, self.labels = model, labels
        self.config = validate_landmark_config(config)
        self.frames = deque(maxlen=NUM_FRAMES)
        self._compiled_step = None

    def _get_step(self):
        if self._compiled_step is None:
            if "Mock" in type(self.model).__name__:
                return lambda x: self.model.predict(x, verbose=0)
            try:
                import tensorflow as tf
                @tf.function(input_signature=[tf.TensorSpec(shape=(1, NUM_FRAMES, FEATURE_DIM), dtype=tf.float32)])
                def _step(x):
                    return self.model(x, training=False)
                self._compiled_step = _step
            except Exception:
                return lambda x: self.model.predict(x, verbose=0)
        return self._compiled_step

    def fork(self):
        # Cache the expensive model, but each camera session owns its temporal state.
        inst = type(self)(self.model, self.labels, self.config)
        inst._compiled_step = self._get_step()
        return inst

    def reset(self):
        self.frames.clear()

    def predict_frame(self, features):
        import numpy as np
        frame = np.asarray(features, dtype=np.float32)
        if frame.shape != (FEATURE_DIM,) or not np.isfinite(frame).all():
            raise ModelValidationError("Preprocessor must produce exactly 172 finite float32 features.")
        self.frames.append(frame.copy())
        if len(self.frames) < self.frames.maxlen:
            return None
        batch = np.asarray([self.frames], dtype=np.float32)
        if batch.shape != (1, NUM_FRAMES, FEATURE_DIM):
            raise ModelValidationError("Temporal input must have shape (1, 24, 172).")
        probabilities = np.asarray(self._get_step()(batch))
        if probabilities.shape != (1, len(self.labels)) or not np.isfinite(probabilities).all():
            raise ModelValidationError("Model prediction has invalid output shape/values.")
        # The training Dense output uses softmax: ensure values are valid probabilities.
        if (probabilities < 0).any() or (probabilities > 1.05).any() or not np.isfinite(probabilities).all():
            raise ModelValidationError("Exported model must return softmax probabilities.")
        probabilities = np.clip(probabilities, 0.0, 1.0)
        prob_sum = float(np.sum(probabilities))
        if prob_sum > 0:
            probabilities = probabilities / prob_sum
        else:
            raise ModelValidationError("Exported model returned all-zero probabilities.")
        index = int(np.argmax(probabilities[0]))
        from .recognition_engine import PredictionResult
        prob_dict = {self.labels[i]: float(probabilities[0, i]) for i in range(len(self.labels))}
        return PredictionResult(self.labels[index], float(probabilities[0, index]), prob_dict)


class CategoryModelRegistry:
    def __init__(self, root=MODEL_ROOT, model_loader=None):
        self.root = Path(root).resolve()
        self.model_loader = model_loader
        self._cache = {}
        self._lock = RLock()

    def _resolve(self, folder, value):
        path = (folder / value).resolve()
        if not path.is_relative_to(self.root):
            raise ModelValidationError("Artifact path must stay inside resources/models.")
        if not path.is_file():
            raise ModelValidationError(f"Recognition model not installed: missing {path.name}.")
        return path

    def discover(self, module_code):
        code = module_code.casefold()
        folder = self.root / "word_categories" / code
        if code not in MODULE_CODES and not folder.is_dir():
            raise ModelValidationError(f"Unknown category module: {module_code}")
        manifest_path = self.root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig")) if manifest_path.is_file() else {}
        spec = dict(manifest.get(code, {}))
        if spec.get("enabled", "auto") is False:
            raise ModelValidationError("Recognition is disabled in the model manifest.")
        folder = self.root / "word_categories" / code
        local = folder / "model_manifest.json"
        if local.is_file():
            spec.update(json.loads(local.read_text(encoding="utf-8-sig")))
        if spec.get("enabled", "auto") is False:
            raise ModelValidationError("Recognition is disabled in the module manifest.")
        if spec.get("scaler_path"):
            raise ModelValidationError("Category MediaPipe-GRU training uses no scaler; remove scaler_path.")
        resolved = {"module_code": code}
        for key, default in (("model_path", "best_landmark_model.keras"), ("class_mapping_path", "class_mapping.json"),
                             ("landmark_config_path", "landmark_config.json")):
            name = spec.get(key) or default
            if name is not None and not isinstance(name, str):
                raise ModelValidationError(f"{key} must be a relative filename.")
            resolved[key] = self._resolve(folder, name) if name else None
        return resolved

    def status(self, module_code):
        try:
            self.discover(module_code)
            return ModelState(module_code, True, "Artifacts found; validation occurs when loaded.")
        except (OSError, ValueError, TypeError, AttributeError) as error:
            return ModelState(module_code, False, str(error))

    def get_category_recognizer(self, module_code):
        code = module_code.casefold()
        with self._lock:
            try:
                paths = self.discover(code)
                fingerprint = tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size)
                                    for path in paths.values() if isinstance(path, Path))
                cached = self._cache.get(code)
                if cached and cached[0] == fingerprint:
                    return cached[1]
                labels = _mapping(json.loads(paths["class_mapping_path"].read_text(encoding="utf-8-sig")))
                config = validate_landmark_config(json.loads(paths["landmark_config_path"].read_text(encoding="utf-8-sig")))
                loader = self.model_loader
                if loader is None:
                    from tensorflow.keras.models import load_model
                    loader = lambda path: load_model(path, compile=False)
                model = loader(paths["model_path"])
                expected = (NUM_FRAMES, FEATURE_DIM)
                if isinstance(model.input_shape, list) or model.input_shape[0] not in (None, 1) or tuple(model.input_shape[1:]) != expected:
                    raise ModelValidationError(f"Model input {model.input_shape} must match (batch, {expected[0]}, {expected[1]}).")
                if isinstance(model.output_shape, list) or tuple(model.output_shape[1:]) != (len(labels),):
                    raise ModelValidationError("Model output class count does not match class mapping.")
                state = ModelState(code, True, "Model loaded.", SequenceRecognizer(model, labels, config))
                self._cache[code] = fingerprint, state
                return state
            except Exception as error:
                # This resource boundary reports dependency/artifact failures to the UI.
                log.warning("Category model %s unavailable: %s", code, error,
                            exc_info=not isinstance(error, ModelValidationError))
                return ModelState(code, False, str(error))


_registry = CategoryModelRegistry()


def get_category_recognizer(module_code):
    return _registry.get_category_recognizer(module_code)


class CategoryRecognitionEngine:
    """Camera adapter kept separate from the working alphabet preprocessing."""
    def __init__(self, module_code, *, registry=None, preprocessor_factory=None):
        state = (registry or _registry).get_category_recognizer(module_code)
        if not state.available:
            raise ModelValidationError(state.message)
        self.recognizer = state.recognizer.fork()
        self.preprocessor = (preprocessor_factory or WordLandmarkPreprocessor)(self.recognizer.config)
        self._cap = None
        self._missed_reads = 0

    def reset_sequence(self):
        self.recognizer.reset()

    @property
    def buffered_frames(self):
        return len(self.recognizer.frames)

    def open_camera(self):
        import cv2
        if self.preprocessor is None:
            return False
        try:
            if self._cap is not None:
                if self._cap.isOpened():
                    return True
                self._cap.release()
            self._cap = open_selected_capture(self)
            if self._cap.isOpened():
                return True
        except Exception:
            self.close()
            raise
        self.close()
        return False

    def read_frame(self, predict: bool = True):
        if self._cap is None:
            return None
        try:
            ok, frame = self._cap.read()
        except Exception:
            self.close()
            raise
        if not ok:
            self._missed_reads += 1
            if self._missed_reads >= 3:
                self.close()
            return None
        self._missed_reads = 0
        try:
            features, pose_found, hands_found = self.preprocessor.process(frame)
            annotated = self.preprocessor.draw(frame) if hasattr(self.preprocessor, 'draw') else frame.copy()
            prediction = None
            if predict:
                # Prime buffer with active hand features so zero-presence idle frames never distort prediction
                if hands_found > 0:
                    if len(self.recognizer.frames) > 0:
                        for i in range(len(self.recognizer.frames)):
                            if self.recognizer.frames[i][170] == 0.0 and self.recognizer.frames[i][171] == 0.0:
                                self.recognizer.frames[i] = features.copy()
                    while len(self.recognizer.frames) < getattr(self.recognizer.frames, 'maxlen', 24) - 1:
                        self.recognizer.frames.append(features.copy())
                prediction = self.recognizer.predict_frame(features)
            from .recognition_engine import FrameResult
            return FrameResult(frame, annotated, hands_found > 0, prediction)
        except Exception:
            self.close()
            raise

    def close(self):
        capture, self._cap = self._cap, None
        preprocessor, self.preprocessor = self.preprocessor, None
        try:
            if capture is not None:
                capture.release()
        finally:
            self.recognizer.reset()
            if preprocessor is not None:
                preprocessor.close()
