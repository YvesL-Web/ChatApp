from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from datetime import datetime

def calculate_timestamp(timestamp):
    """
    1. Today or yesterday
        ex: today at 11:53 AM
        ex: yesterday at 05:12 PM
    2. other:
        ex: 21/05/2023
    """
    # 1.
    if (naturalday(timestamp) == "today" or (naturalday(timestamp) == "yesterday")):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    # 2.
    else:
        str_time = datetime.strftime(timestamp,"%d.%m.%Y")
        ts = f"{str_time}"

    return ts
