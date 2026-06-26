"""Constants for the Tracksolid Pro integration."""

DOMAIN = "tracksolid"

# Config entry keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_IMEIS = "imeis"

# API base URL (the web app's own backend — no appKey/appSecret needed)
API_BASE_URL = "https://www.tracksolidpro.com"

# API endpoints
ENDPOINT_LOGIN = "/v3/new/homepage/login"
ENDPOINT_GET_GROUPS = "/v3/new/newDevice/getUserGroup"
ENDPOINT_GET_DEVICES = "/v3/new/newEquipment/queryEquipmentList"
ENDPOINT_GET_CURRENT_USER = "/v3/new/account/current"
ENDPOINT_GET_NODE_LIST = "/v3/new/newDevice/getNodeList"

DEFAULT_SCAN_INTERVAL = 30  # seconds

# Token assumed valid for 23 h; re-auth proactively before server expires it
TOKEN_TTL = 23 * 3600

# Webhook
WEBHOOK_ID = "tracksolid_push"

# Coordinator keys
COORDINATOR = "coordinator"

# Device status values returned by the API
STATUS_MOVING = "MOVE"
STATUS_STATIC = "STATIC"
STATUS_OFFLINE = "OFFLINE"

# Alarm type codes (used in webhook push payloads)
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
