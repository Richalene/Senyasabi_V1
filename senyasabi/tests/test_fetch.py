import hashlib, sys, time
from pathlib import Path

import requests
from PIL import Image
from sqlalchemy import text

from import_media import get_engine, get_s3, BUCKET   # reuse the admin helpers

CACHE_DIR = Path("./_test_cache")
CACHE_DIR.mkdir(exist_ok=True)


def presign(s3, key, expires=300):
    # In the real app, this runs on your backend, never in the PyQt client
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=expires
    )


def fetch(url, dest: Path) -> bytes:
    """Client side: only needs the URL. Returns SHA-256 of what it downloaded."""
    sha = hashlib.sha256()
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
                sha.update(chunk)
    return sha.digest()


def main(limit=None):
    s3, engine = get_s3(), get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT media_id, object_key, media_type, width, height, file_size, checksum "
            "FROM media_files WHERE NOT is_deleted ORDER BY media_id"
        )).mappings().all()
    rows = rows[:limit] if limit else rows

    ok = 0
    for r in rows:
        key = r["object_key"]
        dest = CACHE_DIR / f"{r['media_id']}_{Path(key).name}"
        try:
            url = presign(s3, key)
            digest = fetch(url, dest)
            problems = []
            if digest != bytes(r["checksum"]):
                problems.append("checksum mismatch")
            if r["file_size"] and dest.stat().st_size != r["file_size"]:
                problems.append("size mismatch")
            if r["media_type"] == "Image":
                with Image.open(dest) as im:
                    if (r["width"], r["height"]) != im.size:
                        problems.append(f"dimensions {im.size} != {(r['width'], r['height'])}")
            print(("FAIL " + ", ".join(problems)) if problems else "OK  ", key)
            ok += not problems
        except Exception as e:
            print("FAIL", key, "->", e)
    print(f"\n{ok}/{len(rows)} files fetched and verified")

    # Negative tests on the first file
    if rows:
        key = rows[0]["object_key"]
        url = presign(s3, key)
        bare = url.split("?")[0]
        print("\nUnsigned URL status (want 400/401/403):", requests.get(bare, timeout=15).status_code)
        short = presign(s3, key, expires=1)
        time.sleep(3)
        print("Expired URL status (want 400/403):", requests.get(short, timeout=15).status_code)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)