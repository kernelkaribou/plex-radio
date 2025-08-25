from plexapi import playlist
import datetime
import random

class DailyPlaylist:
    def __init__(self, current_playlist):
        self.current_playlist = current_playlist.items()
        self.creation_time = datetime.datetime.now()
        self.playlist_items = self.generate_playlist()

    def generate_playlist(self):
        """Generate a shuffled playlist that is limited to 24 hours long"""
        random.shuffle(self.current_playlist)

        limited_playlist = []
        # Limit the playlist to 24 hours
        for item in self.current_playlist:
            total_duration = sum(item.duration for item in limited_playlist)
            if total_duration < 24 * 60 * 60 * 1000:  # 24 hours in milliseconds
                limited_playlist.append(item)

        return limited_playlist
    
