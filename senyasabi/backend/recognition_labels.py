"""Canonical word-model labels, copied from the final training-script correction.

Learner display labels and stable sign codes deliberately keep their own identity.
"""


def normalize_label(value):
    return " ".join(
        str(value)
        .strip()
        .upper()
        .replace("’", "")
        .replace("'", "")
        .split()
    )
