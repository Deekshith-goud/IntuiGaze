# EyeNav API Reference

**Version:** 0.1.0-alpha  
**Base URL:** `http://localhost:8765/api/v1`  
**Protocol:** HTTP/1.1 + WebSocket  
**Authentication:** JWT (for multi-user server mode)  

---

## Overview

EyeNav provides two API surfaces:

1. **REST API** — for configuration, session management, and query
2. **WebSocket API** — for real-time streaming of gaze data, features, and commands

All responses are JSON. All timestamps are Unix epoch with millisecond precision.

---

## Authentication

In **local single-user mode**, no authentication is required.

In **server mode**, all endpoints require a Bearer token:

```http
Authorization: Bearer <jwt-token>
```

---

## REST API

### Health Check

#### `GET /health`

Check system status and pipeline health.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.1.0-alpha",
  "pipeline_fps": 30.2,
  "face_detected": true,
  "uptime_seconds": 3621,
  "modules": {
    "camera": "active",
    "face_detection": "active",
    "gaze_estimation": "active",
    "blink_detection": "active",
    "intent_recognition": "active",
    "safety_filter": "active",
    "os_integration": "active"
  }
}
```

**Response 503:**
```json
{
  "status": "degraded",
  "failing_modules": ["gaze_estimation"],
  "message": "Gaze model failed to load — check ONNX model path"
}
```

---

### Session Management

#### `POST /sessions`

Start a new EyeNav session.

**Request Body:**
```json
{
  "user_id": "user-001",
  "profile_id": "default",
  "camera_id": "0",
  "resolution": "1280x720",
  "fps_target": 30,
  "mode": "edge"
}
```

**Response 201:**
```json
{
  "session_id": "sess-a1b2c3d4-...",
  "started_at": 1700000000.000,
  "camera_info": {
    "id": "0",
    "name": "Integrated Webcam",
    "resolution": "1280x720",
    "fps": 30
  }
}
```

---

#### `DELETE /sessions/{session_id}`

Stop an active session.

**Response 200:**
```json
{
  "session_id": "sess-a1b2c3d4-...",
  "ended_at": 1700003600.000,
  "duration_seconds": 3600,
  "commands_executed": 127,
  "false_positives_blocked": 2
}
```

---

### Calibration

#### `POST /calibration/start`

Start calibration process.

**Request Body:**
```json
{
  "session_id": "sess-a1b2c3d4-...",
  "mode": "5_point",
  "profile_name": "default"
}
```

**Calibration Modes:**
- `"uncalibrated"` — No calibration, immediate use
- `"5_point"` — Rapid 5-point calibration (<30 seconds)
- `"13_point"` — Full 13-point calibration (<90 seconds)

**Response 200:**
```json
{
  "calibration_id": "cal-xyz...",
  "points": [
    {"id": 0, "x": 0.5, "y": 0.5, "label": "center"},
    {"id": 1, "x": 0.1, "y": 0.1, "label": "top_left"},
    {"id": 2, "x": 0.9, "y": 0.1, "label": "top_right"},
    {"id": 3, "x": 0.1, "y": 0.9, "label": "bottom_left"},
    {"id": 4, "x": 0.9, "y": 0.9, "label": "bottom_right"}
  ],
  "current_point": 0,
  "estimated_duration_seconds": 30
}
```

---

#### `POST /calibration/{calibration_id}/point/{point_id}/record`

Record gaze for a calibration point. User should be looking at the point when this is called.

**Response 200:**
```json
{
  "point_id": 0,
  "recorded": true,
  "samples_collected": 30,
  "quality": "good",
  "next_point_id": 1
}
```

---

#### `POST /calibration/{calibration_id}/complete`

Finalize calibration and compute mapping.

**Response 200:**
```json
{
  "calibration_id": "cal-xyz...",
  "success": true,
  "mean_error_degrees": 0.94,
  "max_error_degrees": 1.87,
  "quality": "good",
  "profile_saved": true,
  "profile_id": "profile-001"
}
```

---

### Configuration

#### `GET /config`

Get current configuration.

**Response 200:**
```json
{
  "safety": {
    "confidence_thresholds": {
      "low_risk": 0.85,
      "medium_risk": 0.92,
      "high_risk": 0.97,
      "critical_risk": 0.99
    },
    "cooldown_ms": {
      "scroll": 300,
      "select": 800,
      "back": 1200,
      "delete": 2000
    },
    "emergency_stop_duration_ms": 3000,
    "fatigue_monitoring_enabled": true
  },
  "calibration": {
    "mode": "5_point",
    "profile_id": "default",
    "continuous_refinement": true
  },
  "pipeline": {
    "fps_target": 30,
    "resolution": "1280x720",
    "gaze_smoothing": "kalman",
    "temporal_window_ms": 1500
  }
}
```

---

#### `PATCH /config`

Update configuration. Accepts partial updates.

**Request Body (example — update confidence threshold):**
```json
{
  "safety": {
    "confidence_thresholds": {
      "medium_risk": 0.95
    }
  }
}
```

**Response 200:**
```json
{
  "updated": true,
  "changes_applied": ["safety.confidence_thresholds.medium_risk"],
  "requires_restart": false
}
```

---

### Status & Diagnostics

#### `GET /status/gaze`

Current gaze estimate.

**Response 200:**
```json
{
  "timestamp": 1700000000.033,
  "frame_id": 108901,
  "face_detected": true,
  "gaze_screen": {
    "x": 0.512,
    "y": 0.348
  },
  "gaze_3d": {
    "x": -0.012,
    "y": 0.087,
    "z": 0.996
  },
  "confidence": 0.89,
  "head_pose": {
    "yaw": 2.3,
    "pitch": -5.1,
    "roll": 0.8
  }
}
```

---

#### `GET /status/intent`

Current intent prediction.

**Response 200:**
```json
{
  "timestamp": 1700000000.050,
  "intent": "reading",
  "confidence": 0.94,
  "attention_summary": {
    "most_important_feature": "gaze_velocity",
    "most_important_frames": [12, 13, 14, 15]
  },
  "safety_state": "active",
  "last_command": {
    "command": "scroll_down",
    "timestamp": 1699999960.200,
    "confidence": 0.96
  }
}
```

---

#### `GET /status/safety`

Safety system state.

**Response 200:**
```json
{
  "emergency_stop_active": false,
  "fatigue_level": "moderate",
  "active_cooldowns": {
    "select": {
      "remaining_ms": 320
    }
  },
  "session_stats": {
    "commands_executed": 127,
    "commands_blocked_safety": 14,
    "estimated_false_positives_blocked": 2
  }
}
```

---

## WebSocket API

### Connect

```
ws://localhost:8765/ws/v1/stream?session_id=sess-xxx&auth=token
```

### Subscribe to Streams

After connecting, send a subscription message:

```json
{
  "type": "subscribe",
  "streams": ["gaze", "intent", "commands", "features"]
}
```

### Stream: Gaze

Published at camera framerate (30fps default):

```json
{
  "stream": "gaze",
  "timestamp": 1700000000.033,
  "frame_id": 108901,
  "gaze_screen": {"x": 0.512, "y": 0.348},
  "gaze_3d": {"x": -0.012, "y": 0.087, "z": 0.996},
  "confidence": 0.89,
  "smoothed": true
}
```

### Stream: Intent

Published when intent changes or confidence exceeds threshold:

```json
{
  "stream": "intent",
  "timestamp": 1700000000.050,
  "intent": "selecting",
  "confidence": 0.95,
  "duration_ms": 820,
  "gesture_sequence": ["fixation_600ms", "blink_single"]
}
```

### Stream: Commands

Published when a command is executed:

```json
{
  "stream": "commands",
  "timestamp": 1700000000.200,
  "command": "scroll_down",
  "execution_id": "exec-abc...",
  "confidence": 0.96,
  "safety_layers_passed": 6
}
```

### Stream: Features

Published per-frame — full feature vector for research/debugging:

```json
{
  "stream": "features",
  "timestamp": 1700000000.033,
  "frame_id": 108901,
  "features": [0.012, -0.087, 0.996, 0.512, 0.348, 0.32, 0.31, ...]
}
```

---

## Error Codes

| Code | Name | Description |
|---|---|---|
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing or invalid auth token |
| 404 | Not Found | Session or resource not found |
| 409 | Conflict | Session already active for user |
| 422 | Unprocessable | Valid JSON but invalid parameter values |
| 500 | Internal Error | Pipeline error — check /health |
| 503 | Service Unavailable | Camera or model not available |

---

## Rate Limits

| Endpoint | Limit |
|---|---|
| REST endpoints | 100 req/min per session |
| WebSocket streams | No limit (streaming) |
| Calibration endpoints | 10 req/min per session |
| Config updates | 30 req/min per session |

---

## SDK

See [docs/sdk/README.md](../sdk/README.md) for Python and JavaScript SDK documentation that wraps this API.

---

## Changelog

| Version | Changes |
|---|---|
| 0.1.0-alpha | Initial API design |
