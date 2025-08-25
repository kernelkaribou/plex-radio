import os
import requests
import subprocess
import time
import json
import sys
import threading
import select
from urllib.parse import urlparse

class PlexRadioClient:
    def __init__(self, api_base_url="http://localhost:5000"):
        self.api_base_url = api_base_url
        self.current_process = None
        self.input_thread = None
        self.should_stop = False
        self.should_change_channel = False
        self.next_channel = None
        self.current_channel = 0
        self.channels = []
        
    def get_current_song(self, channel=None):
        """Get current song information from the API"""
        try:
            if channel is not None:
                url = f"{self.api_base_url}/current-song/{channel}"
            else:
                url = f"{self.api_base_url}/current-song"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data")
            else:
                print(f"API Error: {data.get('error', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
    
    def get_channels(self):
        """Get available channels from the API"""
        try:
            url = f"{self.api_base_url}/channels"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", [])
            else:
                print(f"API Error: {data.get('error', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return []
    
    def check_ffplay_available(self):
        """Check if ffplay is available in the system"""
        try:
            subprocess.run(['ffplay', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def stop_current_playback(self):
        """Stop current ffplay process if running"""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            print("Stopped current playback")
    
    def handle_keyboard_input(self):
        """Handle keyboard input in a separate thread"""
        print("\nKeyboard Commands:")
        print("  q - Quit")
        print("  n - Next channel")
        print("  p - Previous channel")
        print("  0-9 - Switch to channel number")
        print("  i - Show current channel info")
        print("  h - Show this help")
        
        while not self.should_stop:
            try:
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    command = sys.stdin.readline().strip().lower()
                    
                    if command == 'q':
                        print("Quitting...")
                        self.should_stop = True
                        self.stop_current_playback()
                        break
                    elif command == 'n':
                        # Next channel
                        next_channel = (self.current_channel + 1) % len(self.channels)
                        self.change_channel(next_channel)
                    elif command == 'p':
                        # Previous channel
                        prev_channel = (self.current_channel - 1) % len(self.channels)
                        self.change_channel(prev_channel)
                    elif command.isdigit():
                        # Direct channel selection
                        channel_num = int(command)
                        if 0 <= channel_num < len(self.channels):
                            self.change_channel(channel_num)
                        else:
                            print(f"Invalid channel number. Available channels: 0-{len(self.channels)-1}")
                    elif command == 'i':
                        self.show_current_channel_info()
                    elif command == 'h':
                        self.show_help()
                    
            except Exception as e:
                if not self.should_stop:
                    print(f"Input handling error: {e}")
            
            time.sleep(0.1)
    
    def change_channel(self, channel_num):
        """Change to a specific channel"""
        if 0 <= channel_num < len(self.channels):
            print(f"\nSwitching to channel {channel_num}: {self.channels[channel_num]['name']}")
            self.next_channel = channel_num
            self.should_change_channel = True
            self.stop_current_playback()
        else:
            print(f"Invalid channel number: {channel_num}")
    
    def show_current_channel_info(self):
        """Show current channel and available channels"""
        if self.channels:
            print(f"\nCurrent Channel: {self.current_channel} - {self.channels[self.current_channel]['name']}")
            print("\nAvailable Channels:")
            for i, channel in enumerate(self.channels):
                marker = " *** CURRENT ***" if i == self.current_channel else ""
                print(f"  {i}: {channel['name']} - {channel['playlist']}{marker}")
        else:
            print("No channels available")
    
    def show_help(self):
        """Show keyboard commands"""
        print("\nKeyboard Commands:")
        print("  q - Quit")
        print("  n - Next channel")
        print("  p - Previous channel")
        print("  0-9 - Switch to channel number")
        print("  i - Show current channel info")
        print("  h - Show this help")

    def play_song(self, song_info, start_time=None):
        """Play a song using ffplay"""
        if not song_info:
            print("No song information provided")
            return False
        
        if not self.check_ffplay_available():
            print("Error: ffplay is not available. Please install ffmpeg.")
            print("Ubuntu/Debian: sudo apt install ffmpeg")
            print("macOS: brew install ffmpeg")
            return False
        
        media_url = song_info.get("media_link")
        if not media_url:
            print("No media link found in song info")
            return False
        
        # Stop any current playback
        self.stop_current_playback()
        
        # Prepare ffplay command
        cmd = ['ffplay', '-nodisp', '-autoexit']
        
        # Add start time if provided
        if start_time is not None:
            cmd.extend(['-ss', str(start_time)])
        elif song_info.get("start_time"):
            cmd.extend(['-ss', str(song_info["start_time"])])
        
        # Add the media URL
        cmd.append(media_url)
        
        try:
            print(f"Playing: {song_info.get('title', 'Unknown')} by {song_info.get('artist', 'Unknown')}")
            print(f"Album: {song_info.get('album', 'Unknown')}")
            if song_info.get("start_time"):
                print(f"Starting at: {song_info['start_time']} seconds")
            
            # Start ffplay process (non-blocking)
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"ffplay error: {e}")
            return False

    def radio_mode(self, starting_channel=0, check_interval=30):
        """Interactive radio mode with channel switching"""
        # Load available channels
        self.channels = self.get_channels()
        if not self.channels:
            print("No channels available")
            return
        
        # Set starting channel
        if 0 <= starting_channel < len(self.channels):
            self.current_channel = starting_channel
        else:
            self.current_channel = 0
            
        print(f"Starting radio mode on channel {self.current_channel}: {self.channels[self.current_channel]['name']}")
        print(f"Checking for song changes every {check_interval} seconds")
        
        # Initialize control flags
        self.should_stop = False
        self.should_change_channel = False
        self.next_channel = None
        
        # Start keyboard input handler thread
        self.input_thread = threading.Thread(target=self.handle_keyboard_input, daemon=True)
        self.input_thread.start()
        
        last_song_title = None
        
        try:
            while not self.should_stop:
                # Handle channel change
                if self.should_change_channel and self.next_channel is not None:
                    self.current_channel = self.next_channel
                    self.should_change_channel = False
                    self.next_channel = None
                    last_song_title = None  # Force new song fetch
                    print(f"Switched to channel {self.current_channel}: {self.channels[self.current_channel]['name']}")
                
                # Get current song for current channel
                song_info = self.get_current_song(self.current_channel)
                
                if song_info:
                    current_title = song_info.get("title")
                    
                    # Check if the song has changed or if we need to start playing
                    if current_title != last_song_title:
                        print(f"\n--- Channel {self.current_channel}: {self.channels[self.current_channel]['name']} ---")
                        if self.play_song(song_info):
                            last_song_title = current_title

                # Wait before checking again, but check control flags frequently
                for _ in range(check_interval * 10):  # Check every 0.1 seconds
                    if self.should_stop or self.should_change_channel:
                        break
                    # Check if current process ended (song finished)
                    if self.current_process and self.current_process.poll() is not None:
                        print("Song ended, checking for next song...")
                        if self.play_song(song_info.get("next_song")):
                            last_song_title = song_info.get("next_song").get("title")
                    time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nReceived Ctrl+C, stopping...")
        finally:
            print("Stopping radio...")
            self.should_stop = True
            self.stop_current_playback()
            if self.input_thread and self.input_thread.is_alive():
                self.input_thread.join(timeout=1)

def main():
    """Main function to demonstrate the client"""
    client = PlexRadioClient()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "channels":
            # List available channels
            print("Available channels:")
            channels = client.get_channels()
            for i, channel in enumerate(channels):
                print(f"  {i}: {channel.get('name')} - {channel.get('playlist')}")
        
        elif command == "radio":
            # Interactive radio mode
            channel = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            client.radio_mode(channel)
        
        elif command == "info":
            # Just get song info without playing
            channel = int(sys.argv[2]) if len(sys.argv) > 2 else None
            song_info = client.get_current_song(channel)
            if song_info:
                print(json.dumps(song_info, indent=2))
        
        else:
            print("Unknown command")
            print_usage()
    
    else:
        print_usage()

def print_usage():
    """Print usage instructions"""
    print("Plex Radio Client")
    print("Usage:")
    print("  python example_client.py channels          - List available channels")
    print("  python example_client.py info [channel]    - Get current song info")
    print("  python example_client.py radio [channel]   - Interactive radio mode")
    print()
    print("Radio Mode Commands:")
    print("  q + Enter - Quit")
    print("  n + Enter - Next channel")
    print("  p + Enter - Previous channel")
    print("  0-9 + Enter - Switch to channel number")
    print("  i + Enter - Show current channel info")
    print("  h + Enter - Show help")
    print()
    print("Examples:")
    print("  python example_client.py channels")
    print("  python example_client.py radio 1")

if __name__ == "__main__":
    main()