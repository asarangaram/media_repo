import calendar
import re
from datetime import datetime

from marshmallow import ValidationError
from sqlalchemy import extract

from src.endpoint.entity.resources.search_schema.param import Param
from src.utils.custom_errors.internal_server_errors import (
    DataNotLoadedError,
    UnexpectedFailure,
)


class DateTimeParam(Param):
    def __init__(
        self,
        field_name: str,
        dbColumn,
        data,
        no_variant: bool = False,
        is_null_supported: bool = True,
    ):
        super().__init__(
            field_name,
            dbColumn,
            data,
            no_variant=no_variant,
            is_null_supported=is_null_supported,
        )
        self.patterns = [
            re.compile(r"^(YY(MM(DD)?)?)?(From|Till)$"),
            re.compile(r"^(YY)?(MM)?(DD)?(HH)?$"),
        ]

    def load(self):
        return super().load(lambda key, value: self.to_datetime(key, value))

    def validate(self):
        if not super().validate():
            return False

        if len(self.raw_fields.keys()) > (1 if self.no_variant else 2):
            return self.TooManyParametersUsed()

        if len(self.raw_fields.keys()) == 2:
            from_key = next(
                (k for k in self.raw_fields.keys() if k.endswith("From")),
                None,
            )
            till_key = next(
                (k for k in self.raw_fields.keys() if k.endswith("Till")),
                None,
            )

            if not from_key or not till_key:
                return self.conflictingParametersUsed()

            if from_key[:-4] != till_key[:-4]:
                return self.mismatchInMasks()

        return True

    def mismatchInMasks(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "parameters are conflicting. "
                "masks are not matching between From and Till"
            }
        )

    def conflictingParametersUsed(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "parameters are conflicting. "
                "use either a matching query or a range query with From and "
                "Till when using range query, masks"
            }
        )

    def TooManyParametersUsed(self):
        raise ValidationError(
            {
                f"{self.raw_fields.keys()}": "Too many parameters used. "
                "use either a matching query or a range query with From and "
                "Till"
            }
        )

    def _valid(self):
        match len(self.raw_fields):
            case 0:
                return True
            case 1:
                return True
            case 2:
                from_key = next(
                    (k for k in self.raw_fields if k.endswith("From")), None
                )
                till_key = next(
                    (k for k in self.raw_fields if k.endswith("Till")), None
                )
                if from_key and till_key:
                    suffix_from = from_key[len(self.field_name) : -4]
                    suffix_till = till_key[len(self.field_name) : -4]
                    return suffix_from == suffix_till
                return False
            case _:
                return False

    def datetime_query(
        self,
        value: datetime,
        yy: bool = False,
        mm: bool = False,
        dd: bool = False,
        hh: bool = False,
        From: bool = False,
        Till: bool = False,
    ):
        dbColumn = self.dbColumn

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
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    microsecond=microsecond,
                )
                pass
            else:
                dt = value

            if From:
                filter = dbColumn >= dt
            else:
                filter = dbColumn <= dt

            pass
        else:
            """Match query"""
            if yy or mm or dd or hh:
                if yy:
                    filter = extract("year", dbColumn) == value.year
                if mm:
                    filter = extract("month", dbColumn) == value.month
                if dd:
                    filter = extract("day", dbColumn) == value.day
                if hh:
                    filter = extract("hour", dbColumn) == value.hour
            else:
                if isinstance(value, list):
                    filter = dbColumn.in_(value)
                elif value == "__null__":
                    filter = dbColumn.is_(None)
                elif value == "__notnull__":
                    filter = dbColumn.is_not(None)
                else:
                    filter = dbColumn == value

        return filter

    @property
    def queries(self):
        if not hasattr(self, "fields"):
            raise DataNotLoadedError("data is not loaded for {self.field_name}")

        date_query_filters = []
        if len(self.fields) > 0:
            for key, value in self.fields.items():
                prefix_len = len(self.field_name)
                suffix = key[prefix_len:]
                if not suffix:
                    date_query_filters.append(self.datetime_query(value))
                    continue
                if not self.no_variant:
                    m1 = self.patterns[0].fullmatch(suffix)
                    if m1:
                        whole_suffix, MM, DD, from_till = m1.groups()
                        args = dict(
                            yy=(
                                1
                                if whole_suffix and whole_suffix.startswith("YY")
                                else None
                            ),
                            mm=1 if MM else None,
                            dd=1 if DD else None,
                            From=(from_till == "From"),
                            Till=(from_till == "Till"),
                        )
                        date_query_filters.append(self.datetime_query(value, **args))
                        continue

                    m2 = self.patterns[1].fullmatch(suffix)
                    if m2:
                        YY, MM, DD, HH = m2.groups()
                        args = dict(
                            yy=YY is not None,
                            mm=MM is not None,
                            dd=DD is not None,
                            hh=HH is not None,
                        )
                        date_query_filters.append(self.datetime_query(value, **args))
                        continue

                raise UnexpectedFailure()

        return date_query_filters
