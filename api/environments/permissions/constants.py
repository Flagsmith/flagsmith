# Maintain a list of permissions here
VIEW_ENVIRONMENT = "VIEW_ENVIRONMENT"
UPDATE_FEATURE_STATE = "UPDATE_FEATURE_STATE"
MANAGE_IDENTITIES = "MANAGE_IDENTITIES"
CREATE_CHANGE_REQUEST = "CREATE_CHANGE_REQUEST"
APPROVE_CHANGE_REQUEST = "APPROVE_CHANGE_REQUEST"

ENVIRONMENT_PERMISSIONS = [
    (VIEW_ENVIRONMENT, "View permission for the given environment."),
    (UPDATE_FEATURE_STATE, "Update the state or value for a given feature state."),
    (MANAGE_IDENTITIES, "Manage identities in the given environment."),
    (
        CREATE_CHANGE_REQUEST,
        "Permission to create change requests in the given environment.",
    ),
    (
        APPROVE_CHANGE_REQUEST,
        "Permission to approve change requests in the given environment.",
    ),
]
