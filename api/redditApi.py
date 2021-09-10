import praw, math
from datetime import datetime, date, timedelta
reddit = praw.Reddit(
    client_id="7Yw6WhBpterynw",
    client_secret="XPQZtFRUuunSlTdvDCwA1wDa7PyvNg",
    user_agent="scraper by u/NiquS7",
)

"""
interval - hour, day, week
"""
nextIntervalTable = {
    "hour":("day",24),
    "day":("week",7),
    "week":("month",4),
}
def getPopularity(subreddit,interval):
    submissions = reddit.subreddit(subreddit).top(time_filter=interval)
    submissionsBack = reddit.subreddit(subreddit).top(time_filter=nextIntervalTable[interval][0])
    commentsMultiplier = 10
    value = 0
    for submission in submissions:
        value += submission.score + (submission.num_comments * commentsMultiplier)

    averageValue = 0
    for submission in submissionsBack:
        averageValue += submission.score + (submission.num_comments * commentsMultiplier)
    averageValue /= nextIntervalTable[interval][1]

    subscribersPenality = reddit.subreddit(subreddit).subscribers
    return ((value/averageValue)/subscribersPenality)*10**8

print(getPopularity("Bitcoin","hour"))
print(getPopularity("ethereum","hour"))