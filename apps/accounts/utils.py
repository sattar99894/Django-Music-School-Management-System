"""
Helpers for the Persian weekly schedule.

Persian weekdays start on Saturday (شنبه). Django/Python's
`date.weekday()` returns Monday=0..Sunday=6, so we remap to a
Saturday-first index (0=شنبه .. 6=جمعه).

Day strings in the database may or may not contain the Zero-Width
Non-Joiner (U+200C) — e.g. "یک‌شنبه" vs "یکشنبه" — so `normalize_day`
maps any variant back to a single canonical form.
"""
from datetime import date
from typing import Dict, List

# Canonical Persian weekday names (Saturday-first), WITH ZWNJ.
PERSIAN_DAYS: List[str] = [
    "شنبه",
    "یک‌شنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنج‌شنبه",
    "جمعه",
]

# ZWNJ-stripped variants, used for fuzzy matching.
_NORM = [d.replace("\u200c", "").replace("\u200d", "") for d in PERSIAN_DAYS]
_NORM_MAP = dict(zip(_NORM, PERSIAN_DAYS))

def persian_weekday_index(d: date | None = None) -> int:
    """Return 0-6 where 0 = شنبه (Saturday)."""
    if d is None:
        d = date.today()
    # Python: Monday=0 .. Sunday=6  ->  remap to Saturday=0
    return (d.weekday() - 5) % 7


def today_persian_day() -> str:
    """Canonical name of today's Persian weekday."""
    return PERSIAN_DAYS[persian_weekday_index()]


def normalize_day(day: str) -> str:
    """Map any ZWNJ variant of a weekday name to its canonical form."""
    if not day:
        return day
    key = day.replace("\u200c", "").replace("\u200d", "").strip()
    return _NORM_MAP.get(key, day)


def build_weekly_schedule(enrollments) -> Dict[str, List[dict]]:
    """
    Build an ordered {day: [items]} structure from a student's enrollments.

    Each item: {"course_title", "teacher_name", "time", "class_id"}.
    Days with no classes yield an empty list (so the template can show "—").
    """
    weekly: Dict[str, List[dict]] = {day: [] for day in PERSIAN_DAYS}

    for enr in enrollments:
        if enr.status != "ENROLLED":
            continue
        cls = enr.class_ref
        schedule = cls.schedule or {}
        teacher_name = ""
        if cls.teacher and cls.teacher.user:
            teacher_name = cls.teacher.user.full_name
        course_title = cls.course.title if cls.course else ""

        for raw_day, time_range in schedule.items():
            day = normalize_day(raw_day)
            if day not in weekly:
                weekly[day] = []
            weekly[day].append({
                "course_title": course_title,
                "teacher_name": teacher_name,
                "time": time_range,
                "class_id": cls.id,
            })

    # Sort each day's classes by start time for a tidy timetable.
    def _time_key(item):
        t = (item.get("time") or "").split("-")[0].strip()
        # Persian digits -> ascii for sorting
        p2a = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
        return t.translate(p2a)

    for day in weekly:
        weekly[day].sort(key=_time_key)
    return weekly
