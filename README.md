# EuclidCam

Custom embedded camera firmware for a Raspberry Pi point-and-shoot. Runs headlessly on a 480×320 SPI display with a capacitive touch panel.

```
euclidcam/
├── firmware/python/       # On-device runtime
│   ├── main.py            # CameraEngine — event loop, all subsystems
│   ├── camera.py          # systemd entry point
│   ├── filters/           # PIL colour-grading modules
│   ├── UI/                # Framebuffer renderer, touch controller, themes
│   ├── settings/          # Composition grid
│   ├── connectivity/      # Flask server + WiFi helpers
│   └── IO/                # GPIO / evdev stubs
├── splashscreen/          # Logo assets
├── Webapp/                # Remote gallery (served over WiFi)
└── Captured/              # Photo output (on-device)
```

## Setup

```bash
make install    # apt + pip deps, splash assets
make run        # foreground launch
make service-install  # register systemd unit
```

## Dev

```bash
make check   # syntax-check all .py files
make lint    # flake8
make clean   # remove __pycache__, temp.jpg
```
