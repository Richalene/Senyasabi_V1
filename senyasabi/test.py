from pathlib import Path
from PIL import Image

path = Path(
    "senyasabi/cache/media/47_M_new.png"
).resolve()

try:
    img = Image.open(path)
    print("Format:", img.format)
    print("Mode:", img.mode)
    print("Dimensions:", img.size)
    img.verify()
    print("Image verification: PASSED")
except Exception as e:
    print("Image loading failed:", repr(e))