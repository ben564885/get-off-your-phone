# Get Off Your Phone! 📱🚀

A Python-based productivity tool that helps you stay focused by detecting distractions and reminding you to get back to work with randomized YouTube videos.

## Features
- **AI-Powered Phone Detection**: Uses a Roboflow AI model to specifically detect when you're holding your phone.
- **Instagram Monitoring**: Automatically detects if you have Instagram open in Safari (macOS only).
- **Randomized Reminders**: Opens a random video from a curated list of YouTube reminders to keep things fresh.
- **Secure Configuration**: Uses environment variables to keep your API keys private.

## Setup

### 1. Prerequisites
- macOS (for Instagram detection and `open` command support)
- Python 3.x
- A Roboflow API Key (get one at [roboflow.com](https://roboflow.com))

### 2. Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/ben564885/get-off-your-phone.git
   cd get-off-your-phone
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install opencv-python numpy requests python-dotenv pyobjc-framework-Cocoa
   ```

### 3. Configuration
Create a `.env` file in the project root and add your Roboflow API key:
```env
ROBOFLOW_API_KEY=your_api_key_here
```

## Usage
Run the monitor:
```bash
python phone_monitor.py
```

- **Quit**: Press `q` while the camera window is focused.
- **Cooldown**: There is a default 10-second cooldown between triggers to prevent spamming.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
