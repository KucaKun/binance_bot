from pytrends.request import TrendReq
from datetime import datetime, timedelta
pytrends = TrendReq(hl='en-US', tz=360)

def getHistoricalInterest(keywords, hours):
    today = datetime.today()
    hoursAgo = today - timedelta(hours=hours)
    return pytrends.get_historical_interest(
        keywords, year_start=hoursAgo.year, month_start=hoursAgo.month, day_start=hoursAgo.day, hour_start=hoursAgo.hour,
        year_end=today.year, month_end=today.month, day_end=today.day, hour_end=today.hour, cat=0, geo='', gprop='', sleep=0
    )