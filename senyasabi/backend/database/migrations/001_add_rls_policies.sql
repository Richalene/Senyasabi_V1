-- Add RLS policies for distributed client access
-- This script enables safe anon/authenticated access to PostgreSQL
-- Content tables: read-only for anon and authenticated
-- User tables: authenticated users can read/write only their own data

BEGIN;

-- Drop existing restrictive policies if they exist
DROP POLICY IF EXISTS "modules_read" ON public.modules;
DROP POLICY IF EXISTS "lessons_read" ON public.lessons;
DROP POLICY IF EXISTS "signs_read" ON public.signs;
DROP POLICY IF EXISTS "media_files_read" ON public.media_files;
DROP POLICY IF EXISTS "lesson_signs_read" ON public.lesson_signs;
DROP POLICY IF EXISTS "sign_media_read" ON public.sign_media;
DROP POLICY IF EXISTS "lesson_media_read" ON public.lesson_media;
DROP POLICY IF EXISTS "quizzes_read" ON public.quizzes;
DROP POLICY IF EXISTS "quiz_signs_read" ON public.quiz_signs;
DROP POLICY IF EXISTS "minigames_read" ON public.minigames;
DROP POLICY IF EXISTS "minigame_signs_read" ON public.minigame_signs;
DROP POLICY IF EXISTS "badges_read" ON public.badges;
DROP POLICY IF EXISTS "content_versions_read" ON public.content_versions;

DROP POLICY IF EXISTS "users_read_own" ON public.users;
DROP POLICY IF EXISTS "users_insert_signup" ON public.users;
DROP POLICY IF EXISTS "lesson_progress_user" ON public.lesson_progress;
DROP POLICY IF EXISTS "quiz_attempts_user" ON public.quiz_attempts;
DROP POLICY IF EXISTS "minigame_attempts_user" ON public.minigame_attempts;
DROP POLICY IF EXISTS "user_badges_user" ON public.user_badges;
DROP POLICY IF EXISTS "streaks_user" ON public.streaks;
DROP POLICY IF EXISTS "user_statistics_user" ON public.user_statistics;

-- Grant usage permissions to anon and authenticated
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Content version table (read-only)
CREATE POLICY "content_versions_read" ON public.content_versions
  FOR SELECT TO anon, authenticated
  USING (is_published = true AND is_deleted = false);

-- Modules table (read-only)
CREATE POLICY "modules_read" ON public.modules
  FOR SELECT TO anon, authenticated
  USING (is_active = true AND is_deleted = false);

-- Lessons table (read-only)
CREATE POLICY "lessons_read" ON public.lessons
  FOR SELECT TO anon, authenticated
  USING (is_active = true AND is_deleted = false);

-- Signs table (read-only)
CREATE POLICY "signs_read" ON public.signs
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Media files table (read-only)
CREATE POLICY "media_files_read" ON public.media_files
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Lesson signs junction table (read-only)
CREATE POLICY "lesson_signs_read" ON public.lesson_signs
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Sign media junction table (read-only)
CREATE POLICY "sign_media_read" ON public.sign_media
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Lesson media junction table (read-only)
CREATE POLICY "lesson_media_read" ON public.lesson_media
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Quizzes table (read-only)
CREATE POLICY "quizzes_read" ON public.quizzes
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Quiz signs junction table (read-only)
CREATE POLICY "quiz_signs_read" ON public.quiz_signs
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Minigames table (read-only)
CREATE POLICY "minigames_read" ON public.minigames
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Minigame signs junction table (read-only)
CREATE POLICY "minigame_signs_read" ON public.minigame_signs
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Badges table (read-only)
CREATE POLICY "badges_read" ON public.badges
  FOR SELECT TO anon, authenticated
  USING (is_deleted = false);

-- Users table (read own profile, insert on signup)
CREATE POLICY "users_read_own" ON public.users
  FOR SELECT TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "users_insert_signup" ON public.users
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Lesson progress (user-specific)
CREATE POLICY "lesson_progress_user" ON public.lesson_progress
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Quiz attempts (user-specific)
CREATE POLICY "quiz_attempts_user" ON public.quiz_attempts
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Minigame attempts (user-specific)
CREATE POLICY "minigame_attempts_user" ON public.minigame_attempts
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- User badges (user-specific)
CREATE POLICY "user_badges_user" ON public.user_badges
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Streaks (user-specific)
CREATE POLICY "streaks_user" ON public.streaks
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- User statistics (user-specific)
CREATE POLICY "user_statistics_user" ON public.user_statistics
  FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Grant SELECT on all content tables to anon and authenticated
GRANT SELECT ON public.content_versions TO anon, authenticated;
GRANT SELECT ON public.modules TO anon, authenticated;
GRANT SELECT ON public.lessons TO anon, authenticated;
GRANT SELECT ON public.signs TO anon, authenticated;
GRANT SELECT ON public.media_files TO anon, authenticated;
GRANT SELECT ON public.lesson_signs TO anon, authenticated;
GRANT SELECT ON public.sign_media TO anon, authenticated;
GRANT SELECT ON public.lesson_media TO anon, authenticated;
GRANT SELECT ON public.quizzes TO anon, authenticated;
GRANT SELECT ON public.quiz_signs TO anon, authenticated;
GRANT SELECT ON public.minigames TO anon, authenticated;
GRANT SELECT ON public.minigame_signs TO anon, authenticated;
GRANT SELECT ON public.badges TO anon, authenticated;

-- Grant SELECT, INSERT, UPDATE, DELETE on user tables to authenticated
GRANT SELECT, INSERT, UPDATE, DELETE ON public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.lesson_progress TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.quiz_attempts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.minigame_attempts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_badges TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.streaks TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_statistics TO authenticated;

-- Grant execute on statistics functions to authenticated
GRANT EXECUTE ON FUNCTION public.refresh_user_statistics(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.rebuild_user_statistics() TO authenticated;

COMMIT;

-- Verification queries (run these to verify policies are in place):
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
-- FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, policyname;
