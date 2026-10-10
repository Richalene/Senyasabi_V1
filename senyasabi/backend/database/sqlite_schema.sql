-- ============================================
-- USERS (SQLite cache - only local fields)
-- ============================================
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Autoincrement for offline, server-assigned when synced
    username TEXT NOT NULL COLLATE NOCASE,
    display_name TEXT,
    updated_at TEXT
);

-- ============================================
-- OFFLINE AUTH (SQLite only)
-- ============================================
CREATE TABLE IF NOT EXISTS offline_auth (
	user_id INTEGER PRIMARY KEY,                 -- References users.user_id
	username TEXT NOT NULL UNIQUE COLLATE NOCASE,
	password_verifier TEXT NOT NULL,             -- full argon2id string (salt + params embedded)
	created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	last_online_login TEXT NOT NULL,
	failed_attempts INTEGER NOT NULL DEFAULT 0,  -- local throttling
	locked_until TEXT,                           -- backoff lockout
	FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- ============================================
-- VERSION CONTROL
-- ============================================
CREATE TABLE IF NOT EXISTS content_versions (
	content_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
	version_number INTEGER NOT NULL UNIQUE,
	released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	changelog TEXT,
	is_published BOOLEAN DEFAULT 0,
    is_deleted BOOLEAN DEFAULT 0 NOT NULL
);

-- ============================================
-- MEDIA FILES (POSTGRE)
-- ============================================
CREATE TABLE media_files (
    media_id INTEGER PRIMARY KEY,
    file_name TEXT NOT NULL,
    object_key TEXT NOT NULL,
    media_type TEXT NOT NULL
        CHECK (media_type IN ('Image', 'Video')),
    file_size INTEGER,
    checksum TEXT,
    content_version INTEGER NOT NULL,
    updated_at TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (content_version)
        REFERENCES content_versions(content_version_id)
);

CREATE INDEX IF NOT EXISTS idx_media_files_version
	ON media_files (content_version);

-- ============================================
-- MEDIA CACHE (SQLITE)
-- ============================================
CREATE TABLE IF NOT EXISTS media_cache (
	media_id INTEGER PRIMARY KEY,
	local_path VARCHAR(500),
	content_version INT NOT NULL,
	cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	checksum TEXT,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
	FOREIGN KEY (media_id) REFERENCES media_files(media_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_media_cache_version
   	ON media_cache (content_version);

-- ============================================
-- MODULES
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
	module_id INTEGER PRIMARY KEY,  -- server-assigned ID
 	module_code TEXT NOT NULL UNIQUE,
	title TEXT NOT NULL,
	description TEXT,
	module_order INTEGER NOT NULL,
	is_active INTEGER DEFAULT 1,
	updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
	is_deleted INTEGER DEFAULT 0 NOT NULL,
	content_version INTEGER NOT NULL,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_modules_content_version
	ON modules (content_version);

-- ============================================
-- LESSONS
-- ============================================
CREATE TABLE IF NOT EXISTS lessons (
	lesson_id INTEGER PRIMARY KEY,  -- server-assigned ID
	lesson_code TEXT NOT NULL UNIQUE,
	title TEXT NOT NULL,
	description TEXT,
	parent_module INTEGER NOT NULL,
	lesson_order INTEGER NOT NULL,
	is_active INTEGER DEFAULT 1,
	updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
	is_deleted INTEGER DEFAULT 0 NOT NULL,
	content_version INTEGER NOT NULL,
	FOREIGN KEY (parent_module) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_lessons_content_version
	ON lessons (content_version);
CREATE INDEX IF NOT EXISTS idx_lessons_parent_module
	ON lessons (parent_module);

-- ============================================
-- SIGNS
-- ============================================
CREATE TABLE IF NOT EXISTS signs (
	sign_id INTEGER PRIMARY KEY,  -- server-assigned ID
	sign_code TEXT NOT NULL UNIQUE,
	lesson_id INTEGER NOT NULL,
	media_id INTEGER UNIQUE NOT NULL,
	label TEXT NOT NULL,
	recognition_label TEXT NOT NULL,
	updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
	is_deleted INTEGER DEFAULT 0 NOT NULL,
	content_version INTEGER NOT NULL,
	FOREIGN KEY (lesson_id) REFERENCES lessons (lesson_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (media_id) REFERENCES media_files (media_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_signs_lesson ON signs (lesson_id);
CREATE INDEX IF NOT EXISTS idx_signs_content_version
	ON signs (content_version);

-- ============================================
-- QUIZZES
-- ============================================
CREATE TABLE IF NOT EXISTS quizzes (
	quiz_id INTEGER PRIMARY KEY,  -- server-assigned ID
	module_id INTEGER NOT NULL,
	title TEXT,
	passing_score INTEGER DEFAULT 70,
	time_limit_seconds INTEGER,
	updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
	is_deleted INTEGER DEFAULT 0 NOT NULL,
	content_version INTEGER NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_quizzes_version
	ON quizzes (content_version);
CREATE INDEX IF NOT EXISTS idx_quizzes_module
	ON quizzes (module_id);

-- ============================================
-- MINIGAMES
-- ============================================
CREATE TABLE IF NOT EXISTS minigames (
	minigame_id INTEGER PRIMARY KEY,  -- server-assigned ID
	minigame_code TEXT NOT NULL UNIQUE,
	game_name TEXT,
	game_type TEXT,
	module_id INTEGER NOT NULL,
	description TEXT,
	config TEXT NOT NULL,  -- JSON stored as TEXT
	updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
	is_deleted INTEGER DEFAULT 0 NOT NULL,
	content_version INTEGER NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(content_version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_minigames_version
	ON minigames (content_version);
CREATE INDEX IF NOT EXISTS idx_minigames_module
	ON minigames (module_id);

-- ============================================
-- MINIGAME SIGNS
-- ============================================
CREATE TABLE IF NOT EXISTS minigame_signs (
	minigame_id INTEGER NOT NULL,
	sign_id INTEGER NOT NULL,
	PRIMARY KEY (minigame_id, sign_id),
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id)
		ON DELETE CASCADE,
	FOREIGN KEY (sign_id) REFERENCES signs (sign_id)
		ON DELETE RESTRICT
);

-- ============================================
-- BADGES
-- ============================================

CREATE TABLE IF NOT EXISTS badges (
    badge_id INTEGER PRIMARY KEY,  -- server-assigned ID
    badge_name TEXT NOT NULL,
    description TEXT,
	is_deleted INTEGER DEFAULT 0 NOT NULL
);

-- ============================================
-- USER BADGES
-- ============================================

CREATE TABLE user_badges (
    user_id INTEGER NOT NULL,
    badge_id INTEGER NOT NULL,
    unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, badge_id),

    FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges (badge_id)
		ON DELETE RESTRICT
);

-- ============================================
-- LESSON PROGRESS
-- ============================================
CREATE TABLE lesson_progress (
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    completion_percentage REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Not Started'
        CHECK (
            status IN (
                'Not Started',
                'In Progress',
                'Completed'
            )
        ),
    last_accessed TEXT,
    completed_at TEXT,
    time_spent_seconds INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, lesson_id),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (lesson_id)
        REFERENCES lessons(lesson_id) ON DELETE RESTRICT
);

-- ============================================
-- MODULE PROGRESS
-- ============================================
DROP VIEW IF EXISTS v_module_progress_live;

CREATE VIEW v_module_progress_live AS
SELECT
    u.user_id,
    m.module_id,
    COUNT(l.lesson_id) AS total_lessons,
    SUM(
        CASE
            WHEN lp.status = 'Completed' THEN 1
            ELSE 0
        END
    ) AS completed_lessons,
    COALESCE(
        ROUND(
            SUM(
                CASE
                    WHEN lp.status = 'Completed' THEN 100.0
                    ELSE COALESCE(lp.completion_percentage, 0)
                END
            ) / NULLIF(COUNT(l.lesson_id), 0),
            2
        ),
        0
    ) AS completion_percentage,

    CASE
        WHEN COUNT(l.lesson_id) = 0
            THEN 'Not Started'
        WHEN SUM(
            CASE
                WHEN lp.status = 'Completed' THEN 1
                ELSE 0
            END
        ) = COUNT(l.lesson_id)
            THEN 'Completed'
        WHEN SUM(
            CASE
                WHEN COALESCE(lp.completion_percentage, 0) > 0
                  OR lp.status IN ('In Progress', 'Completed')
                THEN 1
                ELSE 0
            END
        ) > 0
            THEN 'In Progress'
        ELSE 'Not Started'
    END AS status,

    MAX(lp.last_accessed) AS last_accessed,

    CASE
        WHEN COUNT(l.lesson_id) > 0
         AND SUM(
             CASE WHEN lp.status = 'Completed' THEN 1 ELSE 0 END
         ) = COUNT(l.lesson_id)
        THEN MAX(lp.completed_at)
        ELSE NULL
    END AS completed_at
FROM users u
CROSS JOIN modules m
LEFT JOIN lessons l
    ON l.parent_module = m.module_id
    AND l.is_active = 1
    AND l.is_deleted = 0
LEFT JOIN lesson_progress lp
    ON lp.user_id = u.user_id
    AND lp.lesson_id = l.lesson_id
WHERE m.is_active = 1
  AND m.is_deleted = 0
GROUP BY u.user_id, m.module_id;

-- ============================================
-- USER STATISTICS (CACHED AGG)
-- ============================================

CREATE TABLE IF NOT EXISTS user_statistics (
	user_id INTEGER PRIMARY KEY,
	lessons_completed INTEGER NOT NULL DEFAULT 0,
	quizzes_completed INTEGER NOT NULL DEFAULT 0,
	minigames_completed INTEGER NOT NULL DEFAULT 0,
	total_quiz_score INTEGER NOT NULL DEFAULT 0,
	total_minigame_score INTEGER NOT NULL DEFAULT 0,
	average_accuracy REAL,
	total_time_spent_seconds INTEGER NOT NULL DEFAULT 0,
	updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE VIEW v_user_statistics_live AS
WITH lesson_stats AS (
    SELECT
        user_id,

        SUM(
            CASE WHEN status = 'Completed' THEN 1 ELSE 0 END
        ) AS lessons_completed,

        COALESCE(SUM(time_spent_seconds), 0) AS lesson_time

    FROM lesson_progress
    GROUP BY user_id
),
quiz_stats AS (
    SELECT
        user_id,

        SUM(
            CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END
        ) AS quizzes_completed,

        COALESCE(
            SUM(
                CASE WHEN completed_at IS NOT NULL
                     THEN COALESCE(score, 0)
                     ELSE 0
                END
            ),
            0
        ) AS total_quiz_score,
        COALESCE(
            SUM(
                CASE
                    WHEN completed_at IS NOT NULL
                     AND started_at IS NOT NULL
                    THEN COALESCE(
                        strftime('%s', completed_at)
                        - strftime('%s', started_at),
                        0
                    )
                    ELSE 0
                END
            ),
            0
        ) AS quiz_time
    FROM quiz_attempts
    GROUP BY user_id
),
minigame_stats AS (
    SELECT
        user_id,
        SUM(
            CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END
        ) AS minigames_completed,
        COALESCE(
            SUM(
                CASE WHEN completed_at IS NOT NULL
                     THEN COALESCE(score, 0)
                     ELSE 0
                END
            ),
            0
        ) AS total_minigame_score,
        COALESCE(
            SUM(
                CASE WHEN completed_at IS NOT NULL
                     THEN COALESCE(duration_seconds, 0)
                     ELSE 0
                END
            ),
            0
        ) AS minigame_time
    FROM minigame_attempts
    GROUP BY user_id
),
accuracy_rows AS (
    SELECT user_id, percentage AS accuracy
    FROM quiz_attempts
    WHERE completed_at IS NOT NULL
      AND percentage IS NOT NULL
    UNION ALL
    SELECT user_id, accuracy
    FROM minigame_attempts
    WHERE completed_at IS NOT NULL
      AND accuracy IS NOT NULL
),
accuracy_stats AS (
    SELECT
        user_id,
        AVG(accuracy) AS average_accuracy
    FROM accuracy_rows
    GROUP BY user_id
)
SELECT
    u.user_id,
    COALESCE(ls.lessons_completed, 0)
        AS lessons_completed,
    COALESCE(qs.quizzes_completed, 0)
        AS quizzes_completed,
    COALESCE(ms.minigames_completed, 0)
        AS minigames_completed,
    COALESCE(qs.total_quiz_score, 0)
        AS total_quiz_score,
    COALESCE(ms.total_minigame_score, 0)
        AS total_minigame_score,
    ast.average_accuracy,
    COALESCE(ls.lesson_time, 0)
      + COALESCE(qs.quiz_time, 0)
      + COALESCE(ms.minigame_time, 0)
        AS total_time_spent_seconds
FROM users u
LEFT JOIN lesson_stats ls
    ON ls.user_id = u.user_id
LEFT JOIN quiz_stats qs
    ON qs.user_id = u.user_id
LEFT JOIN minigame_stats ms
    ON ms.user_id = u.user_id
LEFT JOIN accuracy_stats ast
    ON ast.user_id = u.user_id;

-- ============================================
-- STREAKS (CACHED AGG)
-- ============================================

CREATE TABLE IF NOT EXISTS streaks (
	streak_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER NOT NULL UNIQUE,
	current_streak INTEGER,
	longest_streak INTEGER,
	last_activity_date TEXT,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE
);

-- ============================================
-- LEADERBOARD CACHE (SQLITE ONLY)
-- ============================================
CREATE TABLE leaderboard_cache (
    board_code TEXT NOT NULL DEFAULT 'all_time',
    user_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    total_score INTEGER NOT NULL DEFAULT 0,
    rank_position INTEGER NOT NULL,
    current_streak INTEGER NOT NULL DEFAULT 0,
    badge_count INTEGER NOT NULL DEFAULT 0,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (board_code, user_id)
);

CREATE INDEX IF NOT EXISTS idx_leaderboard_cache_rank
    ON leaderboard_cache (board_code, rank_position);

-- ============================================
-- QUIZ ATTEMPTS
-- ============================================
CREATE TABLE IF NOT EXISTS quiz_attempts (
	attempt_id TEXT PRIMARY KEY, -- UUID stored as TEXT
	user_id INTEGER NOT NULL,
	quiz_id INTEGER NOT NULL,
	started_at TEXT,
	completed_at TEXT,
	score INTEGER,
	max_score INTEGER,
	percentage REAL,
	passed INTEGER,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
	FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id
	ON quiz_attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id
	ON quiz_attempts (quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_quiz
	ON quiz_attempts (user_id, quiz_id);

-- ============================================
-- MINIGAME ATTEMPTS
-- ============================================
CREATE TABLE IF NOT EXISTS minigame_attempts (
	game_attempt_id TEXT PRIMARY KEY, -- UUID stored as TEXT
	user_id INTEGER NOT NULL,
	minigame_id INTEGER NOT NULL,
	started_at TEXT,
	completed_at TEXT,
	score INTEGER,
	duration_seconds INTEGER,
	accuracy REAL,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_minigame_attempts_user_id
	ON minigame_attempts (user_id);
CREATE INDEX IF NOT EXISTS idx_minigame_attempts_minigame_id
	ON minigame_attempts (minigame_id);
CREATE INDEX IF NOT EXISTS idx_minigame_attempts_user_minigame
	ON minigame_attempts (user_id, minigame_id);

-- ============================================
-- SYNC QUEUE
-- ============================================
-- Only completed attempts get queued and the operation is always an upsert.
CREATE TABLE IF NOT EXISTS sync_queue (
	sync_id TEXT PRIMARY KEY,
	user_id INTEGER NOT NULL,
	entity_type TEXT NOT NULL
		CHECK (entity_type IN ('quiz_attempt', 'minigame_attempt', 'lesson_completion')),
	entity_id TEXT NOT NULL,  -- server-assigned UUID
	operation TEXT NOT NULL DEFAULT 'upsert' CHECK (operation IN ('upsert', 'delete')),
	payload TEXT NOT NULL,  -- JSON with full entity data including server IDs
	created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
	retry_count INTEGER NOT NULL DEFAULT 0,
	last_attempted_at TEXT,
	last_error TEXT,
	synced_at TEXT
);

-- At most one pending item per entity; re-queueing replaces the payload
CREATE UNIQUE INDEX IF NOT EXISTS uq_sync_pending
  ON sync_queue (entity_type, entity_id) WHERE synced_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_sync_pending
  ON sync_queue (created_at) WHERE synced_at IS NULL;
