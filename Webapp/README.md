# Webapp/

Remote photo gallery, served over WiFi by `connectivity/server.py` (Flask, port 5000).

The camera displays a QR code when connected. Scanning it opens this UI in any browser — browse, view full-size, download photos.

Local preview (no Flask):
```bash
cd Webapp && python3 -m http.server 8080
```
