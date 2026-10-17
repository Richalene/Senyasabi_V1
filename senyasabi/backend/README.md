# SenyaSabi Backend: Adding Data

This guide explains how to get content (media, modules, lessons, signs, quizzes,
minigames, badges) into the database.

## How the data is organized

| Store | Role | Who writes to it |
|---|---|---|
| **Supabase Postgres** | Authoritative store for content and user progress | Admin scripts (this guide) and the FastAPI backend |
| **Supabase Storage** (S3) | Binary files (videos and images) | You, by uploading |
| **SQLite** (`resources/data/senyasabi.db`) | Local cache on the desktop client | The app, via sync. For local dev/tests, `database/repository.py` |

Content flows one way: **Storage + dataset files -> Postgres -> (sync) -> client SQLite**.
You normally only touch Postgres and Storage.

Relationships:

```
content_versions
   |-- media_files            (one row per file in the bucket)
   |-- modules -> lessons -> lesson_signs -> signs -> sign_media -> media_files
   |-- quizzes -> quiz_signs -> signs
   `-- minigames (-> minigame_signs -> signs)
badges   (standalone)
```

Every content row has a `content_version_id`. Content tables use `*_code` columns
(`module_code`, `lesson_code`, `sign_code`, ...) as stable unique keys. The scripts
upsert on those, so **re-running is safe**.

## Prerequisites

1. Python env with the project requirements installed.
2. A `.env` in `senyasabi/` (never commit it):

```
DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/postgres   # Supabase session pooler
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...        # legacy HS256 projects only

S3_ENDPOINT=https://<ref>.supabase.co/storage/v1/s3
S3_REGION=<region>
S3_BUCKET=senyasabi-media
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

Use the `postgresql+psycopg://` prefix. `config.py` rewrites plain `postgresql://`,
but `tests/import_media.py` reads `DATABASE_URL` directly and would pick the wrong driver.

3. The Postgres schema is applied. `backend/database/postgre_schema.sql` is a
   **destructive reset script** (it drops all app tables). Only run it on a fresh or
   throwaway database.
4. A **private** Storage bucket matching `S3_BUCKET`.

Check everything is wired up:

```bash
cd senyasabi/tests
python import_media.py check          # tests Postgres + bucket access
python ../backend/scripts/verify_postgres_schema.py
```

## Step 1: Upload media

Upload files to the bucket with the Supabase dashboard, `rclone`, or `aws s3 sync`
against the S3 endpoint.

Layout and naming rules (the migration depends on them):

```
videos/words/greetings/hello.mp4
videos/words/greetings/good_morning.mp4
videos/numbers/one.mp4
images/alphabet/A.png
```

- Lowercase, underscores, no spaces.
- **The filename stem must match the sign's label after slugifying**
  (`Good morning` -> `good_morning`). That is how `migrate_content.py` links signs to files.
- Folder names are only used as a tiebreaker when two files share a stem
  (they're compared against the lesson and module names).
- Supported extensions: images `.png .jpg .jpeg .webp .gif`, videos `.mp4 .mov .webm .m4v`.
  Anything else is skipped.

## Step 2: Register the files in `media_files`

```bash
cd senyasabi/tests
python import_media.py import
```

For every object in the bucket this inserts or updates a `media_files` row with
`object_key`, `media_type`, `file_size`, SHA-256 `checksum`, and image dimensions.
It creates content version `1` if needed (`VERSION_NUMBER` in the script) and runs in a
single transaction, so it is all-or-nothing. Re-running updates existing rows by
`object_key`.

You never insert `media_files` rows by hand.

## Step 3: Describe the content

Edit the dataset files in `senyasabi/resources/data/`.

### `expected_dataset.md` (modules, lessons, signs)

```
## Module 4: Basic Communication      <- module
### Daily Greetings & Farewells       <- lesson
Good morning, Good afternoon, ...     <- signs, comma-separated
```

- Sign lines directly under a module (no `###`) go into a default lesson named after the module.
- Duplicate labels within a lesson are ignored.
- Codes are generated, e.g. lesson `<MODULE_CODE>_<LESSON_NAME>` and sign
  `<LESSON_CODE>_<LABEL>`, upper-snake-cased and truncated to 100 characters.

### `105labels.json` (recognition labels)

Maps a sign to the label the ML model outputs. Matching is by slugified label.
Signs not found here still import, with a derived label, and are listed in the
script summary. Check that list, because a wrong `recognition_label` means the camera
will never mark that sign correct.

### `minigames.json` (optional)

```json
{
  "minigames": [
    {
      "minigame_id": "sign_sprint",
      "game_name": "Sign Sprint",
      "game_type": "camera",
      "module_id": "alphabet",
      "config": { "rounds": 5, "time_limit": 60 }
    }
  ]
}
```

- `minigame_id` is stored as `minigame_code`.
- `module_id` is a **module code or slugified module name**, not a number. Unknown modules are skipped with a warning.
- `config` is free-form JSON and may differ per game.

## Step 4: Run the migration

```bash
cd senyasabi
python -m backend.scripts.migrate_content --dry-run   # runs everything, then rolls back
python -m backend.scripts.migrate_content             # writes to the database
```

What it creates, in order: content version, then modules, lessons, signs,
`lesson_signs`, `sign_media`, one quiz per module with its `quiz_signs`, badges
(static ones plus a `<MODULE>_MASTER` per module), and minigames.

Read the summary after each run:
- `created` vs `existing/unchanged` counts per table.
- **"signs skipped (no unused matching media_files row)"**: those signs were NOT created. Fix the filenames or upload the file, run `import_media.py import` again, then re-run the migration.
- **"signs not found in 105labels.json"**: fix labels as described above.

## Step 5: Verify

```bash
python tests/test_fetch.py 5   # presign + download 5 files, verify checksum/size/dimensions
```

Also check in the Supabase SQL editor:

```sql
SELECT m.title, count(DISTINCT l.lesson_id) lessons, count(DISTINCT ls.sign_id) signs
FROM modules m
LEFT JOIN lessons l ON l.parent_module = m.module_id AND NOT l.is_deleted
LEFT JOIN lesson_signs ls ON ls.lesson_id = l.lesson_id AND NOT ls.is_deleted
GROUP BY m.title, m.module_order ORDER BY m.module_order;

-- signs with no media
SELECT s.sign_code FROM signs s
LEFT JOIN sign_media sm ON sm.sign_id = s.sign_id AND NOT sm.is_deleted
WHERE sm.sign_id IS NULL AND NOT s.is_deleted;
```

## Common tasks

**Add a new sign:** upload the file, run `import_media.py import`, add the label under the
right lesson in `expected_dataset.md`, add it to `105labels.json`, run the migration.

**Replace a file:** upload under the same key and re-run `import_media.py import`.
The checksum and `updated_at` change.

**Remove content:** the scripts never delete. Soft-delete by hand so clients can sync
the removal:

```sql
UPDATE signs SET is_deleted = true WHERE sign_code = '...';
UPDATE lesson_signs SET is_deleted = true WHERE sign_id = (SELECT sign_id FROM signs WHERE sign_code = '...');
```

**Release a new content version:** insert a `content_versions` row with the next
`version_number` and `is_published = true`, then update `VERSION_NUMBER` in
`import_media.py` and `CONTENT_VERSION_NUMBER` in `migrate_content.py` (keep them equal).
Clients sync "since version N" using these numbers.

**Add a badge:** add a tuple to `STATIC_BADGES` in `migrate_content.py` and re-run.

**Add a per-category quiz** (e.g. `GREETING_QUIZ` with `category_code`): the script only
makes one quiz per module. Insert the `quizzes` row (`config` is JSONB, e.g.
`{"shuffle": true, "question_types": ["camera","identification"]}`), then insert
`quiz_signs` rows for its signs.

## Local SQLite (dev and tests only)

`backend/database/init_db.py` creates `senyasabi.db` from `sqlite_schema.sql` on first run
and seeds content version 1. For tests, seed with the helpers in
`backend/database/repository.py`
(`create_module`, `create_lesson`, `create_sign`, `link_sign_to_lesson`, `create_quiz`,
`create_minigame`, `create_badge`, ...); see `tests/tests_backend_smoke.py`.
IDs are passed in explicitly because in production they are server-assigned.
If you change `models.py`, update `sqlite_schema.sql` too. `tests/test_schema_drift.py` checks this.

To rebuild the local DB: `python -m backend.database.init_db --rebuild`.

## Gotchas (read before your first run)

1. **No media means no sign.** A sign with no matching `media_files` row is skipped
   entirely, so it never gets a `signs` row, a quiz entry, or a lesson link. Always import media first.
2. **Label vs. file naming.** Dataset labels like `1`, `I'm fine`, `What is your name?` slugify to
   `1`, `i_m_fine`, `what_is_your_name`. Name files to match, or `105labels.json` lookups
   (e.g. `IM FINE` -> `im_fine`) will miss.
3. **Dataset vs. model labels.** `expected_dataset.md` (7 modules) and `105labels.json`
   (categories like SURVIVAL, COLOR, FOOD) don't line up one-to-one. Only labels present in
   both get a model-accurate `recognition_label`.
4. **Run locations matter.** `import_media.py` imports itself by name, so run it from `tests/`.
   `migrate_content.py` imports `backend.*`, so run it with `-m` from `senyasabi/`.
5. **Never ship server secrets in the client.** The S3 keys and service-role key are for
   admin scripts and FastAPI only. The desktop app should only talk to the API.
