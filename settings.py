MESSAGE_CATEGORY: str = "ANYWAYS"
EDIT_API = "https://api.anyways.eu/edit/"
API = "https://api.anyways.eu/impact/canary/"

OIDC_AUTHORITY = "https://www.anyways.eu/account"
OIDC_CLIENT_ID = "qgis-plugin"
OIDC_SCOPES = "openid profile impact"

PROFILE_COLOURS = {
    "bicycle": "#2222cc",
    "pedestrian": "#22cc22",
    "car": "#bb2222",
    "bigtruck": "#333333",
    "FAILED": "#ff0000"
}

PROFILE_OFFSET = {
    "bicycle": 2,
    "pedestrian": 3,
    "car": 1,
    "bigtruck": 1,
    "FAILED": 0
}
