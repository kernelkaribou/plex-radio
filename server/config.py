import yaml

class Config:
    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found, using defaults")
            return self.get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration if file doesn't exist"""
        return {
            'channels': [
                {'name': 'Maisie Radio', 'playlist': 'Maisie Power House'}
            ]
        }

    def get_plex_config(self):
        """Get Plex server configuration from config"""
        return self.config.get('plex', {})

    def get_channels(self):
        """Get list of channels from config"""
        return self.config.get('channels', [])
    
    def get_playlist_for_channel(self, channel_name):
        """Get playlist name for a specific channel"""
        for channel in self.get_channels():
            if channel['name'] == channel_name:
                return channel['playlist']
        return None

# Usage example
if __name__ == "__main__":
    config = Config('example.yaml')
    
    # Get all channels
    channels = config.get_channels()
    print("Available channels:")
    for channel in channels:
        print(f"  - {channel['name']}: {channel['playlist']}")
    
    # Get specific playlist
    playlist = config.get_playlist_for_channel("Maisie Radio")
    print(f"\nPlaylist for Maisie Radio: {playlist}")