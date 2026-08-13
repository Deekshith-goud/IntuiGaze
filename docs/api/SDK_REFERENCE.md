# EyeNav — SDK Documentation

**Version:** 1.0.0-alpha  
**Status:** Draft — Pre-release  
**Audience:** Third-party developers integrating EyeNav into their applications  

---

## 1. Overview

The EyeNav SDK allows developers to embed intent-driven gaze navigation into their own applications. The SDK handles all the complexity of the vision pipeline — developers receive high-level intent events and gaze coordinates.

### 1.1 SDK Variants

| SDK | Language | Platform | Mode |
|---|---|---|---|
| `eyenav-python` | Python | Desktop, Server | Import library |
| `eyenav-js` | TypeScript | Web, Electron, Node.js | npm package |
| `eyenav-swift` | Swift | iOS, macOS, visionOS | Swift Package |
| `eyenav-kotlin` | Kotlin/Java | Android | AAR |
| `eyenav-cpp` | C++ | Desktop, Embedded | CMake |

This document covers the **Python SDK** (v1.0) and **JavaScript SDK** (v1.5, preview).

---

## 2. Python SDK

### 2.1 Installation

```bash
pip install eyenav-sdk
```

Requirements:
- Python 3.11+
- Camera access permission
- 512MB RAM

### 2.2 Quick Start

```python
from eyenav import EyeNavClient, IntentEvent, GazeEvent

# Initialize with default config
client = EyeNavClient()

# Register event handlers
@client.on_intent
def handle_intent(event: IntentEvent) -> None:
    """Called when user intent is recognized."""
    print(f"Intent: {event.intent} (confidence: {event.confidence:.2f})")
    
    if event.intent == "selecting" and event.confidence > 0.95:
        print(f"User is selecting at {event.gaze_screen}")

@client.on_gaze
def handle_gaze(event: GazeEvent) -> None:
    """Called every frame with gaze estimate."""
    # Throttle to avoid overwhelming your app
    pass

# Start the pipeline
with client:
    client.run()  # Blocks until stopped
```

### 2.3 Async API

```python
import asyncio
from eyenav import AsyncEyeNavClient

async def main():
    async with AsyncEyeNavClient() as client:
        async for event in client.intent_stream():
            print(f"Intent: {event.intent}")
            if event.intent == "selecting":
                await handle_select(event)

asyncio.run(main())
```

### 2.4 Event Types

#### IntentEvent

```python
@dataclass
class IntentEvent:
    intent: str                   # Intent class name
    confidence: float             # 0.0–1.0 confidence score
    command: Optional[str]        # Suggested OS command (if any)
    command_confidence: float     # Command confidence
    gaze_screen: tuple[float, float]  # Normalized screen coords (0–1)
    gaze_3d: tuple[float, float, float]  # 3D gaze direction vector
    timestamp_ms: float           # Event timestamp (ms since epoch)
    attention_weights: list[float]  # Temporal attention (explainability)
    frame_index: int              # Pipeline frame number
```

#### GazeEvent

```python
@dataclass
class GazeEvent:
    gaze_screen: tuple[float, float]   # Normalized screen coords
    gaze_3d: tuple[float, float, float]  # 3D direction vector
    confidence: float                   # Gaze confidence
    blink_state: str                    # "open", "blinking", "closed"
    timestamp_ms: float
    frame_index: int
```

#### SystemEvent

```python
@dataclass
class SystemEvent:
    event_type: str   # "started", "stopped", "calibrated", "error", "emergency_stop"
    message: str      # Human-readable description
    timestamp_ms: float
```

### 2.5 Configuration

```python
from eyenav import EyeNavClient, Config, SafetyConfig

config = Config(
    camera_id=0,
    target_fps=30,
    safety=SafetyConfig(
        confidence_threshold=0.95,
        cooldown_ms=800,
        emergency_stop_enabled=True,
    )
)

client = EyeNavClient(config=config)
```

Or load from YAML:

```python
config = Config.from_file("my_config.yaml")
client = EyeNavClient(config=config)
```

### 2.6 Calibration

```python
# Start calibration wizard (blocking — shows UI)
result = client.calibrate(points=9)
print(f"Calibration MAE: {result.mae_degrees:.2f}°")
print(f"Profile saved: {result.profile_path}")

# Load existing calibration profile
client.load_calibration("~/.eyenav/profiles/default.yaml")

# Check if calibrated
print(client.is_calibrated)  # True/False
```

### 2.7 Custom Command Mapping

```python
from eyenav import CommandMapper, Intent

mapper = CommandMapper()

# Map intent to custom action
@mapper.on(Intent.SELECTING)
def on_select(event: IntentEvent) -> None:
    x, y = event.gaze_screen
    # Your click logic here
    your_app.click(x, y)

@mapper.on(Intent.SCROLLING_DOWN)
def on_scroll_down(event: IntentEvent) -> None:
    your_app.scroll(-3)  # Scroll 3 units down

client = EyeNavClient(command_mapper=mapper)
```

### 2.8 Explainability

Access attention weights to understand why an intent was classified:

```python
@client.on_intent
def handle_intent(event: IntentEvent) -> None:
    # attention_weights[i] = weight for frame i in temporal window
    # High weight = that frame was important for classification
    max_weight_frame = max(range(len(event.attention_weights)),
                          key=lambda i: event.attention_weights[i])
    print(f"Key frame: {max_weight_frame} frames ago")
    print(f"Weights: {event.attention_weights}")
```

---

## 3. JavaScript SDK (Preview — v1.5)

### 3.1 Installation

```bash
npm install @eyenav/sdk
```

Requires EyeNav server running locally:
```bash
eyenav server --port 8765
```

### 3.2 Browser / Electron Quick Start

```typescript
import { EyeNavClient, IntentEvent } from '@eyenav/sdk';

const client = new EyeNavClient({ serverUrl: 'ws://localhost:8765/stream' });

client.on('intent', (event: IntentEvent) => {
  console.log(`Intent: ${event.intent} (${event.confidence.toFixed(2)})`);
  
  if (event.intent === 'selecting') {
    const [x, y] = event.gazeScreen;
    document.elementFromPoint(
      x * window.innerWidth,
      y * window.innerHeight
    )?.click();
  }
});

client.on('gaze', (event) => {
  // Update gaze cursor UI element
  gazeCursor.style.left = `${event.gazeScreen[0] * 100}%`;
  gazeCursor.style.top = `${event.gazeScreen[1] * 100}%`;
});

await client.connect();
```

### 3.3 React Hook

```typescript
import { useEyeNav } from '@eyenav/react';

function MyComponent() {
  const { intent, gaze, isConnected } = useEyeNav({
    serverUrl: 'ws://localhost:8765/stream',
  });

  return (
    <div>
      <p>Connected: {isConnected ? 'Yes' : 'No'}</p>
      <p>Current Intent: {intent?.intent ?? 'none'}</p>
      <p>Gaze: {gaze ? `(${gaze.gazeScreen[0].toFixed(2)}, ${gaze.gazeScreen[1].toFixed(2)})` : 'no signal'}</p>
    </div>
  );
}
```

---

## 4. SDK Security

### 4.1 What the SDK Can Access

- Gaze coordinates (normalized 0–1)
- Intent classifications
- Blink state
- Confidence scores
- Attention weights

### 4.2 What the SDK Cannot Access

- Raw camera frames (never exposed)
- Raw face images
- Eye region images
- Any personally identifiable information

### 4.3 SDK Authentication (Server Mode)

```python
# Server mode requires API key
client = EyeNavClient(
    mode="server",
    server_url="ws://localhost:8765",
    api_key="your-api-key-here"
)
```

API keys are scoped — a key can be limited to read-only gaze events, or given full command execution rights.

---

## 5. SDK Changelog

### v1.0.0-alpha (current)
- Python SDK: Full intent and gaze event API
- Configuration API
- Calibration API
- Explainability (attention weights)

### v1.5.0 (planned)
- JavaScript/TypeScript SDK
- React hooks
- Electron integration helpers
- Mobile SDKs (iOS Swift, Android Kotlin)

### v2.0.0 (planned)
- C++ SDK
- OpenXR integration
- visionOS SDK
