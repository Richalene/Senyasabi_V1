# Models and lesson media

Missing resources must stay unavailable: never fabricate predictions, class mappings,
pickles or videos, and never silently use the legacy `data/105words.keras`.

## Category models

Put trusted exported artifacts in `models/word_categories/<module_code>/`.
Modules: greeting, survival, number, calendar, days, family, relationships, color,
food, drink. Alphabet keeps using `data/alphabet.keras` and
`data/alphabetscaler.pkl`; `models/alphabet/` is reserved for future use.

Copy these three real exports into each module folder (no edits to their JSON
schema are needed):

- `best_landmark_model.keras`
- `class_mapping.json`
- `landmark_config.json`

`backend/model_service.py` lazy-loads only the selected module and caches the
loaded model. `models/manifest.json` contains its filenames/settings;
`enabled: "auto"` uses installed resources and `false` disables a module.
Custom filenames may be set in a local `model_manifest.json`, for example:

```json
{
  "model_path": "actual_export.keras",
  "class_mapping_path": "actual_classes.json",
  "landmark_config_path": "actual_training_config.json"
}
```

Paths are relative to the module folder and must stay inside `models/`.
Without overrides it selects `best_landmark_model.keras` explicitly, so a training
folder's warmup/checkpoint files cannot be selected accidentally. **Category
models use no scaler.** `alphabetscaler.pkl` belongs only to the separate alphabet
pipeline; category scaler configuration is rejected.

Mapping formats: an ordered string list, explicit index-to-label object, or
label-to-index object. Indices must be unique and contiguous from zero; the loader
never invents or rearranges class identities.

`backend/word_landmarks.py` reuses `xyz()` and `frame_to_features()` from the supplied
`fsl_mediapipe_training.py`; only a lazy MediaPipe import was added to the latter.
It validates the exported `num_frames: 24`, `feature_dim: 172`, `num_hands: 2`,
`pose_indices`, `feature_order` and `normalization` against that exact pipeline.
No preprocessor registration or alternate config keys are required.

Shared MediaPipe Tasks assets must also be installed in `models/mediapipe/`:
`hand_landmarker.task` and `pose_landmarker_lite.task`. These are the same detector
assets named in the training script, separate from the category classifiers.
They are currently absent; the app does not download or fabricate them. Missing
assets report an unavailable state before opening a camera.

Training pinned MediaPipe 0.10.30; this desktop app retains its existing 0.10.18
dependency to protect the alphabet recognizer. Its Tasks API accepts the required
options; real detector/model accuracy still needs validation with the actual assets.

Runtime converts unmirrored BGR to RGB and uses HandLandmarker (two hands) and
PoseLandmarker (one pose) in the training script's IMAGE mode with its 0.35
detection/presence thresholds. Features are 44 selected pose xyz/visibility values,
63 left-hand xyz, 63 right-hand xyz, then two presence flags. The exact shoulder
origin/scale, missing-pose fallback, handedness leftovers and zero-filling logic
remain unchanged. Every feature frame, including missing detections, enters the
rolling buffer. No inference runs before 24 frames; input is `(1, 24, 172)` float32.
The exported model already ends in softmax, so confidence is not softmaxed again.

`backend/recognition_labels.py` copies the script's **final** normalization:
strip, uppercase, remove straight/curly apostrophes, collapse whitespace. This is
used for word recognition only. Learner labels, stable sign codes, quiz/spelling
answers and alphabet recognition retain their own behavior.

The loader validates `(batch, 24, 172)` and output mapping count, and caches by
artifact fingerprint. Each camera session owns a separate temporal buffer. Back,
hide and exit stop frame timers, clear the buffer, release the camera, and close
both Tasks detectors. No training or model architecture recreation occurs.
`CategoryModelRegistry.status()` checks discovery; `get_category_recognizer()`
performs full validation and returns an availability/message/result record.

## Videos and database adapters

Put videos in `videos/word_categories/<module_code>/<sign_code>.mp4` or
`videos/alphabet/<letter>.mp4` (lowercase codes). Supported discovery extensions:
`.mp4`, `.webm`, `.mov`, `.m4v`. List the content service's `SignRecord` objects to
see stable codes; bundled codes derive from labels, e.g. `good_morning`, `bread`.
Training/source IDs are not treated as database IDs.

For arbitrary filenames, add an entry to `videos/media_manifest.json`, e.g.
`{"food": {"bread": "word_categories/food/my_bread_export.mp4"}}`.
Do not add entries until the real files exist. The reusable player reports absent
or unplayable media and leaves navigation available.

`backend/content_service.py` supplies logical `SignRecord` objects. A DB/cache
adapter can replace its repository while retaining stable module/sign codes and
supplying real integer sign/lesson/media IDs. `backend/media_service.py` accepts
a repository with `get_media_for_sign(sign_record) -> MediaRecord | None`.
The existing database package is currently reserved; no competing database,
Supabase client or cache was introduced.

Resolution precedence: existing cached local path, bundled file/manifest, then
unavailable. Storage key, remote URL, media ID, checksum and version are preserved
for a future existing-backend cache adapter to download/cache. The UI never
fetches Supabase or remote media itself. Adapters should translate offline access
failures into `OSError`/`ConnectionError`/`TimeoutError`; programming errors remain
visible. No binaries are stored in DB records.

Until word videos/models arrive, the module quiz explicitly uses offline alphabet
decoding from that module's content. Results and auth remain session-only; existing
statistics repositories retain their defaults/sample leaderboard.

## Run and smoke test

### Camera setup

The first usable camera activity offers **Set Up Camera / Not Now**. Setup lists
real Qt camera names, requires a successful preview, then saves the selected
stable device ID and consent in local `QSettings` (`SenyaSabi/SenyaSabi`).
Nothing is stored in the application database. No camera is opened at startup,
on device discovery, or when declining setup.

Use **Main Menu → Menu → Camera Settings** to change devices. Preview stops before
the dialog closes or a lesson opens. A disconnected saved camera is never silently
replaced by another device. **Choose by device number** is an explicit OpenCV
fallback for devices Qt cannot enumerate; its numeric limitation stays inside
`backend/camera_service.py`. Qt device names are never guessed from OpenCV indices.

All camera lessons and FingerSpell Quest consume BGR frames from the same service.
Qt capture runs on its own event-loop thread; camera/model initialization uses the
existing loading overlay. Failed reads stop capture and expose Retry / Choose Camera
and Back. Live frames are neither recorded nor uploaded. Category feature ordering,
24×172 sequences, scaling and alphabet recognition mathematics are unchanged.

Smoke test: DEV Login → Start Learning → Alphabet → Lesson 1 → Set Up Camera →
choose device → Test Camera → Save / Use Camera → Back → reopen. Then open
FingerSpell Quest and confirm the same device is used. Change the device in Camera
Settings and repeat. Also test Not Now / Continue Without Camera, a busy/disconnected
camera, Sign Sprint, Sign Detective and My Statistics. Physical-camera behavior and
OS privacy prompts require a hands-on check; automated tests use injected captures.

### Launch and navigation

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe senyasabi/main.py
.\.venv\Scripts\python.exe -m unittest discover -s senyasabi/tests -v
```

Welcome → Continue → Landing → Login → DEV → Main Menu → Start Learning →
Module Map (hover) → Food → Lesson (missing-resource message, browse, Back) →
Food Quiz → Back → Sign Sprint (Play/Pause/Replay/answer/Next) → Back →
FingerSpell Quest (camera/letters/Back) → Sign Detective (answer/Next) → Back →
Module Map → Alphabet → Lesson 1 (real camera signing, Back) → Module Map →
Main Menu → My Stats → Leaderboard → Back → Main Menu → Logout → Login.
Use Escape to leave fullscreen and F11 to toggle. Reopen the alphabet lesson and
Quest to confirm the physical camera is released and can be acquired again.

`screens/image_card.py` provides centered aspect-fill cropping with painter-based
rounded clipping for future character renders. Current supplied PNGs are full
screen artwork/templates, so they are preserved rather than cropped as portraits.
