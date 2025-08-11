APP_NAME = tilf
MAIN_SCRIPT = main.py
VENV_DIR = env
RESOURCES_DIR = assets
STYLESHEET_FILE = style.qss

ifeq ($(OS),Windows_NT)
    PYINSTALLER_DATA_SEP = ;
    PYTHON = $(VENV_DIR)/Scripts/python
    ICON_FILE = $(RESOURCES_DIR)/icon.ico
else
    PYINSTALLER_DATA_SEP = :
    PYTHON = $(VENV_DIR)/bin/python
    ifeq ($(shell uname), Darwin)
        ICON_FILE = $(RESOURCES_DIR)/icon.icns
    else
        ICON_FILE = $(RESOURCES_DIR)/icon.ico
    endif
endif

.PHONY: all build clean run install

all: build

install: $(VENV_DIR)/touchfile

$(VENV_DIR)/touchfile: requirements.txt
	@echo "Creating virtual environment and installing dependencies..."
	test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	@touch $(VENV_DIR)/touchfile

requirements.txt:
	@echo "Generating requirements.txt..."
	@echo "pyside6" > requirements.txt
	@echo "pyinstaller" >> requirements.txt
	@echo "requirements.txt created successfully."

# pyinstaller --name tilf --onefile --windowed
# --icon assets/icon.icns --add-data assets:assets --add-data style.qss:.
# main.py
build: install
	@echo "Building the application bundle..."
	$(PYTHON) -m PyInstaller --name $(APP_NAME) \
							--onefile \
							--windowed \
							--icon=$(ICON_FILE) \
							--add-data "$(RESOURCES_DIR)$(PYINSTALLER_DATA_SEP)$(RESOURCES_DIR)" \
							--add-data "$(STYLESHEET_FILE)$(PYINSTALLER_DATA_SEP)." \
							$(MAIN_SCRIPT)
	@echo "Build complete. Check the 'dist' folder."

run:
	@echo "Running $(APP_NAME)..."
	./dist/$(APP_NAME)

clean:
	@echo "Cleaning up build files and virtual environment..."
	rm -rf build dist __pycache__
	rm -f $(APP_NAME).spec
	rm -rf $(VENV_DIR)
	rm -f requirements.txt
	@echo "Cleanup complete."