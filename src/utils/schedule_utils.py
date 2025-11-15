"""Schedule and business hours utilities."""
from datetime import datetime, time
from typing import List, Optional

import pytz


class ScheduleChecker:
    """Check if current time falls within configured schedules."""

    def __init__(
        self,
        start_time: str = "08:00",
        end_time: str = "18:00",
        active_days: List[int] = None,
        timezone: str = "America/New_York",
    ):
        """
        Initialize schedule checker.

        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            active_days: List of active weekdays (1=Monday, 7=Sunday)
            timezone: Timezone name (e.g., 'America/New_York')
        """
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.active_days = active_days or [1, 2, 3, 4, 5]  # Mon-Fri default
        self.timezone = pytz.timezone(timezone)

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse time string in HH:MM format."""
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)

    def is_within_schedule(self, dt: Optional[datetime] = None) -> bool:
        """
        Check if given datetime is within the schedule.

        Args:
            dt: Datetime to check. If None, uses current time.

        Returns:
            True if within schedule, False otherwise.
        """
        if dt is None:
            dt = datetime.utcnow()

        # Convert to configured timezone
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        local_dt = dt.astimezone(self.timezone)

        # Check day of week (Monday=1, Sunday=7)
        weekday = local_dt.isoweekday()
        if weekday not in self.active_days:
            return False

        # Check time range
        current_time = local_dt.time()
        if self.start_time <= self.end_time:
            # Normal range (e.g., 08:00 to 18:00)
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight range (e.g., 22:00 to 06:00)
            return current_time >= self.start_time or current_time <= self.end_time


def parse_days_string(days_str: str) -> List[int]:
    """
    Parse comma-separated days string into list of integers.

    Args:
        days_str: Comma-separated days (e.g., "1,2,3,4,5")

    Returns:
        List of day numbers

    Example:
        >>> parse_days_string("1,2,3,4,5")
        [1, 2, 3, 4, 5]
    """
    return [int(d.strip()) for d in days_str.split(",") if d.strip()]


def create_schedule_checker_from_env() -> ScheduleChecker:
    """
    Create ScheduleChecker from environment variables.

    Uses settings from src.config.
    """
    from src.config import get_settings

    settings = get_settings()

    return ScheduleChecker(
        start_time=settings.business_hours_start,
        end_time=settings.business_hours_end,
        active_days=parse_days_string(settings.business_hours_days),
        timezone=settings.business_hours_timezone,
    )


def should_monitor_host(
    host_schedule_type: str,
    custom_schedule_config: Optional[str] = None,
    current_time: Optional[datetime] = None,
) -> bool:
    """
    Determine if a host should be monitored at the current time.

    Args:
        host_schedule_type: Type of schedule ('always', 'business_hours', 'custom')
        custom_schedule_config: JSON config for custom schedules
        current_time: Time to check. If None, uses current time.

    Returns:
        True if host should be monitored, False otherwise.
    """
    if host_schedule_type == "always":
        return True

    if host_schedule_type == "business_hours":
        checker = create_schedule_checker_from_env()
        return checker.is_within_schedule(current_time)

    if host_schedule_type == "custom":
        # TODO: Implement custom schedule logic
        # For now, treat as 'always'
        return True

    # Unknown schedule type, default to always monitor
    return True
