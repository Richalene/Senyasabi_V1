"""
Training Pipeline Configuration: 7 Target Curriculum Modules

Defines the exact class mapping, feature configuration, and model parameters
for the 7 curriculum categories (excluding COLOR, FOOD, DRINK, and RELATIONSHIPS).
"""
import json
from pathlib import Path
from typing import Dict, List

# Target 7 categories and their exact classes
TARGET_CATEGORIES: Dict[str, List[str]] = {
    "ALPHABET": [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ],
    "NUMBER": [
        "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN"
    ],
    "FAMILY": [
        "FATHER", "MOTHER", "SON", "DAUGHTER", "GRANDFATHER", "GRANDMOTHER",
        "UNCLE", "AUNTIE", "PARENTS", "COUSIN"
    ],
    "GREETING": [
        "GOOD MORNING", "GOOD AFTERNOON", "GOOD EVENING", "HELLO", "HOW ARE YOU",
        "IM FINE", "NICE TO MEET YOU", "THANK YOU", "YOURE WELCOME", "SEE YOU TOMORROW"
    ],
    "SURVIVAL": [
        "YES", "NO", "UNDERSTAND", "DON'T UNDERSTAND", "KNOW", "DON'T KNOW",
        "CORRECT", "WRONG", "SLOW", "FAST"
    ],
    "DAYS": [
        "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"
    ],
    "CALENDAR": [
        "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
        "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"
    ]
}

EXCLUDED_CATEGORIES = ["COLOR", "FOOD", "DRINK", "RELATIONSHIPS"]

# Training pipeline constants matching MediaPipe GRU architecture
PIPELINE_CONFIG = {
    "num_frames": 24,
    "feature_dim": 172,
    "num_hands": 2,
    "pose_indices": [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    "feature_order": "pose xyz+visibility, left hand xyz, right hand xyz, presence flags",
    "normalization": "shoulder midpoint origin and shoulder-width scale"
}


def get_class_mapping(category: str) -> Dict[int, str]:
    """Return 0-indexed contiguous mapping for a given category."""
    cat = category.upper()
    if cat not in TARGET_CATEGORIES:
        raise ValueError(f"Category '{category}' is excluded or not in target curriculum.")
    classes = TARGET_CATEGORIES[cat]
    return {idx: label for idx, label in enumerate(classes)}


def export_training_configs(output_dir: Path | str = "senyasabi/resources/models/training_configs"):
    """Export canonical class_mapping.json and landmark_config.json for each module."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    summary = {
        "num_categories": len(TARGET_CATEGORIES),
        "total_classes": sum(len(c) for c in TARGET_CATEGORIES.values()),
        "categories": {cat: len(classes) for cat, classes in TARGET_CATEGORIES.items()},
        "excluded": EXCLUDED_CATEGORIES
    }
    (out_path / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for cat_name, classes in TARGET_CATEGORIES.items():
        cat_dir = out_path / cat_name.lower()
        cat_dir.mkdir(parents=True, exist_ok=True)

        mapping = {idx: label for idx, label in enumerate(classes)}
        (cat_dir / "class_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        (cat_dir / "landmark_config.json").write_text(json.dumps(PIPELINE_CONFIG, indent=2), encoding="utf-8")

    print(f"Exported training configs for all 7 categories ({summary['total_classes']} total classes) to {out_path}")


if __name__ == "__main__":
    export_training_configs()

