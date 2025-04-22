#!/usr/bin/env python3

"""
InputCollector module for handling user input collection in the YouTube AI Content Generator.
"""

from typing import Dict, Any
from datetime import datetime, timedelta

class InputCollector:
    """Handles collection of user input for video generation."""
    
    def __init__(self):
        """Initialize the InputCollector."""
        self.required_fields = {
            'channel': ['name', 'description', 'target_audience'],
            'character': ['name', 'description', 'personality'],
            'video': ['type', 'length', 'genre'],
            'schedule': ['frequency', 'preferred_time']
        }

    def get_channel_info(self) -> Dict[str, str]:
        """Collect channel information from user."""
        print("\n=== Channel Information ===")
        return {
            'name': input("Enter channel name: ").strip(),
            'description': input("Enter channel description: ").strip(),
            'target_audience': input("Enter target audience: ").strip(),
            'niche': input("Enter channel niche/category: ").strip()
        }

    def get_character_details(self) -> Dict[str, str]:
        """Collect main character details."""
        print("\n=== Character Details ===")
        return {
            'name': input("Enter character name: ").strip(),
            'description': input("Enter character description: ").strip(),
            'personality': input("Enter character personality traits: ").strip(),
            'voice_type': input("Enter preferred voice type (e.g., energetic, calm): ").strip()
        }

    def get_video_preferences(self) -> Dict[str, Any]:
        """Collect video preferences."""
        print("\n=== Video Preferences ===")
        
        # Get video type
        while True:
            video_type = input("Enter video type (short/long): ").strip().lower()
            if video_type in ['short', 'long']:
                break
            print("Please enter either 'short' or 'long'")

        # Get video length based on type
        while True:
            try:
                if video_type == 'short':
                    length = float(input("Enter video length in seconds (15-60): "))
                    if 15 <= length <= 60:
                        break
                else:
                    length = float(input("Enter video length in minutes (1-60): "))
                    if 1 <= length <= 60:
                        break
                print("Please enter a valid length")
            except ValueError:
                print("Please enter a number")

        return {
            'type': video_type,
            'length': length,
            'genre': input("Enter video genre (e.g., educational, entertainment): ").strip(),
            'style': input("Enter visual style (e.g., 3D animation, cartoon): ").strip(),
            'music_type': input("Enter preferred music type: ").strip()
        }

    def get_upload_schedule(self) -> Dict[str, Any]:
        """Collect upload schedule preferences."""
        print("\n=== Upload Schedule ===")
        
        # Get upload frequency
        while True:
            frequency = input("Enter upload frequency (daily/weekly/monthly): ").strip().lower()
            if frequency in ['daily', 'weekly', 'monthly']:
                break
            print("Please enter a valid frequency")

        # Get preferred upload time
        while True:
            try:
                time_str = input("Enter preferred upload time (HH:MM in 24-hour format): ").strip()
                preferred_time = datetime.strptime(time_str, "%H:%M").time()
                break
            except ValueError:
                print("Please enter time in HH:MM format (e.g., 14:30)")

        # Get timezone offset
        while True:
            try:
                tz_offset = float(input("Enter timezone offset from UTC (e.g., -5 for EST): "))
                if -12 <= tz_offset <= 14:
                    break
                print("Please enter a valid timezone offset (-12 to +14)")
            except ValueError:
                print("Please enter a number")

        return {
            'frequency': frequency,
            'preferred_time': preferred_time.strftime("%H:%M"),
            'timezone_offset': tz_offset,
            'start_date': datetime.now().strftime("%Y-%m-%d")
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate that all required fields are present and non-empty.
        
        Args:
            input_data: Dictionary containing user input
            
        Returns:
            bool: True if all required fields are present and non-empty
        """
        for category, fields in self.required_fields.items():
            if category not in input_data:
                return False
            for field in fields:
                if field not in input_data[category] or not input_data[category][field]:
                    return False
        return True 