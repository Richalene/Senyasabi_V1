-- ============ RESET DATABASE ============
DROP VIEW IF EXISTS v_user_statistics_live CASCADE;

DROP TABLE IF EXISTS
  refresh_tokens, user_statistics, streaks, minigame_attempts, quiz_attempts,
  lesson_completions, module_progress, user_badges, badges, minigame_signs,
  minigames, quizzes, signs, lessons, modules, media_files,
  content_versions, users
CASCADE;

DROP FUNCTION IF EXISTS refresh_user_statistics(BIGINT) CASCADE;
DROP FUNCTION IF EXISTS trg_refresh_stats() CASCADE;
DROP FUNCTION IF EXISTS rebuild_user_statistics() CASCADE;
DROP FUNCTION IF EXISTS set_updated_at() CASCADE;
DROP FUNCTION IF EXISTS current_user_id() CASCADE;

-- ============ USERS (profile table linked to Supabase Auth) ============
CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE CHECK (email = lower(email)),
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(100),
  notifications_enabled BOOLEAN NOT NULL DEFAULT true,
  dark_mode BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
  token_hash BYTEA NOT NULL UNIQUE,   -- SHA-256 of the token; never store the raw token
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);

-- ============ VERSION CONTROL ============
CREATE TABLE IF NOT EXISTS content_versions (
  content_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version_number INTEGER NOT NULL UNIQUE,
  released_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  changelog TEXT,
  is_published BOOLEAN NOT NULL DEFAULT false,
  is_deleted BOOLEAN NOT NULL DEFAULT false
);

-- ============ MEDIA FILES ============
CREATE TABLE IF NOT EXISTS media_files (
  media_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  file_name VARCHAR(255),
  object_key VARCHAR(255) NOT NULL UNIQUE,
  media_type TEXT NOT NULL CHECK (media_type IN ('Image', 'Video')),
  width INT,
  height INT,
  duration_seconds INT,
  file_size BIGINT,
  checksum BYTEA,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS idx_media_files_version ON media_files (content_version);

-- ============ MODULES ============
CREATE TABLE IF NOT EXISTS modules (
  module_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  module_code VARCHAR(100) NOT NULL UNIQUE,
  title VARCHAR(100) NOT NULL,
  description TEXT,
  module_order INT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_modules_content_version ON modules (content_version);

-- ============ LESSONS ============
CREATE TABLE IF NOT EXISTS lessons (
  lesson_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  lesson_code VARCHAR(100) NOT NULL UNIQUE,
  title VARCHAR(100) NOT NULL,
  description TEXT,
  parent_module BIGINT NOT NULL REFERENCES modules (module_id) ON DELETE RESTRICT,
  lesson_order INT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_lessons_content_version ON lessons (content_version);
CREATE INDEX IF NOT EXISTS idx_lessons_parent_module ON lessons (parent_module);

-- ============ SIGNS ============
CREATE TABLE IF NOT EXISTS signs (
  sign_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sign_code VARCHAR(100) NOT NULL UNIQUE,
  lesson_id BIGINT NOT NULL REFERENCES lessons (lesson_id) ON DELETE RESTRICT,
  media_id BIGINT NOT NULL UNIQUE REFERENCES media_files (media_id) ON DELETE RESTRICT,
  label VARCHAR(100) NOT NULL,
  recognition_label VARCHAR(100) NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_signs_lesson ON signs (lesson_id);
CREATE INDEX IF NOT EXISTS idx_signs_content_version ON signs (content_version);

-- ============ QUIZZES ============
CREATE TABLE IF NOT EXISTS quizzes (
  quiz_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  module_id BIGINT NOT NULL REFERENCES modules (module_id) ON DELETE RESTRICT,
  title VARCHAR(100),
  passing_score INT DEFAULT 70,
  time_limit_seconds INT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_quizzes_version ON quizzes (content_version);
CREATE INDEX IF NOT EXISTS idx_quizzes_module ON quizzes (module_id);

-- ============ MINIGAMES ============
CREATE TABLE IF NOT EXISTS minigames (
  minigame_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  minigame_code VARCHAR(100) NOT NULL UNIQUE,
  game_name VARCHAR(100),
  game_type VARCHAR(50),
  module_id BIGINT NOT NULL REFERENCES modules (module_id) ON DELETE RESTRICT,
  description TEXT,
  config JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now(),
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  content_version BIGINT NOT NULL
    REFERENCES content_versions (content_version_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_minigames_version ON minigames (content_version);
CREATE INDEX IF NOT EXISTS idx_minigames_module ON minigames (module_id);

-- ============ MINIGAME SIGNS ============
CREATE TABLE IF NOT EXISTS minigame_signs (
  minigame_id BIGINT NOT NULL REFERENCES minigames (minigame_id) ON DELETE CASCADE,
  sign_id BIGINT NOT NULL REFERENCES signs (sign_id) ON DELETE RESTRICT,
  PRIMARY KEY (minigame_id, sign_id)
);

-- ============ BADGES ============
CREATE TABLE IF NOT EXISTS badges (
  badge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  badge_name VARCHAR(100) NOT NULL,
  description TEXT,
  is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS user_badges (
  user_id BIGINT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
  badge_id BIGINT NOT NULL REFERENCES badges (badge_id) ON DELETE RESTRICT,
  unlocked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, badge_id)
);

-- ============ PROGRESS ============
CREATE TABLE lesson_progress (
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    completion_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'Not Started'
        CHECK (
            status IN (
                'Not Started',
                'In Progress',
                'Completed'
            )
        ),
    last_accessed TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, lesson_id),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id) ON DELETE RESTRICT
);

CREATE OR REPLACE VIEW v_module_progress_live AS
SELECT
    u.user_id,
    m.module_id,

    COUNT(l.lesson_id) AS total_lessons,

    COALESCE(
        SUM(
            CASE
                WHEN lp.status = 'Completed' THEN 1
                ELSE 0
            END
        ),
        0
    ) AS completed_lessons,

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
        WHEN COUNT(l.lesson_id) = 0
            THEN 'Not Started'

        WHEN COALESCE(
            SUM(
                CASE
                    WHEN lp.status = 'Completed' THEN 1
                    ELSE 0
                END
            ),
            0
        ) = COUNT(l.lesson_id)
            THEN 'Completed'

        WHEN COALESCE(
            SUM(
                CASE
                    WHEN COALESCE(lp.completion_percentage, 0) > 0
                      OR lp.status IN ('In Progress', 'Completed')
                    THEN 1
                    ELSE 0
                END
            ),
            0
        ) > 0
            THEN 'In Progress'

        ELSE 'Not Started'
    END AS status,

    MAX(lp.last_accessed) AS last_accessed,

    CASE
        WHEN COUNT(l.lesson_id) > 0
         AND COALESCE(
             SUM(
                 CASE WHEN lp.status = 'Completed' THEN 1 ELSE 0 END
             ),
             0
         ) = COUNT(l.lesson_id)
        THEN MAX(lp.completed_at)
        ELSE NULL
    END AS completed_at

FROM users u
CROSS JOIN modules m

LEFT JOIN lessons l
    ON l.parent_module = m.module_id
   AND l.is_active = TRUE
   AND l.is_deleted = FALSE

LEFT JOIN lesson_progress lp
    ON lp.user_id = u.user_id
   AND lp.lesson_id = l.lesson_id

WHERE m.is_active = TRUE
  AND m.is_deleted = FALSE

GROUP BY u.user_id, m.module_id;

-- ============ ATTEMPTS ============
CREATE TABLE IF NOT EXISTS quiz_attempts (
  attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
  quiz_id BIGINT NOT NULL REFERENCES quizzes (quiz_id) ON DELETE RESTRICT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  score INT,
  max_score INT,
  percentage NUMERIC(5, 2),
  passed BOOLEAN
);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts ON quiz_attempts (user_id, quiz_id);

CREATE TABLE IF NOT EXISTS minigame_attempts (
  game_attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
  minigame_id BIGINT NOT NULL REFERENCES minigames (minigame_id) ON DELETE RESTRICT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  score INT,
  duration_seconds INT,
  accuracy NUMERIC(5, 2)
);
CREATE INDEX IF NOT EXISTS idx_minigame_attempts ON minigame_attempts (user_id, minigame_id);

-- ============ STREAKS ============
CREATE TABLE IF NOT EXISTS streaks (
  streak_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users (user_id) ON DELETE CASCADE,
  current_streak INT,
  longest_streak INT,
  last_activity_date DATE
);

-- ============ USER STATISTICS (cached aggregate) ============
CREATE TABLE IF NOT EXISTS user_statistics (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    lessons_completed INTEGER NOT NULL DEFAULT 0,
    quizzes_completed INTEGER NOT NULL DEFAULT 0,
    minigames_completed INTEGER NOT NULL DEFAULT 0,
    total_quiz_score BIGINT NOT NULL DEFAULT 0,
    total_minigame_score BIGINT NOT NULL DEFAULT 0,
    average_accuracy NUMERIC(5, 2),
    total_time_spent_seconds BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE VIEW v_user_statistics_live
WITH (security_invoker = true) AS
SELECT
  u.user_id,
  (SELECT COUNT(*) FROM lesson_completions lc WHERE lc.user_id = u.user_id)::INT AS lessons_completed,
  (SELECT COUNT(*) FROM quiz_attempts qa
     WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL)::INT AS quizzes_completed,
  (SELECT COUNT(*) FROM minigame_attempts ma
     WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL)::INT AS minigames_completed,
  (SELECT COALESCE(SUM(qa.score), 0) FROM quiz_attempts qa
     WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL)::INT AS total_quiz_score,
  (SELECT COALESCE(SUM(ma.score), 0) FROM minigame_attempts ma
     WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL)::INT AS total_minigame_score,
  (SELECT AVG(t.v) FROM (
      SELECT user_id, percentage AS v FROM quiz_attempts WHERE completed_at IS NOT NULL
      UNION ALL
      SELECT user_id, accuracy AS v FROM minigame_attempts WHERE completed_at IS NOT NULL
   ) t WHERE t.user_id = u.user_id)::NUMERIC(5, 2) AS average_accuracy,
  (
    (SELECT COALESCE(SUM(lc.time_spent_seconds), 0) FROM lesson_completions lc
       WHERE lc.user_id = u.user_id)
  + (SELECT COALESCE(SUM(EXTRACT(EPOCH FROM (qa.completed_at - qa.started_at))), 0)
       FROM quiz_attempts qa
       WHERE qa.user_id = u.user_id
         AND qa.completed_at IS NOT NULL AND qa.started_at IS NOT NULL)
  + (SELECT COALESCE(SUM(ma.duration_seconds), 0) FROM minigame_attempts ma
       WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL)
  )::INT AS total_time_spent_seconds
FROM users u;

-- ============ STATS REFRESH FUNCTION + TRIGGERS ============
CREATE OR REPLACE FUNCTION refresh_user_statistics(p_user_id BIGINT)
RETURNS void LANGUAGE sql AS $$
  INSERT INTO user_statistics (
    user_id, lessons_completed, quizzes_completed, minigames_completed,
    total_quiz_score, total_minigame_score, average_accuracy,
    total_time_spent_seconds, updated_at)
  SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
         total_quiz_score, total_minigame_score, average_accuracy,
         total_time_spent_seconds, now()
  FROM v_user_statistics_live
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
$$;

CREATE OR REPLACE FUNCTION trg_refresh_stats()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    PERFORM refresh_user_statistics(OLD.user_id);
  ELSE
    PERFORM refresh_user_statistics(NEW.user_id);
  END IF;
  RETURN NULL;
END;
$$;

-- Rebuild everything if the cache ever drifts
CREATE OR REPLACE FUNCTION rebuild_user_statistics()
RETURNS void LANGUAGE sql AS $$
  SELECT refresh_user_statistics(user_id) FROM users;
$$;

-- ============ updated_at AUTO-TOUCH ============
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
-- repeat for modules, lessons, signs, quizzes, minigames, media_files if you want

-- ============ ROW LEVEL SECURITY ============
-- Future tables: don't auto-grant to the public API roles
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;

-- RLS on every table, with no policies = deny all for anon/authenticated
DO $$
DECLARE t record;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
END $$;

-- Existing objects
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM anon, authenticated, PUBLIC;