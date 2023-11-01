import enum


class RelatedObjectType(enum.Enum):
    CHANGE_REQUEST = "Change request"
    EDGE_IDENTITY = "Edge identity"
    ENVIRONMENT = "Environment"
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    GRANT = "Grant"
    GROUP = "Group"
    IMPORT_REQUEST = "Import request"
    PROJECT = "Project"
    ROLE = "Role"
    SEGMENT = "Segment"
    USER = "User"
    USER_MFA_METHOD = "User MFA method"
