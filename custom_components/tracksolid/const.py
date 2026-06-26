"""Constants for the Tracksolid Pro integration."""

DOMAIN = "tracksolid"

# Config entry keys
CONF_APP_KEY = "app_key"
CONF_APP_SECRET = "app_secret"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_REGION = "region"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IMEIS = "imeis"

# Regions / base URLs
REGION_HK_SG = "hk_sg"
REGION_EU = "eu"
REGION_US = "us"

REGION_URLS = {
    REGION_HK_SG: "https://hk-open.tracksolidpro.com/route/rest",
    REGION_EU: "https://eu-open.tracksolidpro.com/route/rest",
    REGION_US: "https://us-open.tracksolidpro.com/route/rest",
}

REGION_LABELS = {
    REGION_HK_SG: "Asia / HK / SG",
    REGION_EU: "Europe",
    REGION_US: "United States",
}

DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_REGION = REGION_EU

# Platform credentials published in the official Tracksolid Pro API documentation.
# These are shared credentials for all users — no developer registration is required.
# Users authenticate with their own Tracksolid username and password.
PLATFORM_APP_KEY = "8FB345B8693CCD00CE073CAB5F094009339A22A4105B6558"
PLATFORM_APP_SECRET = "c0aa0226fddc4365a3c67fef45427f8a"

# API version 1.0 requires MD5 signature; used for all requests.
API_VERSION = "1.0"

# API methods
METHOD_TOKEN_GET = "jimi.oauth.token.get"
METHOD_TOKEN_REFRESH = "jimi.oauth.token.refresh"
METHOD_DEVICE_LIST = "jimi.user.device.list"
METHOD_DEVICE_LOCATION = "jimi.device.location.get"
METHOD_DEVICE_DETAIL = "jimi.track.device.detail"

# Token TTL (refresh at ~6000 s to stay ahead of the 7200 s expiry)
TOKEN_REFRESH_THRESHOLD = 6000

# Webhook
WEBHOOK_ID = "tracksolid_push"

# Coordinator keys
COORDINATOR = "coordinator"
DEVICES = "devices"

# Alarm type codes
ALARM_TYPE_VIBRATION = 9
ALARM_TYPE_SOS = 1
ALARM_TYPE_POWER_OFF = 2
ALARM_TYPE_LOW_BATTERY = 3
ALARM_TYPE_GEOFENCE_ENTER = 4
ALARM_TYPE_GEOFENCE_EXIT = 5
ALARM_TYPE_SPEEDING = 6
ALARM_TYPE_IGNITION_ON = 20
ALARM_TYPE_IGNITION_OFF = 21

ALARM_TYPE_NAMES = {
    ALARM_TYPE_SOS: "SOS",
    ALARM_TYPE_POWER_OFF: "Power Off",
    ALARM_TYPE_LOW_BATTERY: "Low Battery",
    ALARM_TYPE_GEOFENCE_ENTER: "Geofence Enter",
    ALARM_TYPE_GEOFENCE_EXIT: "Geofence Exit",
    ALARM_TYPE_SPEEDING: "Speeding",
    ALARM_TYPE_VIBRATION: "Vibration",
    ALARM_TYPE_IGNITION_ON: "Ignition On",
    ALARM_TYPE_IGNITION_OFF: "Ignition Off",
}
