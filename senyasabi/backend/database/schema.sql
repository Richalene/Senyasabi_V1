-- ============================================
-- USERS
-- ============================================
CREATE TABLE IF NOT EXISTS users (
	user_id INTEGER PRIMARY KEY AUTOINCREMENT,
	username VARCHAR(50) NOT NULL,
	email VARCHAR(255) NOT NULL UNIQUE,
	password_hash VARCHAR(255) NOT NULL,
	display_name VARCHAR(100),
	notifications_enabled BOOLEAN DEFAULT 1 NOT NULL,
	dark_mode BOOLEAN DEFAULT 0 NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ============================================
-- VERSION CONTROL
-- ============================================
CREATE TABLE IF NOT EXISTS content_versions (
	version_id INTEGER PRIMARY KEY AUTOINCREMENT,
	version_number INTEGER NOT NULL,
	released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	changelog TEXT,
	is_published BOOLEAN DEFAULT 0,
    is_deleted BOOLEAN DEFAULT 0
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
	checksum INT,
	content_version INT NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0,
	CHECK (media_type IN ('Image', 'Video')),
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
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
	checksum INT,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_media_cache_version 
   	ON media_cache (content_version);

-- ============================================
-- MODULES
-- ============================================
CREATE TABLE IF NOT EXISTS modules (
	module_id INTEGER PRIMARY KEY AUTOINCREMENT,
 	module_code VARCHAR(100) NOT NULL,
	title VARCHAR(100) NOT NULL,
	description TEXT,
	module_order INT NOT NULL,
	is_active BOOLEAN DEFAULT 1,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0,
	content_version INT NOT NULL,
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_modules_content_version
	ON modules (content_version);

-- ============================================
-- LESSONS
-- ============================================
CREATE TABLE IF NOT EXISTS lessons (
	lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
	lesson_code VARCHAR(100) NOT NULL,
	title VARCHAR(100) NOT NULL,
	description TEXT,
	parent_module INT NOT NULL,
	lesson_order INT NOT NULL,
	is_active BOOLEAN DEFAULT 1,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0,
	content_version INT NOT NULL,
	FOREIGN KEY (parent_module) REFERENCES modules (module_id),
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_lessons_content_version
	ON lessons (content_version);

-- ============================================
-- SIGNS
-- ============================================
CREATE TABLE IF NOT EXISTS signs (
	sign_id INTEGER PRIMARY KEY AUTOINCREMENT,
	sign_code VARCHAR(100) NOT NULL,
	lesson_id INT NOT NULL,
	media_id INT UNIQUE NOT NULL,
	label VARCHAR(100) NOT NULL,
	recognition_label VARCHAR(100) NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0,
	content_version INT NOT NULL,
	FOREIGN KEY (lesson_id) REFERENCES lessons (lesson_id),
	FOREIGN KEY (media_id) REFERENCES media_files (media_id),
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
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
	is_deleted BOOLEAN DEFAULT 0,
	content_version INT NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id),
	FOREIGN KEY (content_version) REFERENCES content_versions(version_id)
);

CREATE INDEX IF NOT EXISTS idx_quizzes_version
	ON quizzes (content_version);

-- ============================================
-- MINIGAMES
-- ============================================
CREATE TABLE IF NOT EXISTS minigames (
	minigame_id INTEGER PRIMARY KEY AUTOINCREMENT,
	minigame_code VARCHAR(100) NOT NULL,
	game_name VARCHAR(100),
	game_type VARCHAR(50),
	module_id INT NOT NULL,
	description TEXT,
	config JSONB NOT NULL,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	is_deleted BOOLEAN DEFAULT 0,
	content_version INT NOT NULL,
	FOREIGN KEY (module_id) REFERENCES modules (module_id),
	FOREIGN KEY (content_version) REFERENCES content_versions (version_id)
);

CREATE INDEX IF NOT EXISTS idx_minigames_version
	ON minigames (content_version);

-- ============================================
-- MINIGAME SIGNS
-- ============================================
CREATE TABLE IF NOT EXISTS minigame_signs (
	minigame_id INTEGER NOT NULL,
	sign_id INTEGER NOT NULL,
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id),
	FOREIGN KEY (sign_id) REFERENCES signs (sign_id)
);

-- ============================================
-- BADGES
-- ============================================

CREATE TABLE IF NOT EXISTS badges (
    badge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_name VARCHAR(100) NOT NULL,
    description TEXT,
	is_deleted BOOLEAN DEFAULT 0
);

-- ============================================
-- USER BADGES
-- ============================================

CREATE TABLE user_badges (
    user_id INTEGER NOT NULL,
    badge_id INTEGER NOT NULL,
    unlocked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, badge_id),

    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (badge_id) REFERENCES badges (badge_id)
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
	FOREIGN KEY (module_id) REFERENCES modules (module_id),
	FOREIGN KEY (user_id) REFERENCES users (user_id),
	CHECK (status IN ('Not Started', 'In Progress', 'Completed'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_module_progress
	ON module_progress (user_id, module_id);

-- ============================================
-- USER STATISTICS (CACHED AGG)
-- ============================================
CREATE TABLE IF NOT EXISTS user_statistics (
	stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INT NOT NULL,
	lessons_completed INT,
	quizzes_completed INT,
	minigames_completed INT,
	total_quiz_score INT,
	total_minigame_score INT,
	average_accuracy DECIMAL(5, 2),
	total_time_spent INT,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- ============================================
-- STREAKS (CACHED AGG)
-- ============================================
CREATE TABLE IF NOT EXISTS streaks (
	streak_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INT NOT NULL,
	current_streak INT,
	longest_streak INT,
	last_activity_date DATE,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- ============================================
-- LEADERBOARD CACHE (SQLITE ONLY)
-- ============================================
CREATE TABLE IF NOT EXISTS leaderboard (
	user_id INT NOT NULL,
	total_score INT,
	average_accuracy DECIMAL(5, 2),
	lessons_completed INT,
	current_streak INT,
	rank_position INT,
	last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES users (user_id)
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
	FOREIGN KEY (user_id) REFERENCES users (user_id),
	FOREIGN KEY (quiz_id) REFERENCES quizzes (quiz_id)
);

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
	FOREIGN KEY (user_id) REFERENCES users (user_id),
	FOREIGN KEY (minigame_id) REFERENCES minigames (minigame_id)
);

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