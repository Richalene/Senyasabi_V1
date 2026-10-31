-- Migration 001: Initialize migration tracking
-- This migration creates the schema_migrations table to track applied migrations

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Mark this migration as applied
INSERT OR IGNORE INTO schema_migrations (migration, applied_at)
VALUES ('001_init_migrations.sql', CURRENT_TIMESTAMP);
