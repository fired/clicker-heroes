import pyautogui
import cv2
import numpy as np
import time
import threading
import keyboard
import mss
from colorama import Fore, Style
import datetime
import uuid
import os

# Disable fail-safe for debugging (not recommended for production)
pyautogui.FAILSAFE = False

# Global flags
stop_flag = False
pause_flag = False
continuous_click_flag = False  # Flag to control continuous clicking
object_detected_flag = False  # Flag to indicate object detection process
click_count = 0  # Click counter

def get_coordinates(prompt):
    """Prompt the user to move the mouse to the specified position and press 's'."""
    print(prompt)
    while True:
        if keyboard.is_pressed('s'):
            x, y = pyautogui.position()
            print(f"Position saved at: ({x}, {y})")
            while keyboard.is_pressed('s'):
                time.sleep(0.1)  # Wait for the key to be released
            return x, y
        time.sleep(0.1)  # Add a small delay to prevent high CPU usage

def get_area_coordinates():
    """Prompt the user to move the mouse to the top-left and bottom-right corners of the area."""
    while True:
        top_left = get_coordinates("Move your mouse to the top-left corner of the area and press 's'.")
        bottom_right = get_coordinates("Now, move your mouse to the bottom-right corner of the area and press 's'.")
        
        if top_left != bottom_right:
            break
        else:
            print("Invalid area. The top-left and bottom-right corners cannot be the same. Please try again.")
    return top_left, bottom_right

def continuous_clicking(x, y):
    """Continuously click at the given coordinates every 100 ms."""
    global stop_flag, pause_flag, continuous_click_flag
    next_click_time = time.perf_counter()
    while not stop_flag:
        if continuous_click_flag and not pause_flag:
            pyautogui.click(x, y)
            next_click_time += 0.1  # Schedule next click in 100 ms
            sleep_time = next_click_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
        else:
            time.sleep(0.1)  # Add a small delay to prevent high CPU usage

def locate_and_click(template_path, area_top_left, area_bottom_right, click_pos, min_match_count, start_time):
    """Locate the object on the screen using SIFT and click if found."""
    global stop_flag, pause_flag, object_detected_flag, click_count
    # Initialize the SIFT detector
    sift = cv2.SIFT_create()

    # Load the template image
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"Error: Could not load template image from {template_path}")
        return
    kp_template, des_template = sift.detectAndCompute(template, None)

    if des_template is None:
        print("Error: No descriptors found in the template image.")
        return
    
    # Create the matches directory if it doesn't exist
    if not os.path.exists('matches'):
        os.makedirs('matches')

    with mss.mss() as sct:
        while not stop_flag:
            if not pause_flag:
                object_detected_flag = True
                # Capture the specified area of the screen
                region = {
                    "top": int(area_top_left[1]),
                    "left": int(area_top_left[0]),
                    "width": int(area_bottom_right[0] - area_top_left[0]),
                    "height": int(area_bottom_right[1] - area_top_left[1])
                }
                if region["width"] <= 0 or region["height"] <= 0:
                    print("Invalid region dimensions. Please restart and set a valid area.")
                    break

                screenshot = np.array(sct.grab(region))
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

                # Detect keypoints and descriptors in the screenshot
                kp_screenshot, des_screenshot = sift.detectAndCompute(gray_screenshot, None)

                if des_screenshot is None:
                    print("Warning: No descriptors found in the screenshot.")
                    continue

                # Use FLANN-based matcher to find matches
                index_params = dict(algorithm=1, trees=5)
                search_params = dict(checks=50)
                flann = cv2.FlannBasedMatcher(index_params, search_params)
                matches = flann.knnMatch(des_template, des_screenshot, k=2)

                # Store all good matches using the Lowe's ratio test
                good_matches = []
                for m, n in matches:
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)

                # If enough matches are found, click the center of the detected object
                if len(good_matches) > min_match_count:
                    src_pts = np.float32([kp_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_screenshot[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                    if M is not None:
                        h, w = template.shape
                        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                        dst = cv2.perspectiveTransform(pts, M)

                        # Calculate center of detected object in the full screen coordinates
                        center_x = int(np.mean(dst[:, 0, 0])) + area_top_left[0]
                        center_y = int(np.mean(dst[:, 0, 1])) + area_top_left[1]

                        # Debugging output
                        # print(f"Clicking at ({center_x}, {center_y})")
                        
                        # Save the current cursor position
                        current_pos = pyautogui.position()
                        
                        # Click the center of the detected object
                        pyautogui.click(center_x, center_y)
                        click_count += 1  # Increment the click counter
                        
                        # Draw matches for debugging
                        img_matches = cv2.drawMatchesKnn(template, kp_template, gray_screenshot, kp_screenshot, [good_matches], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                        match_filename = os.path.join('matches', f"matches_{uuid.uuid4().hex}.png")
                        cv2.imwrite(match_filename, img_matches)
                        
                        # Move the cursor back to the saved click position
                        pyautogui.moveTo(click_pos)
                #     else:
                #         print("Warning: Homography could not be computed.")
                # else:
                #     print("Not enough matches found.")
                time.sleep(1)  # Check for the object every 1.5 seconds
                object_detected_flag = False

def check_for_stop_pause():
    """Check for the stop, pause, and toggle continuous clicking key presses."""
    global stop_flag, pause_flag, continuous_click_flag
    while not stop_flag:
        if keyboard.is_pressed('|'):
            stop_flag = True
            print("Stopping...")
        elif keyboard.is_pressed('{'):
            pause_flag = not pause_flag
            if pause_flag:
                print("Paused")
            else:
                print("Resumed")
            time.sleep(0.5)  # Debounce the key press
        elif keyboard.is_pressed('}'):
            continuous_click_flag = not continuous_click_flag
            if continuous_click_flag:
                print("Continuous clicking enabled")
            else:
                print("Continuous clicking disabled")
            time.sleep(0.5)  # Debounce the key press
        time.sleep(0.1)  # Add a small delay to prevent high CPU usage

def keep_awake(stats_pos, click_pos):
    """Click at the top-left coordinates every minute to keep the computer awake and return to the saved position."""
    global stop_flag, pause_flag, object_detected_flag
    while not stop_flag:
        if not pause_flag and not object_detected_flag:
            # Debugging output
            # print(f"Keep awake click at ({top_left[0]}, {top_left[1]})")
    
            # Save the current cursor position
            current_pos = pyautogui.position()
            
            # Click at the top-left corner
            # pyautogui.click(top_left[0] + 10, top_left[1] + 10)
            pyautogui.click(stats_pos[0], stats_pos[1])
            debug_out = pyautogui.position()
            # print(f"Keep Awake Click: {debug_out}")
            
            # Move back to the saved click position
            pyautogui.moveTo(click_pos[0], click_pos[1])
            
            time.sleep(60)

def update_console(start_time):
    """Update the console with the click count and runtime every second."""
    global stop_flag, click_count
    while not stop_flag:
        elapsed_time = datetime.datetime.now() - start_time
        print(f"\rObject found and clicked: {click_count} | Runtime: {elapsed_time}", end='')
        time.sleep(1)

def main():
    global stop_flag
    template_path = 'object4.png'  # Path to the image of the object to detect
    min_match_count = 10  # Minimum number of matches required to consider the object detected

    # Get the area coordinates for object detection from the user
    area_top_left, area_bottom_right = get_area_coordinates()

    # Get the clicking coordinates from the user
    click_x, click_y = get_coordinates("Move your mouse to the position where it should click and press 's'.")
    click_pos = (click_x, click_y)
    # print(f"Starting continuous clicking at: {click_pos}")

    stats_x, stats_y = get_coordinates("Move your mouse to the stats tab and click 's'.")
    stats_pos = (stats_x, stats_y)

    # Start continuous clicking in a separate thread
    click_thread = threading.Thread(target=continuous_clicking, args=(click_pos[0], click_pos[1]))
    click_thread.daemon = True
    click_thread.start()

    # Start the stop and pause key listener in a separate thread
    stop_pause_thread = threading.Thread(target=check_for_stop_pause)
    stop_pause_thread.daemon = True
    stop_pause_thread.start()

    # Start the keep awake function in a separate thread, passing top-left coordinates and click position
    keep_awake_thread = threading.Thread(target=keep_awake, args=(stats_pos, click_pos))
    keep_awake_thread.daemon = True
    keep_awake_thread.start()

    # Start the runtime timer
    start_time = datetime.datetime.now()

    # Start the console update function in a separate thread
    console_update_thread = threading.Thread(target=update_console, args=(start_time,))
    console_update_thread.daemon = True
    console_update_thread.start()

    # Start object detection and clicking in the main thread
    locate_and_click(template_path, area_top_left, area_bottom_right, click_pos, min_match_count, start_time)

    click_thread.join()
    stop_pause_thread.join()
    keep_awake_thread.join()
    console_update_thread.join()

if __name__ == "__main__":
    main()
