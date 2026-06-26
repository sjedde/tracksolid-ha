# Tracksolid Pro — Home Assistant Integration

Track your motorbike (or any Tracksolid Pro asset) in Home Assistant.

## Features

| Entity | Type | Description |
|--------|------|-------------|
| `device_tracker.<name>` | Device Tracker | Live GPS location on the map |
| `sensor.<name>_speed` | Sensor | Current speed (km/h) |
| `sensor.<name>_battery` | Sensor | Battery level (%) |
| `sensor.<name>_satellites` | Sensor | GPS satellite count |
| `sensor.<name>_signal` | Sensor | GSM signal strength (%) |
| `sensor.<name>_last_update` | Sensor | Timestamp of last GPS fix |
| `binary_sensor.<name>_vibration` | Binary Sensor | Vibration/shock detected |
| `binary_sensor.<name>_ignition` | Binary Sensor | Ignition on/off |
| `binary_sensor.<name>_moving` | Binary Sensor | Device is moving |

### Events

| Event | Fired when |
|-------|-----------|
| `tracksolid_alarm` | Any alarm push received from Tracksolid |
| `tracksolid_vibration` | Vibration/shock alarm specifically |

## Requirements

- A **Tracksolid Pro** account (the same login you use in the Tracksolid Pro app)
- Home Assistant 2023.9+
- No API key registration needed

## Installation

### HACS (recommended)

1. Add this repo as a custom repository in HACS: `Settings → Custom repositories`
2. Install **Tracksolid Pro**
3. Restart Home Assistant

### Manual

1. Copy the `custom_components/tracksolid` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Tracksolid Pro**
3. Enter your **email address** and **password** (same as the Tracksolid Pro app)
4. Choose your **server region** (if unsure, try Europe)
5. Select which devices you want to track
6. Set the polling interval (default: 30 s)

> **How authentication works:** The integration uses the platform credentials published in the
> Tracksolid Pro API documentation. Users only need their own account email and password —
> no separate developer key registration is required.

## Push Notifications (Vibration Alerts)

Tracksolid can **push** alarm events to your Home Assistant via webhook. This enables instant vibration alerts rather than waiting for the next poll cycle.

### Webhook URL

After setup, a webhook is registered at:

```
https://<your-ha-url>/api/webhook/tracksolid_push_<entry_id>
```

You can find the exact URL in **Settings → Devices & Services → Tracksolid Pro → Configure**.

### Configuring the push URL in Tracksolid

1. Log in to the Tracksolid Pro API portal or contact support to enable push callbacks.
2. Set the callback URL to your HA webhook URL above.
3. Tracksolid will POST JSON alarm events to that URL.

> **Note:** Your Home Assistant must be reachable from the internet (e.g., via Nabu Casa / Home Assistant Cloud, or port forwarding). If you use Nabu Casa, your external URL will be `https://<id>.ui.nabu.casa`.

### Automating vibration alerts

Example automation in `automations.yaml`:

```yaml
alias: "Motorbike vibration alert"
trigger:
  - platform: event
    event_type: tracksolid_vibration
condition: []
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Motorbike alert!"
      message: >
        Vibration detected at
        {{ trigger.event.data.latitude }},
        {{ trigger.event.data.longitude }}
      data:
        url: >
          https://maps.google.com/?q=
          {{ trigger.event.data.latitude }},
          {{ trigger.event.data.longitude }}
mode: single
```

Or using the binary sensor:

```yaml
alias: "Motorbike vibration alert"
trigger:
  - platform: state
    entity_id: binary_sensor.my_motorbike_vibration
    to: "on"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Motorbike vibration!"
      message: "Someone may be tampering with your bike."
```

## Alarm type reference

| Code | Name |
|------|------|
| 1 | SOS |
| 2 | Power Off |
| 3 | Low Battery |
| 4 | Geofence Enter |
| 5 | Geofence Exit |
| 6 | Speeding |
| 9 | Vibration |
| 20 | Ignition On |
| 21 | Ignition Off |

## Troubleshooting

- **"cannot_connect"** — verify the region matches your Tracksolid account's server.
- **"invalid_auth"** — double-check your email and password.
- **No location updates** — ensure the device has GPS coverage and the IMEI is correct.
- **Webhook not receiving pushes** — confirm your HA instance is externally reachable and the push URL is configured correctly in the Tracksolid portal.
