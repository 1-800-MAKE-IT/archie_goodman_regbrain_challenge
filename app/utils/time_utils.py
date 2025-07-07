from datetime import datetime, timedelta

#file created by Gemini
def ten_day_bucket(dt: datetime) -> str:
    """Return a 10-day bucket string 'YYYY-MM-DD' for any date.
    The bucket start date is calculated by finding the date that is a multiple of 10 days away from the start of the year.
    """
    days_since_year_start = (dt - datetime(dt.year, 1, 1)).days
    bucket_start_date = dt - timedelta(days=days_since_year_start % 10)
    return bucket_start_date.strftime("%Y-%m-%d")