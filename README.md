# Caffeine Windows

A Python-based utility that prevents your Windows machine from auto-locking and keeps your system active during specified time windows.

## Features

- 🕒 Configurable active hours for each day of the week
- ⏰ Easy-to-use GUI setup for time windows
- 🔄 Persistent settings saved between runs
- 💤 Prevents system sleep and screen lock during active hours
- 📊 Detailed console logging of activity status
- ✨ Minimal system interference during operation

## Requirements

- Windows OS
- Python 3.x
- `pywin32` library

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/caffeine-windows.git
cd caffeine-windows
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the script:
```bash
python caffeine.py
```

2. On first run:
   - A setup window will appear
   - For each day, you can:
     - Check/uncheck to enable/disable that day
     - Set start and end times for the active window
   - Click "Save and Start" to begin

3. After initial setup:
   - The script will run in the background
   - Console will show current status and next active window
   - Settings are saved and will be loaded automatically on next run

## Console Output

The script provides real-time status updates in the console:
- Current active/inactive status
- Next scheduled active window
- End time of current active window
- Configuration details at startup

## How it Works

- During active windows, the script:
  - Prevents system sleep
  - Keeps screen active
  - Simulates minimal activity to maintain online status
- Outside active windows:
  - System returns to normal power management
  - No interference with regular sleep/lock settings

## Configuration

Settings are stored in `caffeine_settings.json` and can be modified by running the script again.

## Stopping the Script

- Press Ctrl+C in the console window to stop the script
- Close the console window
- System will return to normal power management immediately

## License

MIT License - feel free to modify and use as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.