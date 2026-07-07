"""Template filters for Persian (Jalali) dates."""
from datetime import date, datetime

import jdatetime
from django import template

register = template.Library()


@register.filter
def jdate(value, fmt="%d %B %Y"):
    """Format a date/datetime as a Persian (Jalali) string.

    Examples:
        {{ obj.created_at|jdate }}               -> ۱۲ مهر ۱۴۰۳
        {{ obj.created_at|jdate:"%H:%M - %d %B" }} -> ۱۶:۳۲ - ۱۲ مهر
    """
    if not value:
        return ""
    try:
        if isinstance(value, datetime):
            jd = jdatetime.datetime.fromgregorian(datetime=value)
        elif isinstance(value, date):
            jd = jdatetime.date.fromgregorian(date=value)
        else:
            return str(value)
        return jd.strftime(fmt)
    except Exception:
        return str(value)


@register.simple_tag
def jnow(fmt="%d %B %Y"):
    """Current date/time in Persian (Jalali)."""
    return jdatetime.datetime.now().strftime(fmt)


@register.filter
def fa_intcomma(value):
    """Format an integer with Persian thousands separators.

    Example: 3200000 -> "۳,۲۰۰,۰۰۰"
    Independent of Django's i18n/localization settings.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        return value
    # group with ASCII commas, then convert digits to Persian.
    grouped = f"{n:,}"
    persian = grouped.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    return persian
