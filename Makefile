APP_NAME = tilf
MAIN_SCRIPT = main.py
VENV_DIR = env
RESOURCES_DIR = assets
STYLESHEET_FILE = style.qss
PYINSTALLER_DATA_SEP = :
PYTHON ?= python3
VENV_PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_PYTHON) -m pip

ifeq ($(shell uname), Darwin)
	ICON_FILE = $(RESOURCES_DIR)/icon.icns
else
	ICON_FILE = $(RESOURCES_DIR)/icon.ico
endif

.PHONY: all build check clean dev install lint run test typecheck

all: build

install: $(VENV_DIR)/.installed

$(VENV_PYTHON):
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)

$(VENV_DIR)/.installed: pyproject.toml | $(VENV_PYTHON)
	@echo "Creating virtual environment and installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@touch $(VENV_DIR)/.installed

dev: install
	@echo "Running $(APP_NAME) from source..."
	$(VENV_PYTHON) $(MAIN_SCRIPT)

lint: install
	$(VENV_PYTHON) -m ruff check .

typecheck: install
	$(VENV_PYTHON) -m mypy .

test: install
	$(VENV_PYTHON) -m pytest -q

check: lint typecheck test

build: install
	@echo "Building the application bundle..."
	$(VENV_PYTHON) -m PyInstaller --name $(APP_NAME) \
		--onefile \
		--windowed \
		--icon=$(ICON_FILE) \
		--add-data "$(RESOURCES_DIR)$(PYINSTALLER_DATA_SEP)$(RESOURCES_DIR)" \
		--add-data "$(STYLESHEET_FILE)$(PYINSTALLER_DATA_SEP)." \
		$(MAIN_SCRIPT)
	@echo "Build complete. Check the 'dist' folder."

run: build
	@echo "Running $(APP_NAME)..."
	./dist/$(APP_NAME)

clean:
	@echo "Cleaning up build files and virtual environment..."
	rm -rf build dist __pycache__
	rm -f $(APP_NAME).spec
	rm -rf $(VENV_DIR)
	@echo "Cleanup complete."
