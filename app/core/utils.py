import sqlalchemy
from math import floor, ceil
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import re

def to_dict(model_instance):
    return {
        c.key: getattr(model_instance, c.key)
        for c in sqlalchemy.inspect(model_instance).mapper.column_attrs
    }


def get_date_without_tz():
    return datetime.now(timezone.utc).replace(tzinfo=None)
