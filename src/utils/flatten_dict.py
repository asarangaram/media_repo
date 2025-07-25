from datetime import datetime
from clmediakit import toTimeStamp

def flatten_dict(data_map):
    try:
        for key in list(data_map.keys()):
            value = data_map[key]

            if isinstance(value, dict):  # recursive
                data_map[key] = flatten_dict(value)
            elif isinstance(value, list):
                if len(value) == 1:
                    data_map[key] = value[0]
                elif len(value) == 0:
                    del data_map[key]
            if value is None:
                del data_map[key]

        return data_map
    except Exception:
        raise


def convert_bools_to_int_recursive(data):
    if isinstance(data, bool):
        return int(data)
    elif isinstance(data, dict):
        return {k: convert_bools_to_int_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_bools_to_int_recursive(item) for item in data]
    elif isinstance(data, datetime):
        return int(toTimeStamp(data))

    else:
        return data
