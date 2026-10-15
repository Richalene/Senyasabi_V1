-- SenyaSabi PostgreSQL schema for Supabase Auth + FastAPI sync
-- WARNING: RESET/DEVELOPMENT script. It drops application tables.
-- Do not run against a database containing data you need to preserve.

BEGIN;

-- ------------------------------------------------------------
-- RESET
-- ------------------------------------------------------------
DROP VIEW IF EXISTS public.v_user_statistics_live CASCADE;
DROP VIEW IF EXISTS public.v_module_progress_live CASCADE;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_auth_user() CASCADE;
DROP FUNCTION IF EXISTS public.refresh_user_statistics(UUID) CASCADE;
DROP FUNCTION IF EXISTS public.refresh_user_statistics(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS public.rebuild_user_statistics() CASCADE;
DROP FUNCTION IF EXISTS public.trg_refresh_stats() CASCADE;
DROP FUNCTION IF EXISTS public.set_updated_at() CASCADE;

DROP TABLE IF EXISTS
    public.quiz_attempts,
    public.minigame_attempts,
    public.lesson_progress,
    public.user_statistics,
    public.streaks,
    public.user_badges,
    public.badges,
    public.minigame_signs,
    public.minigames,
    public.quizzes,
    public.sign_media,
    public.lesson_media,
    public.lesson_signs,
    public.signs,
    public.lessons,
    public.modules,
    public.media_files,
    public.content_versions,
    public.refresh_tokens,
    public.users
CASCADE;

-- ------------------------------------------------------------
-- updated_at helper
-- ------------------------------------------------------------
CREATE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- ------------------------------------------------------------
-- USERS: profile keyed by the Supabase Auth UUID (same as JWT "sub")
-- ------------------------------------------------------------
CREATE TABLE public.users (
    user_id UUID PRIMARY KEY
        REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE
        CHECK (email IS NULL OR email = lower(email)),
    display_name VARCHAR(100),
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    dark_mode BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_users_username_lower
    ON public.users (lower(username));

-- Auto-create the profile on sign-up. Never blocks sign-up:
-- username is truncated, and a collision falls back to a generated one.
CREATE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    fallback_username TEXT := 'user_' || substr(replace(NEW.id::text, '-', ''), 1, 12);
    chosen_username TEXT;
BEGIN
    chosen_username := left(lower(
        COALESCE(NULLIF(trim(NEW.raw_user_meta_data ->> 'username'), ''), fallback_username)
    ), 50);

    BEGIN
        INSERT INTO public.users (user_id, username, email, display_name)
        VALUES (
            NEW.id,
            chosen_username,
            lower(NULLIF(NEW.email, '')),
            left(NULLIF(NEW.raw_user_meta_data ->> 'display_name', ''), 100)
        );
    EXCEPTION WHEN unique_violation THEN
        INSERT INTO public.users (user_id, username, email, display_name)
        VALUES (
            NEW.id,
            fallback_username,
            lower(NULLIF(NEW.email, '')),
            left(NULLIF(NEW.raw_user_meta_data ->> 'display_name', ''), 100)
        )
        ON CONFLICT DO NOTHING;
    END;

    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_auth_user();

-- ------------------------------------------------------------
-- CONTENT VERSIONS
-- ------------------------------------------------------------
CREATE TABLE public.content_versions (
    content_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_number INTEGER NOT NULL UNIQUE,
    released_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    changelog TEXT,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- MEDIA METADATA (binaries live in object storage)
-- ------------------------------------------------------------
CREATE TABLE public.media_files (
    media_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file_name VARCHAR(255),
    object_key TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL CHECK (media_type IN ('Image', 'Video')),
    width INTEGER CHECK (width IS NULL OR width > 0),
    height INTEGER CHECK (height IS NULL OR height > 0),
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    file_size BIGINT CHECK (file_size IS NULL OR file_size >= 0),
    checksum BYTEA,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_media_files_version ON public.media_files (content_version_id);

-- ------------------------------------------------------------
-- MODULES AND LESSONS
-- ------------------------------------------------------------
CREATE TABLE public.modules (
    module_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    module_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    module_order INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT
);

CREATE INDEX idx_modules_content_version ON public.modules (content_version_id);

CREATE TABLE public.lessons (
    lesson_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lesson_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    parent_module BIGINT NOT NULL
        REFERENCES public.modules(module_id) ON DELETE RESTRICT,
    lesson_order INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT
);

-- Partial: soft-deleted lessons don't hold an order slot.
-- To swap two lessons, move one to a temporary order value first.
CREATE UNIQUE INDEX idx_lessons_module_order
    ON public.lessons (parent_module, lesson_order)
    WHERE NOT is_deleted;

CREATE INDEX idx_lessons_content_version ON public.lessons (content_version_id);
CREATE INDEX idx_lessons_parent_module ON public.lessons (parent_module);

-- ------------------------------------------------------------
-- SIGNS + MAPPINGS (mappings are soft-deletable so deltas can sync removals)
-- ------------------------------------------------------------
CREATE TABLE public.signs (
    sign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sign_code VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    recognition_label VARCHAR(100) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT
);

CREATE INDEX idx_signs_content_version ON public.signs (content_version_id);

CREATE TABLE public.lesson_signs (
    lesson_id BIGINT NOT NULL
        REFERENCES public.lessons(lesson_id) ON DELETE RESTRICT,
    sign_id BIGINT NOT NULL
        REFERENCES public.signs(sign_id) ON DELETE RESTRICT,
    display_order INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT,
    PRIMARY KEY (lesson_id, sign_id)
);

CREATE INDEX idx_lesson_signs_sign ON public.lesson_signs (sign_id);
CREATE INDEX idx_lesson_signs_version ON public.lesson_signs (content_version_id);

CREATE TABLE public.sign_media (
    sign_id BIGINT NOT NULL
        REFERENCES public.signs(sign_id) ON DELETE RESTRICT,
    media_id BIGINT NOT NULL
        REFERENCES public.media_files(media_id) ON DELETE RESTRICT,
    media_role TEXT NOT NULL DEFAULT 'demonstration',
    display_order INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT,
    PRIMARY KEY (sign_id, media_id, media_role)
);

CREATE INDEX idx_sign_media_version ON public.sign_media (content_version_id);

CREATE TABLE public.lesson_media (
    lesson_id BIGINT NOT NULL
        REFERENCES public.lessons(lesson_id) ON DELETE RESTRICT,
    media_id BIGINT NOT NULL
        REFERENCES public.media_files(media_id) ON DELETE RESTRICT,
    media_role TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT,
    PRIMARY KEY (lesson_id, media_id, media_role)
);

CREATE INDEX idx_lesson_media_version ON public.lesson_media (content_version_id);

-- ------------------------------------------------------------
-- QUIZZES
-- Questions are generated on the fly from a module's signs (no question tables).
-- Signs for a module:
--   SELECT DISTINCT s.*
--   FROM public.signs s
--   JOIN public.lesson_signs ls ON ls.sign_id = s.sign_id AND NOT ls.is_deleted
--   JOIN public.lessons l ON l.lesson_id = ls.lesson_id AND NOT l.is_deleted
--   WHERE l.parent_module = :module_id AND NOT s.is_deleted;
-- Each sign yields two questions: camera recognition, and multiple choice
-- (3 random wrong choices from other signs in the module).
-- ------------------------------------------------------------
CREATE TABLE public.quizzes (
    quiz_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    module_id BIGINT NOT NULL
        REFERENCES public.modules(module_id) ON DELETE RESTRICT,
    title VARCHAR(100) NOT NULL,
    passing_score INTEGER NOT NULL DEFAULT 70
        CHECK (passing_score BETWEEN 0 AND 100),
    time_limit_seconds INTEGER CHECK (time_limit_seconds IS NULL OR time_limit_seconds > 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT
);

CREATE INDEX idx_quizzes_version ON public.quizzes (content_version_id);
CREATE INDEX idx_quizzes_module ON public.quizzes (module_id);

-- Client-generated UUID = idempotency key for offline sync.
-- Server should recompute `passed` from percentage vs quizzes.passing_score.
CREATE TABLE public.quiz_attempts (
    attempt_id UUID PRIMARY KEY,
    user_id UUID NOT NULL
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    quiz_id BIGINT NOT NULL
        REFERENCES public.quizzes(quiz_id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    score INTEGER CHECK (score IS NULL OR score >= 0),
    max_score INTEGER NOT NULL DEFAULT 100 CHECK (max_score > 0),
    percentage NUMERIC(5,2) CHECK (percentage IS NULL OR percentage BETWEEN 0 AND 100),
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    camera_accuracy NUMERIC(5,2) CHECK (camera_accuracy IS NULL OR camera_accuracy BETWEEN 0 AND 100),
    mc_accuracy NUMERIC(5,2) CHECK (mc_accuracy IS NULL OR mc_accuracy BETWEEN 0 AND 100),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now(),  -- server-assigned pull cursor
    CHECK (completed_at IS NULL OR completed_at >= started_at),
    CHECK (score IS NULL OR score <= max_score)
);

CREATE INDEX idx_quiz_attempts_user ON public.quiz_attempts (user_id, synced_at);
CREATE INDEX idx_quiz_attempts_quiz ON public.quiz_attempts (quiz_id);

-- ------------------------------------------------------------
-- MINIGAMES
-- ------------------------------------------------------------
CREATE TABLE public.minigames (
    minigame_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    minigame_code VARCHAR(100) NOT NULL UNIQUE,
    game_name VARCHAR(100) NOT NULL,
    game_type VARCHAR(50) NOT NULL,
    module_id BIGINT NOT NULL
        REFERENCES public.modules(module_id) ON DELETE RESTRICT,
    description TEXT,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT
);

CREATE INDEX idx_minigames_version ON public.minigames (content_version_id);
CREATE INDEX idx_minigames_module ON public.minigames (module_id);

CREATE TABLE public.minigame_signs (
    minigame_id BIGINT NOT NULL
        REFERENCES public.minigames(minigame_id) ON DELETE CASCADE,
    sign_id BIGINT NOT NULL
        REFERENCES public.signs(sign_id) ON DELETE RESTRICT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    content_version_id BIGINT NOT NULL
        REFERENCES public.content_versions(content_version_id) ON DELETE RESTRICT,
    PRIMARY KEY (minigame_id, sign_id)
);

CREATE INDEX idx_minigame_signs_version ON public.minigame_signs (content_version_id);

-- ------------------------------------------------------------
-- BADGES
-- ------------------------------------------------------------
CREATE TABLE public.badges (
    badge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    badge_code VARCHAR(100) NOT NULL UNIQUE,
    badge_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE public.user_badges (
    user_id UUID NOT NULL
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    badge_id BIGINT NOT NULL
        REFERENCES public.badges(badge_id) ON DELETE RESTRICT,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, badge_id)
);

CREATE INDEX idx_user_badges_badge ON public.user_badges (badge_id);

-- ------------------------------------------------------------
-- LESSON PROGRESS
-- client_updated_at: set by the device, used for conflict resolution.
-- updated_at: server-maintained, used as the pull cursor.
-- API merge rules: GREATEST() time_spent_seconds/completion_percentage,
-- and never regress status from 'Completed'.
-- ------------------------------------------------------------
CREATE TABLE public.lesson_progress (
    user_id UUID NOT NULL
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    lesson_id BIGINT NOT NULL
        REFERENCES public.lessons(lesson_id) ON DELETE RESTRICT,
    completion_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00
        CHECK (completion_percentage BETWEEN 0 AND 100),
    status TEXT NOT NULL DEFAULT 'Not Started'
        CHECK (status IN ('Not Started', 'In Progress', 'Completed')),
    last_accessed TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    time_spent_seconds BIGINT NOT NULL DEFAULT 0
        CHECK (time_spent_seconds >= 0),
    client_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, lesson_id),
    CHECK (status <> 'Completed' OR completed_at IS NOT NULL)
);

CREATE INDEX idx_lesson_progress_lesson ON public.lesson_progress (lesson_id);
CREATE INDEX idx_lesson_progress_user_updated ON public.lesson_progress (user_id, updated_at);

CREATE VIEW public.v_module_progress_live
WITH (security_invoker = true) AS
SELECT
    u.user_id,
    m.module_id,
    COUNT(l.lesson_id)::BIGINT AS total_lessons,
    COUNT(l.lesson_id) FILTER (WHERE lp.status = 'Completed')::BIGINT
        AS completed_lessons,
    COALESCE(
        ROUND(
            (
                SUM(
                    CASE
                        WHEN lp.status = 'Completed' THEN 100.0
                        ELSE COALESCE(lp.completion_percentage, 0)
                    END
                ) / NULLIF(COUNT(l.lesson_id), 0)
            )::NUMERIC,
            2
        ),
        0
    ) AS completion_percentage,
    CASE
        WHEN COUNT(l.lesson_id) = 0 THEN 'Not Started'
        WHEN COUNT(l.lesson_id) FILTER (WHERE lp.status = 'Completed') = COUNT(l.lesson_id)
            THEN 'Completed'
        WHEN COUNT(l.lesson_id) FILTER (
            WHERE COALESCE(lp.completion_percentage, 0) > 0
               OR lp.status IN ('In Progress', 'Completed')
        ) > 0 THEN 'In Progress'
        ELSE 'Not Started'
    END AS status,
    MAX(lp.last_accessed) AS last_accessed,
    CASE
        WHEN COUNT(l.lesson_id) > 0
         AND COUNT(l.lesson_id) FILTER (WHERE lp.status = 'Completed') = COUNT(l.lesson_id)
        THEN MAX(lp.completed_at)
        ELSE NULL
    END AS completed_at
FROM public.users u
CROSS JOIN public.modules m
LEFT JOIN public.lessons l
    ON l.parent_module = m.module_id
   AND l.is_active = TRUE
   AND l.is_deleted = FALSE
LEFT JOIN public.lesson_progress lp
    ON lp.user_id = u.user_id
   AND lp.lesson_id = l.lesson_id
WHERE m.is_active = TRUE
  AND m.is_deleted = FALSE
GROUP BY u.user_id, m.module_id;

-- ------------------------------------------------------------
-- MINIGAME ATTEMPTS (client-generated UUID, no server default on purpose:
-- a missing id should be an error, not a silent duplicate on retry)
-- ------------------------------------------------------------
CREATE TABLE public.minigame_attempts (
    game_attempt_id UUID PRIMARY KEY,
    user_id UUID NOT NULL
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    minigame_id BIGINT NOT NULL
        REFERENCES public.minigames(minigame_id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    score INTEGER CHECK (score IS NULL OR score >= 0),
    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    accuracy NUMERIC(5, 2) CHECK (accuracy IS NULL OR accuracy BETWEEN 0 AND 100),
    synced_at TIMESTAMPTZ NOT NULL DEFAULT now(),  -- server-assigned pull cursor
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

CREATE INDEX idx_minigame_attempts_user_minigame
    ON public.minigame_attempts (user_id, minigame_id);
CREATE INDEX idx_minigame_attempts_user_synced
    ON public.minigame_attempts (user_id, synced_at);
CREATE INDEX idx_minigame_attempts_completed
    ON public.minigame_attempts (user_id, completed_at)
    WHERE completed_at IS NOT NULL;

-- ------------------------------------------------------------
-- STREAKS
-- ------------------------------------------------------------
CREATE TABLE public.streaks (
    user_id UUID PRIMARY KEY
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    current_streak INTEGER NOT NULL DEFAULT 0 CHECK (current_streak >= 0),
    longest_streak INTEGER NOT NULL DEFAULT 0 CHECK (longest_streak >= 0),
    last_activity_date DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------
-- STATISTICS: live view + cached table, refreshed once per sync batch
-- (no per-row triggers)
-- ------------------------------------------------------------
CREATE VIEW public.v_user_statistics_live
WITH (security_invoker = true) AS
SELECT
    u.user_id,

    (SELECT COUNT(*)::BIGINT FROM public.lesson_progress lp
      WHERE lp.user_id = u.user_id AND lp.status = 'Completed') AS lessons_completed,

    (SELECT COUNT(*)::BIGINT FROM public.quiz_attempts qa
      WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL) AS quizzes_completed,

    (SELECT COUNT(*)::BIGINT FROM public.minigame_attempts ma
      WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL) AS minigames_completed,

    (SELECT COALESCE(SUM(qa.score), 0)::BIGINT FROM public.quiz_attempts qa
      WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL) AS total_quiz_score,

    (SELECT COALESCE(SUM(ma.score), 0)::BIGINT FROM public.minigame_attempts ma
      WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL) AS total_minigame_score,

    (
        SELECT AVG(a.accuracy)::NUMERIC(5, 2)
        FROM (
            SELECT qa.percentage AS accuracy
            FROM public.quiz_attempts qa
            WHERE qa.user_id = u.user_id
              AND qa.completed_at IS NOT NULL
              AND qa.percentage IS NOT NULL
            UNION ALL
            SELECT ma.accuracy
            FROM public.minigame_attempts ma
            WHERE ma.user_id = u.user_id
              AND ma.completed_at IS NOT NULL
              AND ma.accuracy IS NOT NULL
        ) a
    ) AS average_accuracy,

    (
        COALESCE((SELECT SUM(lp.time_spent_seconds)
                    FROM public.lesson_progress lp
                   WHERE lp.user_id = u.user_id), 0)
        + COALESCE((SELECT SUM(COALESCE(
                              qa.duration_seconds,
                              EXTRACT(EPOCH FROM (qa.completed_at - qa.started_at))))
                      FROM public.quiz_attempts qa
                     WHERE qa.user_id = u.user_id
                       AND qa.completed_at IS NOT NULL), 0)
        + COALESCE((SELECT SUM(ma.duration_seconds)
                      FROM public.minigame_attempts ma
                     WHERE ma.user_id = u.user_id
                       AND ma.completed_at IS NOT NULL), 0)
    )::BIGINT AS total_time_spent_seconds

FROM public.users u;

CREATE TABLE public.user_statistics (
    user_id UUID PRIMARY KEY
        REFERENCES public.users(user_id) ON DELETE CASCADE,
    lessons_completed BIGINT NOT NULL DEFAULT 0,
    quizzes_completed BIGINT NOT NULL DEFAULT 0,
    minigames_completed BIGINT NOT NULL DEFAULT 0,
    total_quiz_score BIGINT NOT NULL DEFAULT 0,
    total_minigame_score BIGINT NOT NULL DEFAULT 0,
    average_accuracy NUMERIC(5, 2),
    total_time_spent_seconds BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE FUNCTION public.refresh_user_statistics(p_user_id UUID)
RETURNS VOID
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_statistics (
        user_id, lessons_completed, quizzes_completed, minigames_completed,
        total_quiz_score, total_minigame_score, average_accuracy,
        total_time_spent_seconds, updated_at
    )
    SELECT
        user_id, lessons_completed, quizzes_completed, minigames_completed,
        total_quiz_score, total_minigame_score, average_accuracy,
        total_time_spent_seconds, now()
    FROM public.v_user_statistics_live
    WHERE user_id = p_user_id
    ON CONFLICT (user_id) DO UPDATE SET
        lessons_completed = EXCLUDED.lessons_completed,
        quizzes_completed = EXCLUDED.quizzes_completed,
        minigames_completed = EXCLUDED.minigames_completed,
        total_quiz_score = EXCLUDED.total_quiz_score,
        total_minigame_score = EXCLUDED.total_minigame_score,
        average_accuracy = EXCLUDED.average_accuracy,
        total_time_spent_seconds = EXCLUDED.total_time_spent_seconds,
        updated_at = now();
END;
$$;

CREATE FUNCTION public.rebuild_user_statistics()
RETURNS VOID
LANGUAGE plpgsql
SET search_path = public
AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT user_id FROM public.users LOOP
        PERFORM public.refresh_user_statistics(r.user_id);
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- updated_at triggers
-- ------------------------------------------------------------
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users', 'content_versions', 'media_files', 'modules', 'lessons',
        'signs', 'lesson_signs', 'sign_media', 'lesson_media', 'quizzes',
        'minigames', 'minigame_signs', 'lesson_progress', 'streaks'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%1$s_updated BEFORE UPDATE ON public.%1$I
             FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()', t);
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- BACKFILL profiles for auth users that already exist
-- (the sign-up trigger only fires for new users)
-- ------------------------------------------------------------
INSERT INTO public.users (user_id, username, email, display_name)
SELECT
    au.id,
    'user_' || substr(replace(au.id::text, '-', ''), 1, 12),
    lower(NULLIF(au.email, '')),
    left(NULLIF(au.raw_user_meta_data ->> 'display_name', ''), 100)
FROM auth.users au
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- RLS / privileges
-- All app data goes through FastAPI with server-side credentials
-- (postgres / service_role bypass RLS). No anon/authenticated policies.
-- ------------------------------------------------------------
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON SEQUENCES FROM anon, authenticated;

DO $$
DECLARE
    t RECORD;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
    END LOOP;
END;
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated, PUBLIC;

COMMIT;

-- After sync upserts, inside the same transaction, once per affected user:
--   SELECT public.refresh_user_statistics(:user_id);
-- To rebuild every cached summary:
--   SELECT public.rebuild_user_statistics();