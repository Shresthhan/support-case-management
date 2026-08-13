from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Return the current UTC time without timezone information.

    The current database columns use DateTime without timezone=True.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)