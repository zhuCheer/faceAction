# FaceAction — Facial Gesture Control Assistant (Short-Video Browsing + Anti-Peeping)

Make a few face gestures in front of an ordinary webcam to browse short videos: **nod for the next video, look up for the previous one, shake your head to switch menus**. With "Anti-Peep" enabled, the screen automatically switches to the desktop when you leave the frame and restores the browser when you return. Everything runs **fully offline and locally — camera frames never leave your machine**.

## Background

This project started from a simple idea:

- **Couch potatoes**: lying down, too lazy to reach for the keyboard — just move your face to scroll through videos;
- **Sneaky browsers**: watching videos at work/school who need the screen hidden automatically when someone approaches;
- **Content creators**: shooting "control your PC with your face" skits or live-streaming hands-free demos.

They all share the same need: **watch the screen, move your face, browse videos — with one-switch anti-peeping.** That's how FaceAction came to be — a Windows desktop app based on an ordinary webcam, with no extra hardware required.

![Sneak scrolling, undetected](assets/2.jpeg)
*Scroll videos by shaking your head; anti-peep standby kicks in when someone approaches*

## Use Cases

| Audience | Typical Scenario | Key Concern |
|----------|------------------|-------------|
| Couch potatoes | Scrolling videos in bed / on the sofa | Simple, few false triggers |
| Sneaky browsers | Watching at work/school, instantly switching to desktop when someone approaches | Reliable anti-peeping |
| Meme players / creators | Screen recording / live-streaming "hands-free PC control" | Demo quality, entertainment value |

## Features

### 1. Video Browsing

- **Enter**: nod while the "Video" item is highlighted in the menu — the default browser opens the web version of the short-video site;
- **Next**: nod (lower your head) → keyboard `↓`;
- **Previous**: look up (tilt your head back) → keyboard `↑`;
- **Back**: open your mouth twice in a row to return to the menu.

### 2. Anti-Peep

- **Toggle**: nod while the "Anti-Peep" item is highlighted to switch on/off;
- **Global once enabled**: works regardless of whether you're in video mode — the two coexist happily;
- **Face leaves the frame**: automatically triggers `Win+D` to show the desktop, hiding the video you were watching;
- **Face returns**: automatically restores the browser; if it hasn't been launched yet, the video site opens automatically;
- **Debouncing**: a face appearing/disappearing must persist for 500 ms before switching, avoiding flickering.

![Boss incoming! Hide in one second](assets/1.jpeg)
*A second face detected — immediately minimized to the desktop*

### Gesture → Action Reference

| State | Gesture | Effect |
|-------|---------|--------|
| Menu state | Shake left / right | Select previous / next item |
| Menu state | Nod | Enter "Video" mode or toggle "Anti-Peep" |
| Video state | Nod / look up | Next (↓) / previous (↑) |
| Video state | Open mouth ×2 | Return to menu state |

## Requirements

- Windows 10 / 11
- Python 3.9+ (mediapipe 0.10.14 works best with 3.9)
- An ordinary webcam (built-in laptop camera or external USB camera)

## Installation & Launch

### Option 1: One-click Script (Recommended)

```powershell
cd src
.\start.ps1              # Default camera (index 0)
.\start.ps1 -Camera 1    # Specify a camera
.\start.ps1 -Test        # Run core logic unit tests (no camera needed)
```

The first run of `start.ps1` automatically creates the `.venv` virtual environment and installs dependencies (mediapipe is large — please be patient).

### Option 2: Manual Run

```powershell
cd src
pip install -r requirements.txt
python app.py            # Default camera
python app.py 1          # Specify camera index
```

### Running Tests

```powershell
cd src
python -m unittest discover -s tests -v
```

Tests cover pure logic in `core/` (feature extraction, gesture detection, state machine, mapping, etc.) — no camera needed.

## Packaging

Use PyInstaller to build a ready-to-distribute Windows EXE:

```powershell
cd src
.\build_exe.ps1          # Single-file exe -> release\FaceAction.exe
.\build_exe.ps1 -Dir     # Directory mode -> release\FaceAction\ (faster startup, less likely to trigger AV false positives)
```

The script automatically prepares `.venv`, installs dependencies and PyInstaller (including mediapipe resource collect-all). The packaged build reads its configuration from `<exe directory>\config\settings.json`; you can place an editable config file next to the exe.

## Configuration

Edit `src/config/settings.json`:

```json
{
  "mouse_step": 12,
  "camera_index": 0,
  "theme": "light",
  "language": "en"
}
```

- `mouse_step`: head movement sensitivity in video mode;
- `camera_index`: camera index (default 0);
- `theme`: UI theme (`light` / `dark`);
- `language`: UI language (`zh` / `en`).

## Technical Implementation

The overall design is a real-time pipeline of "capture → recognize → decide → execute", with the UI and algorithms cleanly decoupled:

```
Camera (OpenCV) → MediaPipe FaceMesh 468 landmarks
                    ↓
      Feature extraction (EAR eye aspect ratio / MAR mouth aspect ratio / pitch-yaw head pose)
                    ↓
      Gesture detection (blink / mouth open / nod / look up / directional head shake / head tilt)
                    ↓
      Behavior state machine (menu state ⇄ video state + anti-peep face edge detection)
                    ↓
      Action mapping → executor (Win32 SendInput key simulation / launch browser / Win+D)
```

- **Face tracking**: [MediaPipe FaceMesh](https://developers.google.com/mediapipe) extracts 468 facial landmarks in real time;
- **Feature engineering**: EAR (blinks), MAR (mouth opening), head Euler angles (nod / shake / tilt);
- **Gesture recognition**: temporal thresholds + edge detection with debouncing;
- **Action execution**: Windows `SendInput` API sends system-level keyboard events; `webbrowser` opens web pages;
- **UI**: PySide6 (Qt6) — borderless always-on-top floating window, two-state window (large menu / small bottom-right preview), glassmorphism themes (dark/light), bilingual (Chinese/English);
- **Architecture principles**: `core/` contains only algorithms and business logic (no UI dependency, independently unit-testable); `ui/` handles presentation and thread scheduling only; `config/` holds user-editable resources.

### Project Structure

```
src/
├── app.py                  # Entry point: load config → engine → main window
├── start.ps1               # One-click launch / test script
├── build_exe.ps1           # PyInstaller packaging script
├── FaceAction.spec         # PyInstaller packaging config
├── i18n.py                 # Chinese/English i18n
├── requirements.txt        # Dependency list
├── config/
│   └── settings.json       # User config: sensitivity / camera / theme / language
├── core/                   # Business & algorithm logic (no UI dependency)
│   ├── constants.py        #   Landmark indices + threshold definitions
│   ├── features.py         #   Feature extraction (EAR/MAR/pose)
│   ├── detector.py         #   Gesture detection (blink/mouth/nod/shake/tilt)
│   ├── anti_peep.py        #   Anti-peep controller (face edge → desktop/restore)
│   ├── state_machine.py    #   Behavior state machine (video/anti-peep)
│   ├── mapper.py           #   Gesture → action mapping
│   ├── executor.py         #   Action execution (Win32 SendInput / browser)
│   ├── tracker.py          #   MediaPipe FaceMesh wrapper
│   ├── engine.py           #   Pipeline orchestration (track→recognize→execute)
│   └── config.py           #   Config loading
├── ui/                     # UI layer (PySide6)
│   ├── theme.py            #   Dark/light themes + QSS
│   └── main_window.py      #   Two-state window + camera thread + toast tips
└── tests/                  # Unit tests (no camera needed)
_doc/                       # Spec / design / tasks / user guide documents
release/                    # Packaged build output (not committed)
```

## Scope & Limitations

**Currently supported:**

- Face detection and 468-landmark extraction with an ordinary webcam;
- Gesture recognition: nod / look up / head shake left-right / mouth open / blink, etc.;
- Two core features: video browsing (web version, scroll up/down) and anti-peeping (switch to desktop / restore);
- Windows 10/11, fully local and offline.

**Currently not supported (Scope Out):**

- macOS / Linux;
- General hands-free control (mouse control, scroll paging, media control, etc.);
- Multi-level menus; anti-peep has only on/off states;
- Cloud services or face data upload (purely local by design).

## Privacy & Security

- **Camera frames are processed only in local memory** — never uploaded, never written to disk, never sent over the network;
- All gesture recognition runs on local MediaPipe model inference;
- The program only sends system-level keyboard events (arrow keys, `Win+D`) and opens the browser — it reads no personal data.

> Please use the "Anti-Peep" feature responsibly and comply with your environment's rules; take breaks from the camera during long sessions.

## Development & Contributing

```powershell
git clone <repo-url>
cd face-action/src
.\start.ps1 -Test   # Run the tests first to verify your environment
```

Issues and PRs are welcome: fixing misrecognition, adding new gestures, supporting more platforms — all are appreciated.

## License

This project is open-sourced under the [MIT License](LICENSE).

## Related Documents

- [Requirements Spec (SPEC)](_doc/SPEC.md)
- [Implementation Notes (IMPLEMENT)](_doc/IMPLEMENT.md)
- [Task Breakdown (TASK)](_doc/TASK.md)
- [User Guide (USER_GUIDE)](_doc/USER_GUIDE.md)
- [UI Design Draft](_doc/design/FaceAction-UI-Glassmorphism.html)
