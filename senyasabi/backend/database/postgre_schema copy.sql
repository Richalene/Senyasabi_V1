create table public.badges (
  badge_id bigint generated always as identity not null,
  badge_code character varying(100) not null,
  badge_name character varying(100) not null,
  description text null,
  is_deleted boolean not null default false,
  constraint badges_pkey primary key (badge_id),
  constraint badges_badge_code_key unique (badge_code)
) TABLESPACE pg_default;

create table public.content_versions (
  content_version_id bigint generated always as identity not null,
  version_number integer not null,
  released_at timestamp with time zone not null default now(),
  changelog text null,
  is_published boolean not null default false,
  is_deleted boolean not null default false,
  updated_at timestamp with time zone not null default now(),
  constraint content_versions_pkey primary key (content_version_id),
  constraint content_versions_version_number_key unique (version_number)
) TABLESPACE pg_default;

create trigger trg_content_versions_updated BEFORE
update on content_versions for EACH row
execute FUNCTION set_updated_at ();

create table public.leaderboard_cache (
  board_code character varying(20) not null,
  user_id uuid not null,
  display_name character varying(255) not null,
  total_score bigint not null default 0,
  rank_position integer not null,
  current_streak integer not null default 0,
  badge_count integer not null default 0,
  fetched_at timestamp with time zone null,
  constraint leaderboard_cache_pkey primary key (board_code, user_id)
) TABLESPACE pg_default;

create index IF not exists idx_leaderboard_cache_rank on public.leaderboard_cache using btree (board_code, rank_position) TABLESPACE pg_default;

create table public.lesson_media (
  lesson_id bigint not null,
  media_id bigint not null,
  media_role text not null,
  display_order integer not null default 1,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint lesson_media_pkey primary key (lesson_id, media_id, media_role),
  constraint lesson_media_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint lesson_media_lesson_id_fkey foreign KEY (lesson_id) references lessons (lesson_id) on delete RESTRICT,
  constraint lesson_media_media_id_fkey foreign KEY (media_id) references media_files (media_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_lesson_media_version on public.lesson_media using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_lesson_media_updated BEFORE
update on lesson_media for EACH row
execute FUNCTION set_updated_at ();

create table public.lesson_progress (
  user_id uuid not null,
  lesson_id bigint not null,
  completion_percentage numeric(5, 2) not null default 0.00,
  status text not null default 'Not Started'::text,
  last_accessed timestamp with time zone null,
  completed_at timestamp with time zone null,
  time_spent_seconds bigint not null default 0,
  client_updated_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint lesson_progress_pkey primary key (user_id, lesson_id),
  constraint lesson_progress_lesson_id_fkey foreign KEY (lesson_id) references lessons (lesson_id) on delete RESTRICT,
  constraint lesson_progress_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE,
  constraint lesson_progress_completion_percentage_check check (
    (
      (completion_percentage >= (0)::numeric)
      and (completion_percentage <= (100)::numeric)
    )
  ),
  constraint lesson_progress_check check (
    (
      (status <> 'Completed'::text)
      or (completed_at is not null)
    )
  ),
  constraint lesson_progress_status_check check (
    (
      status = any (
        array[
          'Not Started'::text,
          'In Progress'::text,
          'Completed'::text
        ]
      )
    )
  ),
  constraint lesson_progress_time_spent_seconds_check check ((time_spent_seconds >= 0))
) TABLESPACE pg_default;

create index IF not exists idx_lesson_progress_lesson on public.lesson_progress using btree (lesson_id) TABLESPACE pg_default;

create index IF not exists idx_lesson_progress_user_updated on public.lesson_progress using btree (user_id, updated_at) TABLESPACE pg_default;

create trigger trg_lesson_progress_streak
after INSERT
or DELETE
or
update on lesson_progress for EACH row
execute FUNCTION trg_recalculate_user_streak ();

create trigger trg_lesson_progress_updated BEFORE
update on lesson_progress for EACH row
execute FUNCTION set_updated_at ();

create table public.lesson_signs (
  lesson_id bigint not null,
  sign_id bigint not null,
  display_order integer not null default 1,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint lesson_signs_pkey primary key (lesson_id, sign_id),
  constraint lesson_signs_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint lesson_signs_lesson_id_fkey foreign KEY (lesson_id) references lessons (lesson_id) on delete RESTRICT,
  constraint lesson_signs_sign_id_fkey foreign KEY (sign_id) references signs (sign_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_lesson_signs_sign on public.lesson_signs using btree (sign_id) TABLESPACE pg_default;

create index IF not exists idx_lesson_signs_version on public.lesson_signs using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_lesson_signs_updated BEFORE
update on lesson_signs for EACH row
execute FUNCTION set_updated_at ();

create table public.lessons (
  lesson_id bigint generated always as identity not null,
  lesson_code character varying(100) not null,
  title character varying(100) not null,
  description text null,
  parent_module bigint not null,
  lesson_order integer not null,
  is_active boolean not null default true,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint lessons_pkey primary key (lesson_id),
  constraint lessons_lesson_code_key unique (lesson_code),
  constraint lessons_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint lessons_parent_module_fkey foreign KEY (parent_module) references modules (module_id) on delete RESTRICT
) TABLESPACE pg_default;

create unique INDEX IF not exists idx_lessons_module_order on public.lessons using btree (parent_module, lesson_order) TABLESPACE pg_default
where
  (not is_deleted);

create index IF not exists idx_lessons_content_version on public.lessons using btree (content_version_id) TABLESPACE pg_default;

create index IF not exists idx_lessons_parent_module on public.lessons using btree (parent_module) TABLESPACE pg_default;

create trigger trg_lessons_updated BEFORE
update on lessons for EACH row
execute FUNCTION set_updated_at ();

create table public.media_files (
  media_id bigint generated always as identity not null,
  file_name character varying(255) null,
  object_key text not null,
  media_type text not null,
  width integer null,
  height integer null,
  duration_seconds integer null,
  file_size bigint null,
  checksum bytea null,
  content_version_id bigint not null,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  constraint media_files_pkey primary key (media_id),
  constraint media_files_object_key_key unique (object_key),
  constraint media_files_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint media_files_height_check check (
    (
      (height is null)
      or (height > 0)
    )
  ),
  constraint media_files_media_type_check check (
    (
      media_type = any (array['Image'::text, 'Video'::text])
    )
  ),
  constraint media_files_width_check check (
    (
      (width is null)
      or (width > 0)
    )
  ),
  constraint media_files_duration_seconds_check check (
    (
      (duration_seconds is null)
      or (duration_seconds >= 0)
    )
  ),
  constraint media_files_file_size_check check (
    (
      (file_size is null)
      or (file_size >= 0)
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_media_files_version on public.media_files using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_media_files_updated BEFORE
update on media_files for EACH row
execute FUNCTION set_updated_at ();

create table public.media_files (
  media_id bigint generated always as identity not null,
  file_name character varying(255) null,
  object_key text not null,
  media_type text not null,
  width integer null,
  height integer null,
  duration_seconds integer null,
  file_size bigint null,
  checksum bytea null,
  content_version_id bigint not null,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  constraint media_files_pkey primary key (media_id),
  constraint media_files_object_key_key unique (object_key),
  constraint media_files_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint media_files_height_check check (
    (
      (height is null)
      or (height > 0)
    )
  ),
  constraint media_files_media_type_check check (
    (
      media_type = any (array['Image'::text, 'Video'::text])
    )
  ),
  constraint media_files_width_check check (
    (
      (width is null)
      or (width > 0)
    )
  ),
  constraint media_files_duration_seconds_check check (
    (
      (duration_seconds is null)
      or (duration_seconds >= 0)
    )
  ),
  constraint media_files_file_size_check check (
    (
      (file_size is null)
      or (file_size >= 0)
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_media_files_version on public.media_files using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_media_files_updated BEFORE
update on media_files for EACH row
execute FUNCTION set_updated_at ();

create table public.minigame_signs (
  minigame_id bigint not null,
  sign_id bigint not null,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint minigame_signs_pkey primary key (minigame_id, sign_id),
  constraint minigame_signs_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint minigame_signs_minigame_id_fkey foreign KEY (minigame_id) references minigames (minigame_id) on delete CASCADE,
  constraint minigame_signs_sign_id_fkey foreign KEY (sign_id) references signs (sign_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_minigame_signs_version on public.minigame_signs using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_minigame_signs_updated BEFORE
update on minigame_signs for EACH row
execute FUNCTION set_updated_at ();

create table public.minigames (
  minigame_id bigint generated always as identity not null,
  minigame_code character varying(100) not null,
  game_name character varying(100) not null,
  game_type character varying(50) not null,
  module_id bigint not null,
  description text null,
  config jsonb not null default '{}'::jsonb,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint minigames_pkey primary key (minigame_id),
  constraint minigames_minigame_code_key unique (minigame_code),
  constraint minigames_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint minigames_module_id_fkey foreign KEY (module_id) references modules (module_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_minigames_version on public.minigames using btree (content_version_id) TABLESPACE pg_default;

create index IF not exists idx_minigames_module on public.minigames using btree (module_id) TABLESPACE pg_default;

create trigger trg_minigames_updated BEFORE
update on minigames for EACH row
execute FUNCTION set_updated_at ();

create table public.modules (
  module_id bigint generated always as identity not null,
  module_code character varying(100) not null,
  title character varying(100) not null,
  description text null,
  module_order integer not null,
  is_active boolean not null default true,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint modules_pkey primary key (module_id),
  constraint modules_module_code_key unique (module_code),
  constraint modules_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_modules_content_version on public.modules using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_modules_updated BEFORE
update on modules for EACH row
execute FUNCTION set_updated_at ();

create table public.quiz_attempts (
  attempt_id uuid not null,
  user_id uuid not null,
  quiz_id bigint not null,
  started_at timestamp with time zone not null default now(),
  completed_at timestamp with time zone null,
  duration_seconds integer null,
  score integer null,
  max_score integer not null default 100,
  percentage numeric(5, 2) null,
  passed boolean not null default false,
  camera_accuracy numeric(5, 2) null,
  mc_accuracy numeric(5, 2) null,
  synced_at timestamp with time zone not null default now(),
  camera_correct integer null,
  camera_total integer null,
  constraint quiz_attempts_pkey primary key (attempt_id),
  constraint quiz_attempts_quiz_id_fkey foreign KEY (quiz_id) references quizzes (quiz_id) on delete RESTRICT,
  constraint quiz_attempts_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE,
  constraint quiz_attempts_duration_seconds_check check (
    (
      (duration_seconds is null)
      or (duration_seconds >= 0)
    )
  ),
  constraint quiz_attempts_max_score_check check ((max_score > 0)),
  constraint quiz_attempts_camera_accuracy_check check (
    (
      (camera_accuracy is null)
      or (
        (camera_accuracy >= (0)::numeric)
        and (camera_accuracy <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_percentage_check check (
    (
      (percentage is null)
      or (
        (percentage >= (0)::numeric)
        and (percentage <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_score_check check (
    (
      (score is null)
      or (score >= 0)
    )
  ),
  constraint quiz_attempts_mc_accuracy_check check (
    (
      (mc_accuracy is null)
      or (
        (mc_accuracy >= (0)::numeric)
        and (mc_accuracy <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_check check (
    (
      (completed_at is null)
      or (completed_at >= started_at)
    )
  ),
  constraint quiz_attempts_check1 check (
    (
      (score is null)
      or (score <= max_score)
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_quiz_attempts_user on public.quiz_attempts using btree (user_id, synced_at) TABLESPACE pg_default;

create index IF not exists idx_quiz_attempts_quiz on public.quiz_attempts using btree (quiz_id) TABLESPACE pg_default;

create trigger trg_quiz_attempts_leaderboard
after INSERT
or DELETE
or
update on quiz_attempts for EACH STATEMENT
execute FUNCTION trg_refresh_leaderboard ();

create trigger trg_quiz_attempts_streak
after INSERT
or DELETE
or
update on quiz_attempts for EACH row
execute FUNCTION trg_recalculate_user_streak ();

create table public.quiz_attempts (
  attempt_id uuid not null,
  user_id uuid not null,
  quiz_id bigint not null,
  started_at timestamp with time zone not null default now(),
  completed_at timestamp with time zone null,
  duration_seconds integer null,
  score integer null,
  max_score integer not null default 100,
  percentage numeric(5, 2) null,
  passed boolean not null default false,
  camera_accuracy numeric(5, 2) null,
  mc_accuracy numeric(5, 2) null,
  synced_at timestamp with time zone not null default now(),
  camera_correct integer null,
  camera_total integer null,
  constraint quiz_attempts_pkey primary key (attempt_id),
  constraint quiz_attempts_quiz_id_fkey foreign KEY (quiz_id) references quizzes (quiz_id) on delete RESTRICT,
  constraint quiz_attempts_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE,
  constraint quiz_attempts_duration_seconds_check check (
    (
      (duration_seconds is null)
      or (duration_seconds >= 0)
    )
  ),
  constraint quiz_attempts_max_score_check check ((max_score > 0)),
  constraint quiz_attempts_camera_accuracy_check check (
    (
      (camera_accuracy is null)
      or (
        (camera_accuracy >= (0)::numeric)
        and (camera_accuracy <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_percentage_check check (
    (
      (percentage is null)
      or (
        (percentage >= (0)::numeric)
        and (percentage <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_score_check check (
    (
      (score is null)
      or (score >= 0)
    )
  ),
  constraint quiz_attempts_mc_accuracy_check check (
    (
      (mc_accuracy is null)
      or (
        (mc_accuracy >= (0)::numeric)
        and (mc_accuracy <= (100)::numeric)
      )
    )
  ),
  constraint quiz_attempts_check check (
    (
      (completed_at is null)
      or (completed_at >= started_at)
    )
  ),
  constraint quiz_attempts_check1 check (
    (
      (score is null)
      or (score <= max_score)
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_quiz_attempts_user on public.quiz_attempts using btree (user_id, synced_at) TABLESPACE pg_default;

create index IF not exists idx_quiz_attempts_quiz on public.quiz_attempts using btree (quiz_id) TABLESPACE pg_default;

create trigger trg_quiz_attempts_leaderboard
after INSERT
or DELETE
or
update on quiz_attempts for EACH STATEMENT
execute FUNCTION trg_refresh_leaderboard ();

create trigger trg_quiz_attempts_streak
after INSERT
or DELETE
or
update on quiz_attempts for EACH row
execute FUNCTION trg_recalculate_user_streak ();

create table public.quizzes (
  quiz_id bigint generated always as identity not null,
  module_id bigint not null,
  title character varying(100) not null,
  passing_score integer not null default 70,
  time_limit_seconds integer null,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  quiz_code character varying not null,
  category_code character varying null,
  config jsonb not null default '{}'::jsonb,
  constraint quizzes_pkey primary key (quiz_id),
  constraint quizzes_quiz_code_key unique (quiz_code),
  constraint quizzes_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint quizzes_module_id_fkey foreign KEY (module_id) references modules (module_id) on delete RESTRICT,
  constraint quizzes_passing_score_check check (
    (
      (passing_score >= 0)
      and (passing_score <= 100)
    )
  ),
  constraint quizzes_time_limit_seconds_check check (
    (
      (time_limit_seconds is null)
      or (time_limit_seconds > 0)
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_quizzes_version on public.quizzes using btree (content_version_id) TABLESPACE pg_default;

create index IF not exists idx_quizzes_module on public.quizzes using btree (module_id) TABLESPACE pg_default;

create trigger trg_quizzes_updated BEFORE
update on quizzes for EACH row
execute FUNCTION set_updated_at ();

create table public.sign_media (
  sign_id bigint not null,
  media_id bigint not null,
  media_role text not null default 'demonstration'::text,
  display_order integer not null default 1,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint sign_media_pkey primary key (sign_id, media_id, media_role),
  constraint sign_media_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint sign_media_media_id_fkey foreign KEY (media_id) references media_files (media_id) on delete RESTRICT,
  constraint sign_media_sign_id_fkey foreign KEY (sign_id) references signs (sign_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_sign_media_version on public.sign_media using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_sign_media_updated BEFORE
update on sign_media for EACH row
execute FUNCTION set_updated_at ();

create table public.sign_media (
  sign_id bigint not null,
  media_id bigint not null,
  media_role text not null default 'demonstration'::text,
  display_order integer not null default 1,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint sign_media_pkey primary key (sign_id, media_id, media_role),
  constraint sign_media_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT,
  constraint sign_media_media_id_fkey foreign KEY (media_id) references media_files (media_id) on delete RESTRICT,
  constraint sign_media_sign_id_fkey foreign KEY (sign_id) references signs (sign_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_sign_media_version on public.sign_media using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_sign_media_updated BEFORE
update on sign_media for EACH row
execute FUNCTION set_updated_at ();

create table public.signs (
  sign_id bigint generated always as identity not null,
  sign_code character varying(100) not null,
  label character varying(100) not null,
  recognition_label character varying(100) not null,
  updated_at timestamp with time zone not null default now(),
  is_deleted boolean not null default false,
  content_version_id bigint not null,
  constraint signs_pkey primary key (sign_id),
  constraint signs_sign_code_key unique (sign_code),
  constraint signs_content_version_id_fkey foreign KEY (content_version_id) references content_versions (content_version_id) on delete RESTRICT
) TABLESPACE pg_default;

create index IF not exists idx_signs_content_version on public.signs using btree (content_version_id) TABLESPACE pg_default;

create trigger trg_signs_updated BEFORE
update on signs for EACH row
execute FUNCTION set_updated_at ();

create table public.streaks (
  user_id uuid not null,
  current_streak integer not null default 0,
  longest_streak integer not null default 0,
  last_activity_date date null,
  updated_at timestamp with time zone not null default now(),
  constraint streaks_pkey primary key (user_id),
  constraint streaks_user_id_fkey foreign KEY (user_id) references auth.users (id) on delete CASCADE,
  constraint streaks_current_streak_check check ((current_streak >= 0)),
  constraint streaks_longest_streak_check check ((longest_streak >= 0))
) TABLESPACE pg_default;

create trigger trg_streaks_leaderboard
after INSERT
or DELETE
or
update on streaks for EACH STATEMENT
execute FUNCTION trg_refresh_leaderboard ();

create trigger trg_streaks_updated BEFORE
update on streaks for EACH row
execute FUNCTION set_updated_at ();

create table public.user_statistics (
  user_id uuid not null,
  lessons_completed bigint not null default 0,
  quizzes_completed bigint not null default 0,
  minigames_completed bigint not null default 0,
  total_quiz_score bigint not null default 0,
  total_minigame_score bigint not null default 0,
  average_accuracy numeric(5, 2) null,
  total_time_spent_seconds bigint not null default 0,
  updated_at timestamp with time zone not null default now(),
  constraint user_statistics_pkey primary key (user_id),
  constraint user_statistics_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE
) TABLESPACE pg_default;

create table public.user_statistics (
  user_id uuid not null,
  lessons_completed bigint not null default 0,
  quizzes_completed bigint not null default 0,
  minigames_completed bigint not null default 0,
  total_quiz_score bigint not null default 0,
  total_minigame_score bigint not null default 0,
  average_accuracy numeric(5, 2) null,
  total_time_spent_seconds bigint not null default 0,
  updated_at timestamp with time zone not null default now(),
  constraint user_statistics_pkey primary key (user_id),
  constraint user_statistics_user_id_fkey foreign KEY (user_id) references users (user_id) on delete CASCADE
) TABLESPACE pg_default;

create view public.v_module_progress_live
with
  (security_invoker = true) as
select
  u.user_id,
  m.module_id,
  count(l.lesson_id) as total_lessons,
  count(l.lesson_id) filter (
    where
      lp.status = 'Completed'::text
  ) as completed_lessons,
  COALESCE(
    round(
      sum(
        case
          when lp.status = 'Completed'::text then 100.0
          else COALESCE(lp.completion_percentage, 0::numeric)
        end
      ) / NULLIF(count(l.lesson_id), 0)::numeric,
      2
    ),
    0::numeric
  ) as completion_percentage,
  case
    when count(l.lesson_id) = 0 then 'Not Started'::text
    when count(l.lesson_id) filter (
      where
        lp.status = 'Completed'::text
    ) = count(l.lesson_id) then 'Completed'::text
    when count(l.lesson_id) filter (
      where
        COALESCE(lp.completion_percentage, 0::numeric) > 0::numeric
        or (
          lp.status = any (array['In Progress'::text, 'Completed'::text])
        )
    ) > 0 then 'In Progress'::text
    else 'Not Started'::text
  end as status,
  max(lp.last_accessed) as last_accessed,
  case
    when count(l.lesson_id) > 0
    and count(l.lesson_id) filter (
      where
        lp.status = 'Completed'::text
    ) = count(l.lesson_id) then max(lp.completed_at)
    else null::timestamp with time zone
  end as completed_at
from
  users u
  cross join modules m
  left join lessons l on l.parent_module = m.module_id
  and l.is_active = true
  and l.is_deleted = false
  left join lesson_progress lp on lp.user_id = u.user_id
  and lp.lesson_id = l.lesson_id
where
  m.is_active = true
  and m.is_deleted = false
group by
  u.user_id,
  m.module_id;

create view public.v_user_statistics_live
with
  (security_invoker = true) as
select
  user_id,
  (
    select
      count(*) as count
    from
      lesson_progress lp
    where
      lp.user_id = u.user_id
      and lp.status = 'Completed'::text
  ) as lessons_completed,
  (
    select
      count(*) as count
    from
      quiz_attempts qa
    where
      qa.user_id = u.user_id
      and qa.completed_at is not null
  ) as quizzes_completed,
  (
    select
      count(*) as count
    from
      minigame_attempts ma
    where
      ma.user_id = u.user_id
      and ma.completed_at is not null
  ) as minigames_completed,
  (
    select
      COALESCE(sum(qa.score), 0::bigint) as "coalesce"
    from
      quiz_attempts qa
    where
      qa.user_id = u.user_id
      and qa.completed_at is not null
  ) as total_quiz_score,
  (
    select
      COALESCE(sum(ma.score), 0::bigint) as "coalesce"
    from
      minigame_attempts ma
    where
      ma.user_id = u.user_id
      and ma.completed_at is not null
  ) as total_minigame_score,
  (
    select
      avg(a.accuracy)::numeric(5, 2) as avg
    from
      (
        select
          qa.percentage as accuracy
        from
          quiz_attempts qa
        where
          qa.user_id = u.user_id
          and qa.completed_at is not null
          and qa.percentage is not null
        union all
        select
          ma.accuracy
        from
          minigame_attempts ma
        where
          ma.user_id = u.user_id
          and ma.completed_at is not null
          and ma.accuracy is not null
      ) a
  ) as average_accuracy,
  (
    COALESCE(
      (
        select
          sum(lp.time_spent_seconds) as sum
        from
          lesson_progress lp
        where
          lp.user_id = u.user_id
      ),
      0::numeric
    ) + COALESCE(
      (
        select
          sum(
            COALESCE(
              qa.duration_seconds::numeric,
              EXTRACT(
                epoch
                from
                  qa.completed_at - qa.started_at
              )
            )
          ) as sum
        from
          quiz_attempts qa
        where
          qa.user_id = u.user_id
          and qa.completed_at is not null
      ),
      0::numeric
    ) + COALESCE(
      (
        select
          sum(ma.duration_seconds) as sum
        from
          minigame_attempts ma
        where
          ma.user_id = u.user_id
          and ma.completed_at is not null
      ),
      0::bigint
    )::numeric
  )::bigint as total_time_spent_seconds
from
  users u;

create table auth.users (
  instance_id uuid null,
  id uuid not null,
  aud character varying(255) null,
  role character varying(255) null,
  email character varying(255) null,
  encrypted_password character varying(255) null,
  email_confirmed_at timestamp with time zone null,
  invited_at timestamp with time zone null,
  confirmation_token character varying(255) null,
  confirmation_sent_at timestamp with time zone null,
  recovery_token character varying(255) null,
  recovery_sent_at timestamp with time zone null,
  email_change_token_new character varying(255) null,
  email_change character varying(255) null,
  email_change_sent_at timestamp with time zone null,
  last_sign_in_at timestamp with time zone null,
  raw_app_meta_data jsonb null,
  raw_user_meta_data jsonb null,
  is_super_admin boolean null,
  created_at timestamp with time zone null,
  updated_at timestamp with time zone null,
  phone text null default null::character varying,
  phone_confirmed_at timestamp with time zone null,
  phone_change text null default ''::character varying,
  phone_change_token character varying(255) null default ''::character varying,
  phone_change_sent_at timestamp with time zone null,
  confirmed_at timestamp with time zone GENERATED ALWAYS as (LEAST(email_confirmed_at, phone_confirmed_at)) STORED null,
  email_change_token_current character varying(255) null default ''::character varying,
  email_change_confirm_status smallint null default 0,
  banned_until timestamp with time zone null,
  reauthentication_token character varying(255) null default ''::character varying,
  reauthentication_sent_at timestamp with time zone null,
  is_sso_user boolean not null default false,
  deleted_at timestamp with time zone null,
  is_anonymous boolean not null default false,
  constraint users_pkey primary key (id),
  constraint users_phone_key unique (phone),
  constraint users_email_change_confirm_status_check check (
    (
      (email_change_confirm_status >= 0)
      and (email_change_confirm_status <= 2)
    )
  )
) TABLESPACE pg_default;

create index IF not exists users_instance_id_idx on auth.users using btree (instance_id) TABLESPACE pg_default;

create index IF not exists users_instance_id_email_idx on auth.users using btree (instance_id, lower((email)::text)) TABLESPACE pg_default;

create unique INDEX IF not exists confirmation_token_idx on auth.users using btree (confirmation_token) TABLESPACE pg_default
where
  ((confirmation_token)::text !~ '^[0-9 ]*$'::text);

create unique INDEX IF not exists recovery_token_idx on auth.users using btree (recovery_token) TABLESPACE pg_default
where
  ((recovery_token)::text !~ '^[0-9 ]*$'::text);

create unique INDEX IF not exists email_change_token_current_idx on auth.users using btree (email_change_token_current) TABLESPACE pg_default
where
  (
    (email_change_token_current)::text !~ '^[0-9 ]*$'::text
  );

create unique INDEX IF not exists email_change_token_new_idx on auth.users using btree (email_change_token_new) TABLESPACE pg_default
where
  (
    (email_change_token_new)::text !~ '^[0-9 ]*$'::text
  );

create unique INDEX IF not exists reauthentication_token_idx on auth.users using btree (reauthentication_token) TABLESPACE pg_default
where
  (
    (reauthentication_token)::text !~ '^[0-9 ]*$'::text
  );

create unique INDEX IF not exists users_email_partial_key on auth.users using btree (email) TABLESPACE pg_default
where
  (is_sso_user = false);

create index IF not exists users_is_anonymous_idx on auth.users using btree (is_anonymous) TABLESPACE pg_default;

create index IF not exists idx_users_email on auth.users using btree (email) TABLESPACE pg_default;

create index IF not exists idx_users_created_at_desc on auth.users using btree (created_at desc) TABLESPACE pg_default;

create index IF not exists idx_users_last_sign_in_at_desc on auth.users using btree (last_sign_in_at desc) TABLESPACE pg_default;

create index IF not exists idx_users_name on auth.users using btree (((raw_user_meta_data ->> 'name'::text))) TABLESPACE pg_default
where
  ((raw_user_meta_data ->> 'name'::text) is not null);

create trigger on_auth_user_created
after INSERT on auth.users for EACH row
execute FUNCTION handle_new_auth_user ();