


from src.endpoint.entity.models import EntityModel
from src.endpoint.entity.resources.db_filter_date import date_query_filters

def dbFilter(kwargs):
    query_filters = []

    # --- Helper function for string-based filters ---
    def _apply_string_filter(column, value, match_type="exact"):
        """
        Applies filtering logic for string fields based on match_type.
        'exact': column == value
        'ilike_partial': column.ilike(f"%{value}%")
        'ilike_starts_with': column.ilike(f"{value}%")
        Handles list of values, __null__, and __notnull__.
        """
        if isinstance(value, list):
            return column.in_(value)
        elif value == "__null__":
            return column.is_(None)
        elif value == "__notnull__":
            return column.is_not(None)
        else:
            if match_type == "ilike_partial":
                return column.ilike(f"%{value}%")
            elif match_type == "ilike_starts_with":
                return column.ilike(f"{value}%")
            else: # default to exact
                return column == value

    # --- Helper function for numeric (uint) filters ---
    def _apply_numeric_filter(column, value):
        """
        Applies filtering logic for numeric fields.
        Handles list of values, __null__, and __notnull__.
        """
        if isinstance(value, list):
            return column.in_(value)
        elif value == "__null__":
            return column.is_(None)
        elif value == "__notnull__":
            return column.is_not(None)
        else:
            return column == value

    # --- Boolean flags ---
    if 'isCollection' in kwargs:
        query_filters.append(EntityModel.isCollection == bool(kwargs['isCollection']))
    if 'isDeleted' in kwargs:
        query_filters.append(EntityModel.isDeleted == bool(kwargs['isDeleted']))

    # --- String Search Fields (Looped) ---
    string_search_field_map = {
        'label': {'column': EntityModel.label, 'match_type': 'exact'},
        'md5': {'column': EntityModel.md5, 'match_type': 'exact'},
        'MIMEType': {'column': EntityModel.MIMEType, 'match_type': 'exact'},
        'extension': {'column': EntityModel.extension, 'match_type': 'exact'},
        'label_starts_with': {'column': EntityModel.label, 'match_type': 'ilike_starts_with'},
        'label_contains': {'column': EntityModel.label, 'match_type': 'ilike_partial'},
        'description_contains': {'column': EntityModel.description, 'match_type':"ilike_partial"}
    }

    for field_name, config in string_search_field_map.items():
        if field_name in kwargs:
            query_filters.append(_apply_string_filter(
                config['column'], kwargs[field_name], match_type=config['match_type']
            ))


    # --- Non-zero UInt or List of Non-Zero UInt Fields (Looped) ---
    numeric_search_field_map = {
        'id': EntityModel.id,
        'parentId': EntityModel.parentId,
        'ImageHeight': EntityModel.ImageHeight,
        'ImageWidth': EntityModel.ImageWidth,
        'Duration': EntityModel.Duration,
    }

    for field_name, column in numeric_search_field_map.items():
        if field_name in kwargs:
            query_filters.append(_apply_numeric_filter(column, kwargs[field_name]))

    # --- FileSize range filters ---
    if 'FileSizeMin' in kwargs:
        query_filters.append(EntityModel.FileSize >= kwargs['FileSizeMin'])
    if 'FileSizeMax' in kwargs:
        query_filters.append(EntityModel.FileSize <= kwargs['FileSizeMax'])

    # --- Date range filters ---
    date_fields = {
        'addedDate': EntityModel.addedDate,
        'updatedDate': EntityModel.updatedDate,
        'CreateDate': EntityModel.CreateDate
    }
    query_filters.extend(date_fields, date_query_filters(kwargs))

    # --- Duration range filters ---
    if 'duration_min' in kwargs:
        query_filters.append(EntityModel.Duration >= kwargs['duration_min'])
    if 'duration_max' in kwargs:
        query_filters.append(EntityModel.Duration <= kwargs['duration_max'])

    return query_filters