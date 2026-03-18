from django import template
from datetime import timedelta

register = template.Library()

@register.simple_tag
def week_check(examiner, day, slot_code):
    """
    Checks if an examiner is booked for a specific day and slot.
    Uses the pre-fetched 'week_bookings' list to avoid extra DB queries.
    """
    if hasattr(examiner, 'week_bookings'):
        for b in examiner.week_bookings:
            # Ensure we compare date objects and slot strings
            if b.date == day and b.slot == slot_code:
                return b
    return None

@register.filter
def get_user_count(examiners, user):
    """Counts how many bookings the current logged-in user has in the current view."""
    count = 0
    for ex in examiners:
        if hasattr(ex, 'week_bookings'):
            count += len([b for b in ex.week_bookings if b.booked_by_id == user.id])
    return count

@register.filter
def get_total_booked(examiners):
    """Counts total occupied slots across all examiners in the view."""
    count = 0
    for ex in examiners:
        if hasattr(ex, 'week_bookings'):
            count += len(ex.week_bookings)
    return count

@register.filter
def add_days(date, days):
    """Adds (or subtracts) a number of days to a date object."""
    try:
        return date + timedelta(days=int(days))
    except (ValueError, TypeError):
        return date