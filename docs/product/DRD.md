# EyeNav — Design Requirements Document (DRD)

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** UX/Design Team  
**Last Updated:** 2024-Q4  

---

## 1. Purpose

This Design Requirements Document defines the UX, interaction design, and visual design requirements for all EyeNav user interfaces — including the calibration wizard, settings dashboard, and status overlay.

---

## 2. Design Principles

### DP-1 — Accessible First
All UI elements must be fully accessible before adding visual polish. Screen reader compatible, keyboard navigable, high contrast compliant.

### DP-2 — Unobtrusive During Operation
EyeNav is a background system. During normal use, its presence must be minimal. The user should not feel surveilled by their own assistive tool.

### DP-3 — Clear System State
The user must always know:
- Is EyeNav active?
- Is it seeing their eyes?
- What did it last do?
- What confidence level is it operating at?

### DP-4 — Progressive Disclosure
New users see simple defaults. Advanced users can access full configuration. Complexity is always optional, never mandatory.

### DP-5 — Forgiving
All actions must be reversible. No destructive action without confirmation. Emergency stop is always one gesture away.

---

## 3. UI Components

### 3.1 Status Indicator (Always Visible)

**Purpose:** Show EyeNav activity state without being intrusive.

**Location:** System tray / menu bar (not on screen content)

**States:**
- 🟢 Active — EyeNav tracking, ready
- 🟡 Low confidence — Accuracy degraded (lighting, glasses)
- 🔴 Emergency stop — All commands disabled
- ⚫ Inactive — System off
- 🔵 Calibrating — Calibration in progress

**Accessibility:**
- Screen reader: Announces state changes
- No dependency on color alone (shape + text also conveys state)

---

### 3.2 Calibration Wizard

**Purpose:** Guide new users through calibration.

**Design:**
- Full-screen overlay (dark background)
- Circular target at calibration points
- Animated dot: smooth movement between points
- Progress bar showing overall completion
- Text instructions (large font, high contrast)
- Audio cues (optional)
- Skip button: allows skipping to uncalibrated mode

**Accessibility:**
- Font: ≥ 18pt
- Contrast ratio: ≥ 7:1 (WCAG AAA)
- Screen reader: Describes each point location
- Keyboard: Enter to advance, Escape to skip

---

### 3.3 Settings Dashboard

**Purpose:** Full configuration interface.

**Layout:**
- Left sidebar: Section navigation (Camera, Safety, Calibration, Commands, Privacy, About)
- Main area: Settings for selected section
- Live preview: Camera view with gaze overlay (optional, privacy-respecting)

**Key Settings Exposed:**
- Safety thresholds (slider per risk level)
- Cooldown durations (slider per command)
- Calibration profile selection and management
- Privacy controls (analytics opt-in/out, data export, data deletion)
- Emergency stop gesture configuration
- Command mapping customization

**Accessibility:**
- All controls keyboard navigable
- All sliders have numeric input alternative
- Screen reader: Labels and descriptions for all controls
- Dark mode: System setting respected

---

### 3.4 Gaze Overlay (Debug/Research Mode)

**Purpose:** Visualize gaze tracking for development and research.

**Elements:**
- Gaze crosshair (translucent circle)
- Confidence ring (thickness indicates confidence)
- Intent label (small overlay text)
- Eye region boxes (for debugging)

**Activation:** Developer mode only — not shown in production builds by default.

---

## 4. Interaction Design

### 4.1 Dwell Confirmation UI

When a high-risk command requires dwell confirmation:

**Visual:**
- Circular progress ring around gaze target
- Grows from 0% to 100% during dwell period
- Color: orange (50%) → green (100%)
- Gaze break: Ring immediately vanishes (resets)
- Completion: Brief green flash + audio click

**Audio (optional):**
- 50% dwell: Low tone
- 75% dwell: Medium tone
- 100% dwell: Success chime

---

### 4.2 Emergency Stop Indication

**When triggered:**
- Full-screen semi-transparent red overlay (2 seconds)
- Large "Eye Navigation Paused" text
- Auto-dismiss after 2 seconds

**Recovery:**
- "Look here to resume" indicator appears at screen center
- 500ms gaze confirmation to re-enable

---

## 5. Accessibility Requirements

| Requirement | Standard | Target |
|---|---|---|
| Color contrast (text) | WCAG 2.2 | ≥ 7:1 (AAA) |
| Color contrast (UI elements) | WCAG 2.2 | ≥ 3:1 (AA) |
| Keyboard operability | WCAG 2.2 SC 2.1.1 | 100% |
| Screen reader labels | WCAG 2.2 SC 1.3.1 | 100% |
| Focus visible | WCAG 2.2 SC 2.4.7 | 100% |
| Minimum touch target | WCAG 2.2 SC 2.5.5 | 44×44px |
| Timeout warnings | WCAG 2.2 SC 2.2.1 | All timeouts warned |
| Error identification | WCAG 2.2 SC 3.3.1 | Text description |

---

## 6. Design System

### 6.1 Colors

```
Primary:    #1A73E8  (accessible blue)
Success:    #188038  (green — accessible)
Warning:    #E37400  (amber — accessible)
Danger:     #C5221F  (red — accessible)
Background: #FFFFFF  (light) / #202124  (dark)
Surface:    #F8F9FA  (light) / #2D2E31  (dark)
Text:       #202124  (light) / #E8EAED  (dark)
```

### 6.2 Typography

```
Font family: Inter (Google Fonts)
Heading 1:  28px bold
Heading 2:  22px semi-bold
Heading 3:  18px semi-bold
Body:       16px regular
Caption:    14px regular
Minimum:    14px (never smaller)
```

### 6.3 Icons

Use system icons (SF Symbols on macOS, Material Icons on Windows/Android) for platform consistency. Never use icon-only buttons without text label or tooltip.
