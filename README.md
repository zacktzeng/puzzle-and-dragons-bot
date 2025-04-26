# PAD Auto Bot

A basic Puzzle & Dragons automation bot using Appium, OpenCV, and scrcpy.

## How It Works

- Connects to your Android device using Appium.
- Detects the orb grid using template matching.
- Calculates the best swipe path for max combos.
- Drags the orbs on the screen automatically.
- Waits for attack animations to complete by monitoring orb brightness.

## Setup

1. Create and activate a virtual environment (optional but recommended):
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip3.11 install -r requirements.txt
   brew install scrcpy
   ```

3. Start Appium server:
   ```bash
   appium
   ```

4. Connect your Android device with USB debugging enabled.

5. Run the bot:
   ```bash
   bash start.sh
   ```

   Optional flags:
   - Start scrcpy manually:
     ```bash
     bash start.sh --scrcpy
     ```
   - Limit number of rounds:
     ```bash
     bash start.sh --round 5
     ```

## Folder Structure

```
pad-bot-appium/
├── bot.py
├── bot_core.py
├── start.sh
├── requirements.txt
├── README.md
└── screenshots/
    ├── red_orb.png
    ├── blue_orb.png
    ├── green_orb.png
    ├── light_orb.png
    ├── dark_orb.png
    ├── heart_orb.png
    └── clear_screen.png
```

## Notes

- Make sure orb screenshots (`red_orb.png`, `blue_orb.png`, etc.) are placed inside the `screenshots/` folder.
