# splashscreen/

Logo assets and boot splash for the EuclidCam.

| File                   | Notes                                              |
|------------------------|----------------------------------------------------|
| `transparent_logo.png` | RGBA watermark — used in capture overlays          |
| `transparent.svg`      | Source vector                                      |
| `generate_splash.py`   | Renders `transparent_logo.png` from the SVG        |
| `euclid_splash.png`    | Boot splash                                        |
| `chalk_settings.json`  | Parameters passed to `generate_splash.py`          |

Regenerate: `python3 splashscreen/generate_splash.py` (or `make install`).  
Watermark opacity is set in `UI/themes/chalk.py → LOGO_OPACITY`.
