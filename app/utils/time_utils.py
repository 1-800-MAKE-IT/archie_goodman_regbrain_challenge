from datetime import datetime, timedelta

#file created by chatgpt
def week_bucket(dt: datetime) -> str:
    """Return Monday-start bucket string 'YYYY-MM-DD' for any date."""
    monday = dt - timedelta(days=dt.weekday())  # weekday(): Monday=0
    return monday.strftime("%Y-%m-%d")