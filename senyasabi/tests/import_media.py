import hashlib, io, os, sys
from pathlib import PurePosixPath

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

load_dotenv()

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".m4v"}
BUCKET = os.environ["S3_BUCKET"]
VERSION_NUMBER = 1


def get_engine():
    return create_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )


def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        region_name=os.environ["S3_REGION"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        config=Config(s3={"addressing_style": "path"}),
    )


def iter_objects(s3):
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/") or key.endswith(".emptyFolderPlaceholder"):
                continue
            yield obj


def check():
    with get_engine().connect() as conn:
        print("Postgres OK:", conn.execute(text("select version()")).scalar())
        tables = conn.execute(text(
            "select count(*) from information_schema.tables where table_schema='public'"
        )).scalar()
        print("Public tables:", tables)

    s3 = get_s3()
    s3.head_bucket(Bucket=BUCKET)
    objs = list(iter_objects(s3))
    print(f"Storage OK: bucket '{BUCKET}' has {len(objs)} objects")
    for o in objs[:5]:
        print("  ", o["Key"], o["Size"])


def inspect(s3, key, ext):
    """Download once: SHA-256 for everything, dimensions for images."""
    body = s3.get_object(Bucket=BUCKET, Key=key)["Body"]
    sha = hashlib.sha256()
    buf = io.BytesIO() if ext in IMAGE_EXT else None
    for chunk in iter(lambda: body.read(1024 * 1024), b""):
        sha.update(chunk)
        if buf is not None:
            buf.write(chunk)
    width = height = None
    if buf is not None:
        try:
            buf.seek(0)
            with Image.open(buf) as im:
                width, height = im.size
        except Exception as e:
            print(f"  ! couldn't read dimensions for {key}: {e}")
    return sha.digest(), width, height


def import_media():
    s3, engine = get_s3(), get_engine()
    with engine.begin() as conn:  # one transaction: all or nothing
        version_id = conn.execute(text("""
            INSERT INTO content_versions (version_number, changelog)
            VALUES (:n, 'Initial media import')
            ON CONFLICT (version_number) DO UPDATE SET version_number = EXCLUDED.version_number
            RETURNING content_version_id
        """), {"n": VERSION_NUMBER}).scalar_one()

        count = 0
        for obj in iter_objects(s3):
            key = obj["Key"]
            ext = PurePosixPath(key).suffix.lower()
            if ext in IMAGE_EXT:
                media_type = "Image"
            elif ext in VIDEO_EXT:
                media_type = "Video"
            else:
                print(f"skip (unknown type): {key}")
                continue

            checksum, w, h = inspect(s3, key, ext)
            conn.execute(text("""
                INSERT INTO media_files
                  (file_name, object_key, media_type, width, height,
                   file_size, checksum, content_version)
                VALUES (:name, :key, :type, :w, :h, :size, :sum, :ver)
                ON CONFLICT (object_key) DO UPDATE SET
                  width = EXCLUDED.width, height = EXCLUDED.height,
                  file_size = EXCLUDED.file_size, checksum = EXCLUDED.checksum,
                  updated_at = now()
            """), {
                "name": PurePosixPath(key).name, "key": key, "type": media_type,
                "w": w, "h": h, "size": obj["Size"], "sum": checksum, "ver": version_id,
            })
            count += 1
            print(f"ok: {key}")
        print(f"Imported/updated {count} files under content version {VERSION_NUMBER}")


if __name__ == "__main__":
    {"check": check, "import": import_media}[sys.argv[1] if len(sys.argv) > 1 else "check"]()