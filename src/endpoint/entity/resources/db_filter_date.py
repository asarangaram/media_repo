import calendar
from datetime import datetime
import re

from sqlalchemy import extract

from src.endpoint.entity.models import EntityModel

# Date Filter
#   one of the following is possible.
#       Match query: one or more of (YY MM DD HH) in the strict order or None
#       From query: (YY or YYMM or YYMMDD or None) followed by From
#       Till query: (YY or YYMM or YYMMDD or None) followed by Till
#       Range Query: one From Query and one Till Query


def validate_date_keys(field, matching_keys):
    if len(matching_keys) > 2:
        return False
    if len(matching_keys) == 0 or len(matching_keys) == 1:
        return True

    from_key = next((k for k in matching_keys if k.endswith("From")), None)
    till_key = next((k for k in matching_keys if k.endswith("Till")), None)

    if not from_key or not till_key:
        return False

    suffix_from = from_key[len(field) : -4]  # remove field and 'From'
    suffix_till = till_key[len(field) : -4]  # remove field and 'Till'

    if suffix_from != suffix_till:
        return False

    return True


def date_query_filter(
    field,
    dbColumn,
    value: datetime,
    yy: bool = False,
    mm: bool = False,
    dd: bool = False,
    hh: bool = False,
    From: bool = False,
    Till: bool = False,
):
    date_query_filters = []

    if From or Till:
        if yy or mm or dd:
            year = value.year
            month = value.month if mm else 12 if Till else 1
            _, num_days = calendar.monthrange(year, month)
            day = value.day if dd else num_days if Till else 1
            hour = 23 if Till else 0
            minute = 59 if Till else 0
            second = 59 if Till else 0
            microsecond = 999999 if Till else 0

            dt = datetime(
                year, month, day, hour, minute, second, microsecond=microsecond
            )
            pass
        else:
            dt = value

        if From:
            date_query_filters.append(dbColumn >= dt)
        else:
            date_query_filters.append(dbColumn <= dt)

        pass
    else:
        """Match query"""
        if yy or mm or dd or hh:
            if yy:
                date_query_filters.append(
                    extract("year", EntityModel.CreateDate) == value.year
                )
            if mm:
                date_query_filters.append(
                    extract("month", EntityModel.CreateDate) == value.month
                )
            if dd:
                date_query_filters.append(
                    extract("year", EntityModel.CreateDate) == value.day
                )
            if hh:
                date_query_filters.append(
                    extract("hour", EntityModel.CreateDate) == value.hour
                )
        else:
            if isinstance(value, list):
                date_query_filters.append(dbColumn.in_(value))
            elif value == "__null__":
                date_query_filters.append(dbColumn.is_(None))
            elif value == "__notnull__":
                date_query_filters.append(dbColumn.is_not(None))
            else:
                date_query_filters.append(dbColumn == value)

    return date_query_filters


def date_query_filters(date_fields, kwargs):
    rangePattern = re.compile(r"^(YY(MM(DD)?)?)?(From|Till)$")
    datePattern = re.compile(r"^(YY)?(MM)?(DD)?(HH)?$")

    date_query_filters = []
    for field, column in date_fields.items():
        # There could be upto two fields,
        matching_map = {
            key: value for key, value in kwargs.items() if key.startswith(field)
        }
        matching_keys = matching_map.keys()
        if not validate_date_keys(field, matching_keys):
            raise Exception(f"Invalid Date Search: {matching_keys} ")
        for key in matching_keys:
            prefix_len = len(field)
            suffix = key[prefix_len:]
            if not suffix:
                date_query_filters.extend(
                    date_query_filter(field, column, matching_map[key])
                )
                continue
            m1 = datePattern.fullmatch(suffix)
            if m1:
                YY, MM, DD, HH = m1.groups()
                args = dict(
                    yy=YY is not None,
                    mm=MM is not None,
                    dd=DD is not None,
                    hh=HH is not None,
                )
                date_query_filters.extend(
                    date_query_filter(field, column, matching_map[key], **args)
                )
                continue
            m2 = rangePattern.fullmatch(suffix)
            if m2:
                whole_suffix, MM, DD, HH, from_till = m1.groups()
                args = dict(
                    yy=1 if whole_suffix and whole_suffix.startswith("YY") else None,
                    mm=1 if MM else None,
                    dd=1 if DD else None,
                    hh=1 if HH else None,
                    From=(from_till == "From"),
                    Till=(from_till == "Till"),
                )
                date_query_filters.extend(
                    date_query_filter(field, column, matching_map[key], **args)
                )
                continue
            raise Exception("Invalid dateField")
    return date_query_filters
