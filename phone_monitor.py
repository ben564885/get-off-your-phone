import cv2
import numpy as np
import time
import random
import os
from dotenv import load_dotenv
from AppKit import NSWorkspace
import subprocess
import webbrowser
import base64
import requests

# Load environment variables from .env file
load_dotenv()

class PhoneDetectionMonitor:
    def __init__(self, youtube_urls, cooldown_seconds=30, check_browser=True, check_phone=True):
        """
        Initialize the phone detection monitor.
        
        Args:
            youtube_urls: List of YouTube URLs to open when distraction is detected
            cooldown_seconds: Seconds to wait before opening URL again
            check_browser: Whether to monitor Safari tabs
            check_phone: Whether to use AI camera detection
        """
        self.youtube_urls = youtube_urls if isinstance(youtube_urls, list) else [youtube_urls]
        self.cooldown = cooldown_seconds
        self.check_browser = check_browser
        self.check_phone = check_phone
        self.last_triggered = 0
        
        # Roboflow config
        self.rf_api_key = os.getenv("ROBOFLOW_API_KEY")
        self.rf_model_id = "mobile-phone-detection-2vads/1"
        self.rf_confidence = 0.4  # Minimum confidence
        
        if not self.rf_api_key:
            print("⚠️  WARNING: ROBOFLOW_API_KEY not found in environment!")
            print("Please create a .env file with ROBOFLOW_API_KEY=your_key_here")
        
        if self.check_phone:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            
            # Check if camera opened successfully
            if not self.cap.isOpened():
                print("⚠️  ERROR: Could not open camera!")
                print("Make sure:")
                print("1. Terminal has Camera permission in System Settings")
                print("2. No other app is using the camera")
                print("3. Try camera index 1 if 0 doesn't work")
            else:
                print("✓ Camera initialized successfully")
        else:
            self.cap = None
            print("📷 Camera detection disabled")
        
        # Track Instagram detection
        self.instagram_open = False
        
    def detect_phone_ai(self, frame):
        """
        Detect phone using Roboflow Inference API.
        Returns True if a phone is detected with high confidence.
        """
        try:
            # Resize frame to speed up upload/processing
            small_frame = cv2.resize(frame, (640, 480))
            
            # Encode frame as base64
            _, buffer = cv2.imencode('.jpg', small_frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            
            # Call Roboflow API
            url = f"https://detect.roboflow.com/{self.rf_model_id}?api_key={self.rf_api_key}"
            response = requests.post(url, data=img_str, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=5)
            
            if response.status_code == 200:
                predictions = response.json().get('predictions', [])
                
                # Check for phone detection
                for pred in predictions:
                    if pred['confidence'] >= self.rf_confidence:
                        # Draw bounding box on the original frame
                        # Scale coordinates back to original frame size if needed
                        # (But we are just using it for detection for now)
                        return True, pred['confidence']
            else:
                print(f"Roboflow API Error: {response.text}")
                
            return False, 0
        except Exception as e:
            print(f"Error in Roboflow detection: {e}")
            return False, 0
    
    def is_instagram_open(self):
        """
        Check if Instagram.com is open in Safari using AppleScript.
        This method doesn't require Screen Recording permission.
        """
        try:
            # AppleScript to check Safari tabs
            applescript = '''
            tell application "Safari"
                if it is running then
                    repeat with w in windows
                        repeat with t in tabs of w
                            try
                                set tabURL to URL of t
                                if tabURL contains "instagram.com" then
                                    return "FOUND"
                                end if
                            end try
                        end repeat
                    end repeat
                end if
            end tell
            return "NOT_FOUND"
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output == "FOUND":
                    print("✓✓✓ INSTAGRAM DETECTED in Safari!")
                    return True
            
            return False
            
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"Error checking Safari: {e}")
            return False
            
    def close_distraction_tabs(self):
        """
        Actively close any Safari tabs containing distraction sites like Instagram.
        """
        try:
            applescript = '''
            tell application "Safari"
                if it is running then
                    repeat with w in windows
                        repeat with t in tabs of w
                            try
                                set tabURL to URL of t
                                if tabURL contains "instagram.com" then
                                    close t
                                end if
                            end try
                        end repeat
                    end repeat
                end if
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript], timeout=5)
            print("🛑 Closed distraction tabs in Safari!")
        except Exception as e:
            print(f"Error closing tabs: {e}")

    def is_youtube_playing(self):
        """
        Check if any YouTube video is already open in Safari.
        """
        try:
            applescript = '''
            tell application "Safari"
                if it is running then
                    repeat with w in windows
                        repeat with t in tabs of w
                            try
                                set tabURL to URL of t
                                if tabURL contains "youtube.com/watch" then
                                    return "FOUND"
                                end if
                            end try
                        end repeat
                    end repeat
                end if
            end tell
            return "NOT_FOUND"
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                return result.stdout.strip() == "FOUND"
            
            return False
            
        except:
            return False
    
    def open_youtube_video(self):
        """Open the YouTube video in a new browser tab."""
        try:
            # Check if a video is already playing
            if self.is_youtube_playing():
                print("📺 A YouTube video is already playing. Skipping new tab.")
                return

            # Use the first URL if only one provided, otherwise pick random
            url = random.choice(self.youtube_urls)
            
            print(f"--- Attempting to open: {url}")
            # Try webbrowser first
            success = webbrowser.open(url)
            
            # If webbrowser fails or on macOS, try the 'open' command as it's more reliable
            if not success:
                subprocess.run(['open', url], check=True)
            
            print(f"🎥 Opening YouTube reminder video!")
            self.last_triggered = time.time()
        except Exception as e:
            print(f"Error opening YouTube: {e}")
            # Final attempt with direct open if everything else failed
            try:
                if self.is_youtube_playing():
                     return
                fallback_url = random.choice(self.youtube_urls)
                subprocess.run(['open', fallback_url])
            except:
                pass
    
    def run(self):
        """Main monitoring loop."""
        print("📷 Starting phone detection monitor...")
        monitoring_desc = []
        if self.check_phone: monitoring_desc.append("AI Phone Detection")
        if self.check_browser: monitoring_desc.append("Instagram in Safari")
        
        print(f"🔍 Monitoring for: {' OR '.join(monitoring_desc)}")
        print("📺 Will open YouTube video when distraction detected")
        if self.check_phone:
            print("💡 TIP: Show your phone to the camera to trigger")
        print("=" * 60)
        
        # Check if camera is working if phone check is enabled
        if self.check_phone:
            if not self.cap or not self.cap.isOpened():
                print("❌ CRITICAL ERROR: Camera is not available!")
                print("\nPlease check:")
                print("1. System Settings → Privacy & Security → Camera")
                print("2. Make sure Terminal has camera permission")
                print("3. Close any other apps using the camera")
                return
            print("✓ Camera is active")
            print("=" * 60)
            print("\nPress 'q' in the camera window to quit\n")
        else:
            print("✓ Running in Browser-only mode")
            print("=" * 60)
            print("\nPress Ctrl+C in terminal to quit\n")
        
        check_counter = 0
        
        while True:
            frame = None
            if self.check_phone:
                ret, frame = self.cap.read()
                if not ret:
                    print("ERROR: Failed to read from camera")
                    break
                # Flip frame for mirror view
                frame = cv2.flip(frame, 1)
            
            # Detect Instagram every 30 frames/iterations
            instagram_detected = False
            # Detect Phone AI every 15 frames/iterations
            phone_detected = False
            phone_confidence = 0
            
            check_counter += 1
            if self.check_browser and check_counter % 30 == 0:
                instagram_detected = self.is_instagram_open()
                if instagram_detected:
                    self.close_distraction_tabs()
                print("-" * 40)
            
            if self.check_phone and check_counter % 15 == 0:
                phone_detected, phone_confidence = self.detect_phone_ai(frame)
                if phone_detected:
                    print(f"✓✓✓ PHONE DETECTED! (Conf: {phone_confidence:.2f})")
            
            if check_counter >= 30:
                check_counter = 0

            # Display detection status if camera is on
            if self.check_phone and frame is not None:
                if phone_detected:
                    cv2.putText(frame, f"📱 PHONE! ({int(phone_confidence*100)}%)", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if instagram_detected:
                    cv2.putText(frame, "📸 Instagram open!", (10, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                    self.instagram_open = True
                else:
                    self.instagram_open = False
            
            # Trigger YouTube video
            current_time = time.time()
            time_since_last = current_time - self.last_triggered
            should_trigger_reason = ""
            
            if instagram_detected:
                should_trigger_reason = "Instagram detected"
            elif phone_detected:
                should_trigger_reason = f"Phone detected ({int(phone_confidence*100)}%)"
            
            if should_trigger_reason:
                print(f"DEBUG: Distraction found ({should_trigger_reason}). Cooldown status: {time_since_last:.1f}s / {self.cooldown}s")
                
                if time_since_last > self.cooldown:
                    print("\n" + "!" * 60)
                    print(f"🚨 TRIGGER ACTIVATED! Reason: {should_trigger_reason}")
                    print("!" * 60 + "\n")
                    self.open_youtube_video()
                else:
                    print(f"DEBUG: Trigger blocked by cooldown ({int(self.cooldown - time_since_last)}s remaining)")
            
            # Show cooldown status on screen if camera is active
            if self.check_phone and frame is not None:
                time_until_ready = max(0, self.cooldown - (current_time - self.last_triggered))
                if time_until_ready > 0:
                    cv2.putText(frame, f"Ready in: {int(time_until_ready)}s", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                cv2.imshow('Phone Detection Monitor', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # In browser-only mode, just sleep a bit to avoid CPU hogging
                time.sleep(0.03)
        
        self.cleanup()
    
    def cleanup(self):
        """Release resources."""
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # The specific YouTube video URL to open as a reminder
    YOUTUBE_URLS = [
        "https://www.youtube.com/watch?v=9qQjaqKG0Ro"
    ]
    
    print("\n" + "="*40)
    print("      GET OFF YOUR PHONE MONITOR")
    print("="*40)
    print("Select monitoring mode:")
    print("1. Browser Check Only (Safari)")
    print("2. Phone Check Only (AI Camera)")
    print("3. Both (Recommended)")
    
    choice = input("\nEnter choice (1-3) [default: 3]: ").strip()
    
    b_check, p_check = True, True
    if choice == "1":
        b_check, p_check = True, False
    elif choice == "2":
        b_check, p_check = False, True
        
    monitor = PhoneDetectionMonitor(
        youtube_urls=YOUTUBE_URLS,
        cooldown_seconds=10,
        check_browser=b_check,
        check_phone=p_check
    )
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n👋 Exiting monitor...")
    finally:
        if monitor.check_phone:
            monitor.cleanup()
