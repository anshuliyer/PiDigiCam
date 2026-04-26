# ============================================================
#  EuclidCam — Makefile
# ============================================================

SHELL        := /bin/bash
PYTHON       := python3
FW_DIR       := firmware/python
SERVICE_NAME := euclidcam
SERVICE_FILE := /etc/systemd/system/$(SERVICE_NAME).service

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "EuclidCam"
	@echo ""
	@echo "  make install          apt + pip deps, generate splash assets"
	@echo "  make run              launch firmware (foreground)"
	@echo "  make check            syntax-check all Python files"
	@echo "  make lint             flake8"
	@echo "  make service-install  register + enable systemd unit"
	@echo "  make service-start    start service"
	@echo "  make service-stop     stop service"
	@echo "  make service-log      tail journal (60 lines, follow)"
	@echo "  make clean            remove __pycache__, temp.jpg"

# ── Install ────────────────────────────────────────────────────────────────────

.PHONY: install
install: _apt _pip _splash

.PHONY: _apt
_apt:
	sudo apt-get update -qq
	sudo apt-get install -y --no-install-recommends \
		python3 python3-pip python3-venv \
		python3-picamera2 python3-numpy python3-pil \
		python3-flask python3-evdev \
		libcap-dev libcamera-apps \
		fonts-dejavu-core v4l-utils flake8 git

.PHONY: _pip
_pip:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install picamera2 Pillow numpy Flask evdev qrcode requests

.PHONY: _splash
_splash:
	$(PYTHON) splashscreen/generate_splash.py || true

# ── Run ────────────────────────────────────────────────────────────────────────

.PHONY: run
run:
	cd $(FW_DIR) && $(PYTHON) camera.py

# ── Code quality ───────────────────────────────────────────────────────────────

.PHONY: check
check:
	@find $(FW_DIR) -name "*.py" | sort | while read f; do \
		$(PYTHON) -c "import ast; ast.parse(open('$$f').read())" \
			&& echo "  ok  $$f" || echo "  ERR $$f"; \
	done

.PHONY: lint
lint:
	flake8 $(FW_DIR) --max-line-length=100 \
		--exclude=__pycache__,.venv \
		--extend-ignore=E501,W503

# ── systemd ────────────────────────────────────────────────────────────────────

EXEC_PATH := $(shell realpath $(FW_DIR)/camera.py)
USER_NAME := $(shell whoami)
WORK_DIR  := $(shell realpath $(FW_DIR))

.PHONY: service-install
service-install:
	printf '[Unit]\nDescription=EuclidCam Firmware\nAfter=multi-user.target\n\n[Service]\nType=simple\nUser=$(USER_NAME)\nWorkingDirectory=$(WORK_DIR)\nExecStart=/usr/bin/python3 $(EXEC_PATH)\nRestart=on-failure\nRestartSec=3s\nStandardOutput=journal\nStandardError=journal\n\n[Install]\nWantedBy=multi-user.target\n' \
		| sudo tee $(SERVICE_FILE) > /dev/null
	sudo systemctl daemon-reload
	sudo systemctl enable $(SERVICE_NAME)

.PHONY: service-start
service-start:
	sudo systemctl start $(SERVICE_NAME)

.PHONY: service-stop
service-stop:
	sudo systemctl stop $(SERVICE_NAME)

.PHONY: service-log
service-log:
	journalctl -u $(SERVICE_NAME) -n 60 -f

# ── Clean ──────────────────────────────────────────────────────────────────────

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "temp.jpg" -delete 2>/dev/null || true
