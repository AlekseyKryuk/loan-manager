from decimal import Decimal


def orjson_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)
