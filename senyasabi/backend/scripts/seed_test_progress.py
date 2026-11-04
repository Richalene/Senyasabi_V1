"""
DEV/TEST ONLY: fake learner progress for the five testuser1..5 accounts (Supabase/Postgres).

Deterministic and idempotent: attempt IDs are uuid5-derived, everything else is an
upsert / ON CONFLICT DO NOTHING. Only rows for testuser1..5 are written; real users
are never touched. To remove: delete rows for those user_ids.

Usage (from senyasabi/):  python -m backend.scripts.seed_test_progress [--dry-run]
"""
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from backend import config

NS = uuid.UUID("5e11a5ab-0000-4000-8000-00000000d3ad")
# per user: (lessons completed, extra lesson in progress %, quiz scores by module order,
#            minigame scores per game, streak (current, longest), days of activity)
PROFILES = {
    1: dict(lessons=20, partial=60, quizzes=[92, 85, 78, 88, 74, 95], games=[420, 380, 350], streak=(7, 9), days=9),
    2: dict(lessons=14, partial=40, quizzes=[81, 66, 90, 72], games=[310, 280, 240], streak=(4, 6), days=7),
    3: dict(lessons=9, partial=75, quizzes=[77, 58, 83], games=[260, 190], streak=(2, 4), days=5),
    4: dict(lessons=5, partial=30, quizzes=[64], games=[150], streak=(1, 2), days=3),
    5: dict(lessons=2, partial=50, quizzes=[], games=[], streak=(1, 1), days=1),
}
BADGES = {"first": "FIRST_STEPS", "quiz": "QUIZ_TAKER", "game": "GAME_ON", "roll": "ON_A_ROLL"}


def main(dry_run=False):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    e = create_engine(config.POSTGRESQL_URL, poolclass=NullPool, connect_args={"prepare_threshold": None})
    with e.connect() as c:
        users = {r[0]: r[1] for r in c.execute(text(
            "SELECT username, user_id FROM public.users WHERE username ~ '^testuser[1-5]$'"))}
        lessons = c.execute(text(
            "SELECT l.lesson_id, l.parent_module, m.module_order FROM public.lessons l "
            "JOIN public.modules m ON m.module_id=l.parent_module ORDER BY m.module_order, l.lesson_order")).all()
        quizzes = c.execute(text(
            "SELECT q.quiz_id, q.module_id FROM public.quizzes q JOIN public.modules m USING(module_id) "
            "ORDER BY m.module_order")).all()
        games = [r[0] for r in c.execute(text("SELECT minigame_id FROM public.minigames ORDER BY minigame_id"))]
        badge_ids = {r[0]: r[1] for r in c.execute(text("SELECT badge_code, badge_id FROM public.badges"))}
        by_module = {}
        for lid, mid, _ in lessons:
            by_module.setdefault(mid, []).append(lid)

        for i, p in PROFILES.items():
            uid = users.get(f"testuser{i}")
            if uid is None:
                print(f"skip testuser{i}: not found"); continue
            n = p["lessons"]
            done = [l[0] for l in lessons[:n]]
            for k, lid in enumerate(lessons[:n + 1]):
                completed = k < n
                when = now - timedelta(days=p["days"] - 1 - (k * p["days"] // max(n, 1)) % p["days"], hours=k % 5)
                c.execute(text("""
                    INSERT INTO public.lesson_progress (user_id, lesson_id, completion_percentage, status,
                        last_accessed, completed_at, time_spent_seconds, client_updated_at)
                    VALUES (:u,:l,:pct,:st,:t,:ct,:ts,:t)
                    ON CONFLICT (user_id, lesson_id) DO NOTHING"""),
                    dict(u=uid, l=lid[0] if False else lid[0], pct=100 if completed else p["partial"],
                         st="Completed" if completed else "In Progress", t=when,
                         ct=when if completed else None, ts=240 + 35 * k))
            # quizzes: only for modules whose lessons are all completed
            qdone = 0
            for qi, score in enumerate(p["quizzes"]):
                quiz_id, module_id = quizzes[qi]
                if not set(by_module[module_id]) <= set(done):
                    continue
                started = now - timedelta(days=max(p["days"] - 1 - qi, 0), hours=2)
                c.execute(text("""
                    INSERT INTO public.quiz_attempts (attempt_id, user_id, quiz_id, started_at, completed_at,
                        duration_seconds, score, max_score, percentage, passed, camera_accuracy, mc_accuracy)
                    VALUES (:a,:u,:q,:s,:s + interval '4 minutes',240,:sc,100,:sc,:ok,:ca,:ma)
                    ON CONFLICT (attempt_id) DO NOTHING"""),
                    dict(a=uuid.uuid5(NS, f"quiz-{i}-{qi}"), u=uid, q=quiz_id, s=started, sc=score,
                         ok=score >= 70, ca=max(score - 6, 0), ma=min(score + 5, 100)))
                qdone += 1
            for gi, score in enumerate(p["games"]):
                started = now - timedelta(days=max(p["days"] - 1 - gi, 0), hours=1)
                c.execute(text("""
                    INSERT INTO public.minigame_attempts (game_attempt_id, user_id, minigame_id, started_at,
                        completed_at, score, duration_seconds, accuracy)
                    VALUES (:a,:u,:g,:s,:s + interval '1 minute',:sc,60,:acc)
                    ON CONFLICT (game_attempt_id) DO NOTHING"""),
                    dict(a=uuid.uuid5(NS, f"game-{i}-{gi}"), u=uid, g=games[gi], s=started, sc=score,
                         acc=min(60 + score // 10, 99)))
            cur, longest = p["streak"]
            c.execute(text("""
                INSERT INTO public.streaks (user_id, current_streak, longest_streak, last_activity_date)
                VALUES (:u,:c,:l,:d)
                ON CONFLICT (user_id) DO UPDATE SET current_streak=EXCLUDED.current_streak,
                    longest_streak=EXCLUDED.longest_streak, last_activity_date=EXCLUDED.last_activity_date"""),
                dict(u=uid, c=cur, l=longest, d=now.date()))
            earned = ["first"] + (["quiz"] if qdone else []) + (["game"] if p["games"] else []) + (
                ["roll"] if longest >= 7 or cur >= 7 else [])
            for b in earned:
                c.execute(text("INSERT INTO public.user_badges (user_id, badge_id) VALUES (:u,:b) "
                               "ON CONFLICT DO NOTHING"), dict(u=uid, b=badge_ids[BADGES[b]]))
            c.execute(text("SELECT public.refresh_user_statistics(:u)"), dict(u=uid))
            print(f"testuser{i}: {n} lessons done, {qdone} quizzes, {len(p['games'])} games, badges={earned}", flush=True)
        c.rollback() if dry_run else c.commit()
        print("DRY RUN: rolled back" if dry_run else "Committed")


if __name__ == "__main__":
    main("--dry-run" in sys.argv)

