import calendar
from datetime import datetime

from sqlalchemy import extract
from src.endpoint.entity.models import EntityModel
from src.utils.custom_errors.validation_errors import NonZeroUIntSearchFieldError


from clmediakit import fromTimeStamp


import re


class DateTimeQuerySchema:
    allowed_date_fields = {
        "addedDate": EntityModel.addedDate,
        "updatedDate": EntityModel.updatedDate,
        "CreateDate": EntityModel.CreateDate,
    }
    rangePattern = re.compile(r"^(YY(MM(DD)?)?)?(From|Till)$")
    datePattern = re.compile(r"^(YY)?(MM)?(DD)?(HH)?$")

    def __init__(self, date_field, **kwargs):
        self.date_field = date_field
        self.matching_map = {
            key: value for key, value in kwargs.items() if key.startswith(date_field)
        }

    @staticmethod
    def validate(field, matching_keys):
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

    def translate(self):
        if hasattr(self, "translatedMap"):
            return

        matching_keys = self.matching_map.keys()
        if not self.validate(self.date_field, matching_keys):
            raise Exception("Validation Failed")

        translatedMap = {}
        for key in self.matching_map.keys():
            prefix_len = len(self.date_field)
            suffix = key[prefix_len:]
            if not suffix:
                translatedMap[key] = self.translate_to_dt(
                    self.matching_map[key], key, nulSupported=True
                )
                continue
            m1 = self.datePattern.fullmatch(suffix)
            if m1:
                translatedMap[key] = self.translate_to_dt(
                    self.matching_map[key], key, nulSupported=False
                )
                continue
            m2 = self.rangePattern.fullmatch(suffix)
            if m2:
                translatedMap[key] = self.translate_to_dt(
                    self.matching_map[key], key, nulSupported=False
                )
                continue
            raise Exception(f"Invalid argument {key}={self.matching_map[key]}")
        self.translatedMap = translatedMap
        return self.translatedMap

    def translate_to_dt(self, value, attr, nulSupported: bool):
        if isinstance(value, list):
            if len(value) == 1:
                if value[0] in ("__null__", "__notnull__"):
                    if nulSupported:
                        return value[0]
                    else:
                        raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
                return self.translate_value(value[0], value, attr)

            return [self.translate_value(v, value, attr) for v in value]
        if value in ("__null__", "__notnull__"):
            if nulSupported:
                return value
            else:
                raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code

        return self.translate_value(value, value, attr)

    def translate_value(self, v, value, attr):
        try:
            if isinstance(v, str) or isinstance(v, float):
                dt = fromTimeStamp(int(v))
            elif isinstance(v, int):
                dt = fromTimeStamp(v)
            else:
                raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
        except (ValueError, TypeError):
            raise NonZeroUIntSearchFieldError(attr, value)  # FIX Error code
        return dt

    def query(
        self,
        value: datetime,
        yy: bool = False,
        mm: bool = False,
        dd: bool = False,
        hh: bool = False,
        From: bool = False,
        Till: bool = False,
    ):
        dbColumn = self.allowed_date_fields[self.date_field]
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
                    date_query_filters.append(extract("year", dbColumn) == value.year)
                if mm:
                    date_query_filters.append(extract("month", dbColumn) == value.month)
                if dd:
                    date_query_filters.append(extract("day", dbColumn) == value.day)
                if hh:
                    date_query_filters.append(extract("hour", dbColumn) == value.hour)
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

    @property
    def queries(self):
        self.translate()
        date_query_filters = []
        for key, value in self.translatedMap.items():
            prefix_len = len(self.date_field)
            suffix = key[prefix_len:]
            if not suffix:
                date_query_filters.extend(self.query(value))
                continue
            m1 = self.datePattern.fullmatch(suffix)
            if m1:
                YY, MM, DD, HH = m1.groups()
                args = dict(
                    yy=YY is not None,
                    mm=MM is not None,
                    dd=DD is not None,
                    hh=HH is not None,
                )
                date_query_filters.extend(self.query(value, **args))
                continue
            m2 = self.rangePattern.fullmatch(suffix)
            if m2:
                whole_suffix, MM, DD, from_till = m2.groups()
                args = dict(
                    yy=1 if whole_suffix and whole_suffix.startswith("YY") else None,
                    mm=1 if MM else None,
                    dd=1 if DD else None,
                    From=(from_till == "From"),
                    Till=(from_till == "Till"),
                )
                date_query_filters.extend(self.query(value, **args))
                continue
            raise Exception("Invalid dateField")

        return date_query_filters
        pass
