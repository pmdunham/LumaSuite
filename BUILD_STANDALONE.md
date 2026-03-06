# Building Standalone Executables for LumaServer

This guide explains how to build portable .exe (Windows) and .app (macOS) executables for LumaServer.

## Requirements

- Python 3.8+
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation & Build

### Windows (.exe)

1. **Install dependencies:**
   ```bash
   pip install -r requirements-build.txt
   ```

2. **Build the Windows executable:**
   ```bash
   python build_executable.py windows
   ```

   Or to build for the current platform:
   ```bash
   python build_executable.py
   ```

3. **Output:**
   ```
   dist/Windows/LumaServer.exe
   ```

4. **Run the executable:**
   - Double-click `LumaServer.exe`
   - A window will open
   - The default browser will auto-launch with `http://127.0.0.1:5000`
   - Click "Open Browser" to manually open the UI
   - Click "Quit" to close the server and exit

### macOS (.app)

1. **Install dependencies:**
   ```bash
   pip install -r requirements-build.txt
   ```

2. **Build the macOS app:**
   ```bash
   python build_executable.py mac
   ```

3. **Output:**
   ```
   dist/macOS/LumaServer.app
   ```

4. **Run the app:**
   - Double-click `LumaServer.app` or drag to Applications folder
   - A window will open
   - The default browser will auto-launch with `http://127.0.0.1:5000`
   - Click "Open Browser" to manually open the UI
   - Click "Quit" to close the server and exit

## Features

- **Standalone:** No Python installation required on end-user machines
- **Portable:** Single executable file (Windows) or app bundle (macOS)
- **Auto-Launch Browser:** Automatically opens the web UI in your default browser
- **GUI Window:** Minimalist control window with status and manual browser open button
- **Clean Exit:** Gracefully shuts down server when window is closed

## Command-Line Arguments

You can pass arguments to control host/port:

```bash
# Windows
LumaServer.exe --host=0.0.0.0 --port=8080

# macOS
LumaServer.app/Contents/MacOS/LumaServer --host=0.0.0.0 --port=8080
```

## Troubleshooting

### Windows
- **"Windows protected your PC"** - This is a SmartScreen warning. Click "More info" → "Run anyway"
- **Port already in use** - Use `--port=8080` to specify a different port

### macOS
- **"LumaServer cannot be opened"** - Right-click → Open (or lower security settings temporarily)
- **"Developer cannot be verified"** - System Preferences → Security & Privacy → Open Anyway

## Distribution

To distribute:

1. **Windows:** Zip and distribute the `dist/Windows/LumaServer.exe` file
2. **macOS:** Create a DMG installer or distribute the `dist/macOS/LumaServer.app` bundle

## Building from Cross-Platform

To build for a different platform, you need to run the build script on that platform. For example:
- To build Windows .exe: Run the script on a Windows machine
- To build macOS .app: Run the script on a Mac

Alternatively, you can use CI/CD (GitHub Actions, etc.) to automate cross-platform builds.
