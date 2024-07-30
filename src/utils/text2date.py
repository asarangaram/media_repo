from dateutil import tz
import datetime
import pytz

import re

pattern = r'^\b(.{4})[:-](.{2})[:-](.{2})\s+(.{2}):(.{2}):(.{2})(Z|([+-])(.{2}):(.{2}))?.*\b$'


class Text2Time:
    def __init__(self, text):
        match = re.search(pattern, text)
        if match:
            groups = match.groups()

            year = int(groups[0].strip())
            month = int(groups[1].strip())
            day = int(groups[2].strip())
            hour = int(groups[3].strip())
            minute = int(groups[4].strip())
            second = int(groups[5].strip())
            if groups[6]:
                if groups[6].strip() == 'Z':
                    timezone_value = 0
                else:
                    timezone_sign = -1 if (groups[7].strip() == '-') else 1
                    timezone_hours = int(groups[8].strip())
                    timezone_minutes = int(groups[9].strip())
                    timezone_value = timezone_sign * (timezone_hours * 60 + timezone_minutes)
            else:
                timezone_value = None
            self.dateTime = Text2Time.create_custom_datetime(
                year, month, day, hour, minute, second, timezone_value)

    @classmethod
    def create_custom_datetime(cls, year, month, day, hour, minute, second, timezone_value=None):
        if timezone_value is None:
            tz_info = tz.tzlocal()
        elif timezone_value == 'Z':
            tz_info = pytz.utc
        else:
            tz_info = tz.tzoffset(None, timezone_value * 60)

        try:
            dt = datetime.datetime(year, month, day, hour, minute, second, tzinfo=tz_info)
            return dt.astimezone(tz.tzlocal())
        except ValueError as e:
            # print(f"Error creating datetime: {e}")
            return None


if __name__ == '__main__':
    time_values = [
        "2014:05:06 14:55:08+05:30",
        "2014:05:06 14:55:08Z",
        "2014:05:06 14:55:08",
        "2014:05:06 14:55: 8",
        "2014:05:06 14: 5: 8"
    ]

    for value in time_values:
        print(f"{value} ==> {Text2Time(value).dateTime}")
