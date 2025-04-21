#!/usr/bin/env python3

"""Example script demonstrating the usage of the MusicGenerator class."""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_generation.music_generator import MusicGenerator
from src.utils.config import Config

async def main():
    # Initialize configuration and MusicGenerator
    config = Config('config.yaml')
    output_dir = Path("output/audio")
    generator = MusicGenerator(str(output_dir), config)
    
    try:
        # Generate background music
        music_path = await generator.generate_background_music(
            prompt="Upbeat fantasy acoustic guitar, happy and adventurous",
            output_filename="adventure_background"
        )
        print(f"Generated background music: {music_path}")
        
        # Generate various sound effects
        # Magical effects
        magic_sfx = await generator.generate_sfx(
            category='magic',
            count=3
        )
        print(f"Generated magical effects: {magic_sfx}")
        
        # Nature sounds
        nature_sfx = await generator.generate_sfx(
            category='nature',
            count=3
        )
        print(f"Generated nature sounds: {nature_sfx}")
        
        # Action sounds
        action_sfx = await generator.generate_sfx(
            category='action',
            count=3
        )
        print(f"Generated action sounds: {action_sfx}")
        
        # Clean up any temporary files
        generator.cleanup_temp_files()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 