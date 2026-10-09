-- ============================================
-- USERS (POSTGRE)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
	user_id INTEGER PRIMARY KEY AUTOINCREMENT,
	username VARCHAR(50) NOT NULL UNIQUE,
	email VARCHAR(255) NOT NULL UNIQUE,
	password_hash VARCHAR(255) NOT NULL,
	display_name VARCHAR(100),
	notifications_enabled BOOLEAN DEFAULT 1 NOT NULL,
	dark_mode BOOLEAN DEFAULT 0 NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

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
CREATE TABLE IF NOT EXISTS media_files (
	media_id INTEGER PRIMARY KEY AUTOINCREMENT,
	file_name VARCHAR(255),
	object_key VARCHAR(255),
	media_type TEXT NOT NULL,
	width INT,
	height INT,
	duration_seconds INT,
	file_size BIGINT,
	checksum BLOB,
	content_version INT NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	CHECK (media_type IN ('Image', 'Video')),
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_media_files_version
	ON media_files (content_version);

-- ============================================
-- MEDIA CACHE (SQLITE)
-- ============================================
CREATE TABLE IF NOT EXISTS media_cache (
	media_id INTEGER PRIMARY KEY AUTOINCREMENT,
	local_path VARCHAR(500),
	content_version INT NOT NULL,
	cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	checksum BLOB,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_media_cache_version 
   	ON media_cache (content_version);

-- ============================================
-- MODULES
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
	module_id INTEGER PRIMARY KEY AUTOINCREMENT,
 	module_code VARCHAR(100) NOT NULL UNIQUE,
	title VARCHAR(100) NOT NULL,
	description TEXT,
	module_order INT NOT NULL,
	is_active BOOLEAN DEFAULT 1,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	content_version INT NOT NULL,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_modules_content_version
	ON modules (content_version);

-- ============================================
-- LESSONS
-- ============================================
CREATE TABLE IF NOT EXISTS lessons (
	lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
	lesson_code VARCHAR(100) NOT NULL UNIQUE,
	title VARCHAR(100) NOT NULL,
	description TEXT,
	parent_module INT NOT NULL,
	lesson_order INT NOT NULL,
	is_active BOOLEAN DEFAULT 1,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	content_version INT NOT NULL,
	FOREIGN KEY (parent_module) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
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
	sign_id INTEGER PRIMARY KEY AUTOINCREMENT,
	sign_code VARCHAR(100) NOT NULL UNIQUE,
	lesson_id INT NOT NULL,
	media_id INT UNIQUE NOT NULL,
	label VARCHAR(100) NOT NULL,
	recognition_label VARCHAR(100) NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	content_version INT NOT NULL,
	FOREIGN KEY (lesson_id) REFERENCES lessons (lesson_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (media_id) REFERENCES media_files (media_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_signs_lesson ON signs (lesson_id);
CREATE INDEX IF NOT EXISTS idx_signs_content_version
	ON signs (content_version);

-- ============================================
-- QUIZZES
-- ============================================
CREATE TABLE IF NOT EXISTS quizzes (
	quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
	module_id INT NOT NULL,
	title VARCHAR(100),
	passing_score INT DEFAULT 70,
	time_limit_seconds INT,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	content_version INT NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
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
	minigame_id INTEGER PRIMARY KEY AUTOINCREMENT,
	minigame_code VARCHAR(100) NOT NULL UNIQUE,
	game_name VARCHAR(100),
	game_type VARCHAR(50),
	module_id INT NOT NULL,
	description TEXT,
	config JSONB NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL,
	content_version INT NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (content_version) REFERENCES content_versions (version_id)
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
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id)
		ON DELETE CASCADE,
	FOREIGN KEY (sign_id) REFERENCES signs (sign_id)
		ON DELETE RESTRICT
);

-- ============================================
-- BADGES
-- ============================================

CREATE TABLE IF NOT EXISTS badges (
    badge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_name VARCHAR(100) NOT NULL,
    description TEXT,
	is_deleted BOOLEAN DEFAULT 0 NOT NULL
);

-- ============================================
-- USER BADGES
-- ============================================

CREATE TABLE user_badges (
    user_id INTEGER NOT NULL,
    badge_id INTEGER NOT NULL,
    unlocked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, badge_id),

    FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges (badge_id)
		ON DELETE RESTRICT
);

-- ============================================
-- MODULE PROGRESS
-- ============================================
CREATE TABLE IF NOT EXISTS module_progress (
	progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INT NOT NULL,
	module_id INT NOT NULL,
	completion_percentage DECIMAL(5, 2),
	status TEXT DEFAULT 'Not Started',
	last_accessed DATETIME,
	completed_at DATETIME,
	FOREIGN KEY (module_id) REFERENCES modules (module_id)
		ON DELETE RESTRICT,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,

	CHECK (status IN ('Not Started', 'In Progress', 'Completed'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_module_progress
	ON module_progress (user_id, module_id);

-- ============================================
-- LESSON PROGRESS
-- ============================================
CREATE TABLE IF NOT EXISTS lesson_completion (
	user_id INT NOT NULL,
	lesson_id INT NOT NULL,
	completed_at DATETIME,
	time_spent_seconds INTEGER NOT NULL DEFAULT 0,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (user_id, lesson_id),

	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
	FOREIGN KEY (lesson_id) REFERENCES lessons (lesson_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_lesson_completions_lesson
	ON lesson_completions (lesson_id);

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
	average_accuracy DECIMAL(5, 2),
	total_time_spent_seconds INTEGER NOT NULL DEFAULT 0,
	updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS v_user_statistics_live AS
SELECT
	u.user_id,

	(SELECT COUNT(*) FROM lesson_completions lc
	  WHERE lc.user_id = u.user_id) AS lessons_completed,

	(SELECT COUNT(*) FROM quiz_attempts qa
	  WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL) AS quizzes_completed,

	(SELECT COUNT(*) FROM minigame_attempts ma
	  WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL) AS minigames_completed,

	(SELECT COALESCE(SUM(qa.score), 0) FROM quiz_attempts qa
	  WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL) AS total_quiz_score,

	(SELECT COALESCE(SUM(ma.score), 0) FROM minigame_attempts ma
	  WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL) AS total_minigame_score,

	-- mean of quiz percentages and minigame accuracies together; NULLs are ignored
	(SELECT AVG(v) FROM (
		SELECT user_id, percentage AS v FROM quiz_attempts
		 WHERE completed_at IS NOT NULL
		UNION ALL
		SELECT user_id, accuracy AS v FROM minigame_attempts
		 WHERE completed_at IS NOT NULL
	 ) WHERE user_id = u.user_id) AS average_accuracy,

	  (SELECT COALESCE(SUM(lc.time_spent_seconds), 0) FROM lesson_completions lc
	    WHERE lc.user_id = u.user_id)
	+ (SELECT COALESCE(SUM(strftime('%s', qa.completed_at) - strftime('%s', qa.started_at)), 0)
	     FROM quiz_attempts qa
	    WHERE qa.user_id = u.user_id
	      AND qa.completed_at IS NOT NULL AND qa.started_at IS NOT NULL)
	+ (SELECT COALESCE(SUM(ma.duration_seconds), 0) FROM minigame_attempts ma
	    WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL)
	  AS total_time_spent_seconds
FROM users u;

-- ============================================
-- STREAKS (CACHED AGG)
-- ============================================

CREATE TABLE IF NOT EXISTS streaks (
	streak_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INT NOT NULL UNIQUE,
	current_streak INT,
	longest_streak INT,
	last_activity_date DATE,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE
);

-- ============================================
-- LEADERBOARD CACHE (SQLITE ONLY)
-- ============================================
CREATE TABLE IF NOT EXISTS leaderboard (
	user_id INT NOT NULL PRIMARY KEY,
	rank_position INT,
	last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE
);

-- ============================================
-- QUIZ ATTEMPTS
-- ============================================
CREATE TABLE IF NOT EXISTS quiz_attempts (
	attempt_id UUID PRIMARY KEY, -- Use UUID in SQLAlchemy
	user_id INT NOT NULL,
	quiz_id INT NOT NULL,
	started_at DATETIME,
	completed_at DATETIME,
	score INT,
	max_score INT,
	percentage DECIMAL(5, 2),
	passed BOOLEAN,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
	FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts
	ON quiz_attempts (user_id, quiz_id);

-- ============================================
-- MINIGAME ATTEMPTS
-- ============================================
CREATE TABLE IF NOT EXISTS minigame_attempts (
	game_attempt_id UUID PRIMARY KEY, -- Use UUID in SQLAlchemy
	user_id INT NOT NULL,
	minigame_id INT NOT NULL,
	started_at DATETIME,
	completed_at DATETIME,
	score INT,
	duration_seconds INT,
	accuracy DECIMAL(5, 2),
	FOREIGN KEY (user_id) REFERENCES users (user_id)
		ON DELETE CASCADE,
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id)
		ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_minigame_attempts
	ON minigame_attempts (user_id, minigame_id);

-- ============================================
-- SYNC QUEUE
-- ============================================
CREATE TABLE sync_queue (
    sync_id UUID PRIMARY KEY, -- Use UUID in SQLAlchemy
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL,
    payload TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_attempted_at TIMESTAMP,
    synced_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_queue
	ON sync_queue (synced_at);

-- ============================================
-- TRIGGERS
-- ============================================

-- OWNER: triggers on lesson_completions / quiz_attempts / minigame_attempts.
-- DO NOT write to this table from application code. Rebuildable via rebuild_user_statistics().
CREATE TRIGGER IF NOT EXISTS trg_stats_lesson_completed
AFTER INSERT ON lesson_completions
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = NEW.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_lesson_uncompleted
AFTER DELETE ON lesson_completions
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = OLD.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_quiz_insert
AFTER INSERT ON quiz_attempts
WHEN NEW.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = NEW.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

-- Attempts are usually inserted at start (completed_at NULL) and updated on finish
CREATE TRIGGER IF NOT EXISTS trg_stats_quiz_update
AFTER UPDATE OF completed_at, started_at, score, percentage ON quiz_attempts
WHEN NEW.completed_at IS NOT NULL OR OLD.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = NEW.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_quiz_delete
AFTER DELETE ON quiz_attempts
WHEN OLD.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = OLD.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_minigame_insert
AFTER INSERT ON minigame_attempts
WHEN NEW.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = NEW.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_minigame_update
AFTER UPDATE OF completed_at, score, accuracy, duration_seconds ON minigame_attempts
WHEN NEW.completed_at IS NOT NULL OR OLD.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = NEW.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

CREATE TRIGGER IF NOT EXISTS trg_stats_minigame_delete
AFTER DELETE ON minigame_attempts
WHEN OLD.completed_at IS NOT NULL
BEGIN
	INSERT INTO user_statistics (
		user_id, lessons_completed, quizzes_completed, minigames_completed,
		total_quiz_score, total_minigame_score, average_accuracy,
		total_time_spent_seconds, updated_at)
	SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
	       total_quiz_score, total_minigame_score, average_accuracy,
	       total_time_spent_seconds, CURRENT_TIMESTAMP
	FROM v_user_statistics_live
	WHERE user_id = OLD.user_id
	ON CONFLICT (user_id) DO UPDATE SET
		lessons_completed = excluded.lessons_completed,
		quizzes_completed = excluded.quizzes_completed,
		minigames_completed = excluded.minigames_completed,
		total_quiz_score = excluded.total_quiz_score,
		total_minigame_score = excluded.total_minigame_score,
		average_accuracy = excluded.average_accuracy,
		total_time_spent_seconds = excluded.total_time_spent_seconds,
		updated_at = CURRENT_TIMESTAMP;
END;

-- INSERT INTO user_statistics (user_id, lessons_completed, quizzes_completed, minigames_completed,
-- 	total_quiz_score, total_minigame_score, average_accuracy, total_time_spent_seconds, updated_at)
-- SELECT user_id, lessons_completed, quizzes_completed, minigames_completed,
-- 	total_quiz_score, total_minigame_score, average_accuracy, total_time_spent_seconds, CURRENT_TIMESTAMP
-- FROM v_user_statistics_live
-- WHERE 1  -- required by SQLite to disambiguate ON CONFLICT
-- ON CONFLICT (user_id) DO UPDATE SET
-- 	lessons_completed = excluded.lessons_completed,
-- 	quizzes_completed = excluded.quizzes_completed,
-- 	minigames_completed = excluded.minigames_completed,
-- 	total_quiz_score = excluded.total_quiz_score,
-- 	total_minigame_score = excluded.total_minigame_score,
-- 	average_accuracy = excluded.average_accuracy,
-- 	total_time_spent_seconds = excluded.total_time_spent_seconds,
-- 	updated_at = CURRENT_TIMESTAMP;