# Clicker Heroes Automation Script

## Overview

This script is designed to automate mouse clicking tasks and object detection on the screen using Python. It is optimized for use with the Clicker Heroes game, running in full-screen mode, to click on various clickable objects to help you collect gems and other rewards.

### Key Features

1. **Continuous Clicking**: Clicks at specified coordinates continuously.
2. **Object Detection and Clicking**: Detects specified objects on the screen and clicks them if found.
3. **Keep Awake Functionality**: Simulates a click to keep the computer awake.
4. **Pause and Stop Controls**: Provides keyboard controls to pause, resume, and stop the script.
5. **Console Updates**: Displays real-time statistics in the console.

### Prerequisites

- Python 3.x installed.
- Required Python libraries installed. You can install them using pip:

  ```sh
  pip install pyautogui opencv-python numpy keyboard mss colorama
  ```

### Directory Structure

Ensure your project directory contains the following files:
- `opti.py` (the main script)
- `object4.png` (the template image for object detection)

## Usage

### Running the Script

1. **Navigate to the project directory**:

   ```sh
   cd path/to/your/project
   ```

2. **Run the script**:

   ```sh
   python opti.py
   ```

### Script Flow

1. **Prompt for Area Coordinates**:
   - The script will prompt you to move your mouse to the top-left corner of the area to monitor and press 's'.
   - Next, it will prompt you to move your mouse to the bottom-right corner of the area to monitor and press 's'.

2. **Prompt for Click Coordinates**:
   - The script will prompt you to move your mouse to the position where it should click and press 's'.

3. **Prompt for Stats Tab Coordinates**:
   - The script will prompt you to move your mouse to the stats tab position and press 's'.

4. **Start Automation**:
   - The script starts the continuous clicking, object detection, and keep awake functionalities in separate threads.
   - The console will display real-time statistics of the number of clicks and the runtime.

### Best Performance Tips

- Run Clicker Heroes in full-screen mode to ensure the script accurately captures and processes the screen area.
- Set the monitored area to cover the entire game screen for optimal object detection performance.

### Keyboard Controls

- Press `|` to stop the script.
- Press `{` to pause or resume the script.
- Press `}` to toggle continuous clicking on or off.

## Code Explanation

### Functions

- `get_coordinates(prompt)`: Prompts the user to move the mouse to a specified position and press 's' to save the coordinates.
- `get_area_coordinates()`: Prompts the user to set the top-left and bottom-right corners of the area to monitor.
- `continuous_clicking(x, y)`: Clicks at the given coordinates every 100 ms.
- `locate_and_click(template_path, area_top_left, area_bottom_right, click_pos, min_match_count, start_time)`: Detects the specified object on the screen and clicks it if found.
- `check_for_stop_pause()`: Checks for stop, pause, and toggle continuous clicking key presses.
- `keep_awake(stats_pos, click_pos)`: Simulates a click to keep the computer awake.
- `update_console(start_time)`: Updates the console with the click count and runtime every second.
- `main()`: The main function that orchestrates the script's flow.

### Multithreading

The script uses multithreading to run multiple tasks concurrently:
- Continuous clicking.
- Checking for stop and pause key presses.
- Keeping the computer awake.
- Updating the console.

### Object Detection

The script uses the SIFT (Scale-Invariant Feature Transform) algorithm to detect objects in the specified area:
- Captures the screen using `mss`.
- Detects keypoints and descriptors using SIFT.
- Matches the descriptors with the template image using FLANN-based matcher.
- If enough good matches are found, clicks the center of the detected object.
