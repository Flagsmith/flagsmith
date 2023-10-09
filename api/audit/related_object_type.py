import enum


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    ENVIRONMENT = "Environment"
    CHANGE_REQUEST = "Change request"
    EDGE_IDENTITY = "Edge Identity"
    IMPORT_REQUEST = "Import request"
