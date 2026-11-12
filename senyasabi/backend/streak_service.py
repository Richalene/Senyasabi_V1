"""Streak rules. The local result is provisional; the server's (recalculate_streak) wins."""
import logging
import uuid
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select

from .database import models as m

log = logging.getLogger(__name__)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


# ── pure rule (mirrors public.recalculate_streak) ────────────────────────
def compute_streak(dates):
    """-> (current, longest, last_activity_date) from a set of calendar dates.

    first activity -> 1; same date -> no change (set); next date -> +1;
    gap of one or more days -> reset to 1; backfilled dates merge naturally.
    """
    days = sorted(set(dates))
    if not days:
        return 0, 0, None
    run = longest = 1
    for prev, cur in zip(days, days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)
    return run, longest, days[-1]


# ── timezone ─────────────────────────────────────────────────────────────
def _valid_tz(name):
    try:
        ZoneInfo(name)
        return bool(name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return False


def _system_tz():
    try:
        import tzlocal                      # optional: pip install tzlocal
        return tzlocal.get_localzone_name()
    except Exception:
        return None


def resolve_timezone(db, user_id) -> str:
    """The user's configured IANA zone; detects and persists one on first use."""
    user = db.get(m.User, user_id)
    name = user.timezone if user else None
    if not _valid_tz(name):
        name = _system_tz()
        if not _valid_tz(name):
            name = "UTC"
        if user is not None:
            user.timezone = name
            db.flush()
    return name


def set_timezone(db, user_id, name):
    """Hook for a settings screen. The new zone reaches the server with the next sync payload."""
    if not _valid_tz(name):
        raise ValueError(f"Unknown timezone: {name}")
    user = db.get(m.User, user_id)
    if user is not None:
        user.timezone = name
        db.flush()


# ── local activity history ───────────────────────────────────────────────
def local_activity_dates(db, user_id, tz_name):
    tz = ZoneInfo(tz_name)
    stamps = []
    stamps += db.scalars(select(m.LessonProgress.completed_at).where(
        m.LessonProgress.user_id == user_id, m.LessonProgress.status == "Completed",
        m.LessonProgress.completed_at.is_not(None)))
    stamps += db.scalars(select(m.QuizAttempt.completed_at).where(
        m.QuizAttempt.user_id == user_id, m.QuizAttempt.completed_at.is_not(None)))
    stamps += db.scalars(select(m.MinigameAttempt.completed_at).where(
        m.MinigameAttempt.user_id == user_id, m.MinigameAttempt.completed_at.is_not(None)))
    return {ts.astimezone(tz).date() for ts in stamps}


def _streak_row(db, user_id):
    row = db.get(m.Streak, user_id)
    if row is None:
        row = m.Streak(user_id=user_id, current_streak=0, longest_streak=0)
        db.add(row)
    return row


# ── activity completed (steps 2-4) ───────────────────────────────────────
def apply_activity(db, user_id):
    """Call inside the caller's transaction AFTER the activity row is flushed.
    Updates local streaks + leaderboard_cache. Returns (Streak | None, tz_name)."""
    tz_name = resolve_timezone(db, user_id)
    current, longest, last = compute_streak(local_activity_dates(db, user_id, tz_name))
    if last is None:
        return None, tz_name
    row = _streak_row(db, user_id)
    row.current_streak = current
    row.longest_streak = max(row.longest_streak or 0, longest)   # never decreases
    row.last_activity_date = last
    db.flush()
    refresh_local_leaderboard(db, user_id)
    return row, tz_name


# ── display-time recalc ─────────────────────────────────────────────────
def recalculate(db, user_id):
    """Recompute the provisional streak from local activity; persist on change.

    Safe to call whenever a streak is about to be displayed. Unlike apply_activity
    it never moves the streak backwards for activity the server already knows about:
    a newer stored last_activity_date or a higher reconciled current_streak wins.
    """
    tz_name = resolve_timezone(db, user_id)
    current, longest, last = compute_streak(local_activity_dates(db, user_id, tz_name))
    if last is None:
        return None
    row = _streak_row(db, user_id)
    stored_last = row.last_activity_date
    if stored_last is not None and stored_last > last:
        return row                                   # server saw newer activity elsewhere
    if stored_last == last and (row.current_streak or 0) > current:
        current = row.current_streak                 # reconciled value is higher; keep it
    longest = max(row.longest_streak or 0, longest)
    if ((row.current_streak or 0, row.longest_streak or 0, stored_last)
            == (current, longest, last)):
        return row
    row.current_streak = current
    row.longest_streak = longest
    row.last_activity_date = last
    db.flush()
    refresh_local_leaderboard(db, user_id)
    return row


def refresh_for_display(user_id):
    """Recalculate and return the current streak int, or None for invalid/no user."""
    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError, AttributeError):
        return None
    from .database.repository import get_streak       # lazy: avoids an import cycle
    from .database.session import session_scope
    with session_scope() as db:
        row = recalculate(db, uid)
        if row is None:
            row = get_streak(db, uid)                 # keep stored/server value
        return row.current_streak if row is not None else 0


# ── server result arrives (step 7) ───────────────────────────────────────
def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value[:10])
    return None


def reconcile(db, user_id, server):
    """Adopt the server's streak. Local activity that is still queued is not on the server
    yet, so a newer provisional result is kept until those items sync."""
    last = _as_date((server or {}).get("last_activity_date"))
    if last is None:
        return None                                   # server has nothing yet: keep local
    current = int(server.get("current_streak") or 0)
    longest = max(int(server.get("longest_streak") or 0), current)

    pending = db.scalar(select(m.SyncQueue.sync_id).where(
        m.SyncQueue.user_id == user_id, m.SyncQueue.synced_at.is_(None)).limit(1))
    if pending is not None:
        tz_name = resolve_timezone(db, user_id)
        p_cur, p_long, p_last = compute_streak(local_activity_dates(db, user_id, tz_name))
        if p_last is not None and (p_last, p_cur) > (last, current):
            current, last = p_cur, p_last
        longest = max(longest, p_long)

    row = _streak_row(db, user_id)
    row.current_streak, row.longest_streak, row.last_activity_date = current, longest, last
    db.flush()
    refresh_local_leaderboard(db, user_id)
    return row


# ── local leaderboard_cache (step 4) ─────────────────────────────────────
def _score(db, model, user_id, cutoff):
    q = select(func.coalesce(func.sum(model.score), 0)).where(
        model.user_id == user_id, model.completed_at.is_not(None), model.score.is_not(None))
    if cutoff is not None:
        q = q.where(model.completed_at >= cutoff)
    return int(db.scalar(q) or 0)


def refresh_local_leaderboard(db, user_id):
    """Update this user's row on every board, then re-rank (ties share a rank).
    fetched_at of existing rows is untouched, so cache staleness still tracks server fetches."""
    from .leaderboard_service import BOARD_PERIODS      # lazy: avoids an import cycle
    user = db.get(m.User, user_id)
    if user is None:
        return
    streak = db.get(m.Streak, user_id)
    badges = int(db.scalar(select(func.count()).select_from(m.UserBadges)
                           .where(m.UserBadges.user_id == user_id)) or 0)
    now = datetime.now(timezone.utc)
    for board, period in BOARD_PERIODS.items():
        cutoff = now - period if period is not None else None
        score = (_score(db, m.QuizAttempt, user_id, cutoff)
                 + _score(db, m.MinigameAttempt, user_id, cutoff))
        row = db.get(m.LeaderboardCache, (board, user_id))
        if row is None:
            if score <= 0:                               # server boards omit zero scores
                continue
            row = m.LeaderboardCache(board_code=board, user_id=user_id, rank_position=0,
                                     display_name="", fetched_at=_EPOCH)
            db.add(row)
        row.display_name = user.display_name or user.username
        row.total_score = score
        row.current_streak = streak.current_streak if streak else 0
        row.badge_count = badges
        db.flush()
        rows = db.scalars(select(m.LeaderboardCache)
                          .where(m.LeaderboardCache.board_code == board)
                          .order_by(m.LeaderboardCache.total_score.desc(),
                                    m.LeaderboardCache.display_name)).all()
        prev, rank = None, 0
        for position, r in enumerate(rows, 1):
            if r.total_score != prev:
                rank, prev = position, r.total_score
            r.rank_position = rank
    db.flush()