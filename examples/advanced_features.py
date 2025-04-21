#!/usr/bin/env python3

"""
Advanced features examples for the YouTube AI Content Generator.
Demonstrates user input collection, music/SFX integration, advanced video editing,
and enhanced error handling.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.user_input.input_collector import InputCollector
from src.content_generation.music_generator import MusicGenerator
from src.content_generation.sfx_downloader import SFXDownloader
from src.video_creation.caption_generator import CaptionGenerator
from src.video_creation.thumbnail_generator import ThumbnailGenerator
from src.utils.retry_handler import RetryHandler
from src.utils.logger import setup_logger

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please create one based on config.yaml.example"
        )
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def user_input_example() -> Dict[str, Any]:
    """Example of collecting comprehensive user input"""
    print("\n=== User Input Collection Example ===")
    
    collector = InputCollector()
    
    # Collect channel details
    channel_info = collector.get_channel_info()
    print("\nChannel Information:")
    print(json.dumps(channel_info, indent=2))
    
    # Collect character details
    character = collector.get_character_details()
    print("\nCharacter Details:")
    print(json.dumps(character, indent=2))
    
    # Collect video preferences
    video_prefs = collector.get_video_preferences()
    print("\nVideo Preferences:")
    print(json.dumps(video_prefs, indent=2))
    
    # Get upload schedule
    schedule = collector.get_upload_schedule()
    print("\nUpload Schedule:")
    print(json.dumps(schedule, indent=2))
    
    return {
        'channel': channel_info,
        'character': character,
        'video_preferences': video_prefs,
        'upload_schedule': schedule
    }

def music_sfx_example(config: Dict[str, Any], script: str) -> Tuple[str, list]:
    """Example of music generation and SFX download"""
    print("\n=== Music and SFX Generation Example ===")
    
    # Generate background music
    music_gen = MusicGenerator(
        api_key=config['api_keys']['suno']['api_key'],
        temp_dir=config['system']['temp_dir']
    )
    
    background_music = music_gen.generate(
        prompt="Upbeat fantasy acoustic guitar, 90bpm, no vocals",
        duration=180  # 3 minutes
    )
    print(f"Generated background music: {background_music}")
    
    # Download relevant SFX
    sfx_downloader = SFXDownloader(
        api_key=config['api_keys']['pixabay']['api_key'],
        temp_dir=config['system']['temp_dir']
    )
    
    # Extract required sound effects from script
    sfx_paths = sfx_downloader.download_relevant_sfx(script)
    print("\nDownloaded SFX files:")
    for path in sfx_paths:
        print(f"- {path}")
    
    return background_music, sfx_paths

def advanced_video_editing_example(
    config: Dict[str, Any],
    video_path: str,
    script: str
) -> Tuple[str, str]:
    """Example of advanced video editing features"""
    print("\n=== Advanced Video Editing Example ===")
    
    # Generate SRT captions
    caption_gen = CaptionGenerator(
        temp_dir=config['system']['temp_dir']
    )
    
    srt_path = caption_gen.generate_captions(
        script=script,
        video_duration=180,  # 3 minutes
        include_pauses=True
    )
    print(f"Generated captions: {srt_path}")
    
    # Generate thumbnail
    thumbnail_gen = ThumbnailGenerator(
        temp_dir=config['system']['temp_dir']
    )
    
    thumbnail_path = thumbnail_gen.generate_thumbnail(
        video_path=video_path,
        title="The History of Pizza",
        dimensions=(1280, 720)
    )
    print(f"Generated thumbnail: {thumbnail_path}")
    
    return srt_path, thumbnail_path

def retry_example():
    """Example of retry mechanism for API calls"""
    print("\n=== Retry Handler Example ===")
    
    retry_handler = RetryHandler(
        max_retries=3,
        base_delay=1,
        max_delay=10
    )
    
    @retry_handler.retry_on_exception(
        exceptions=(ConnectionError, TimeoutError),
        should_retry=lambda e: isinstance(e, (ConnectionError, TimeoutError))
    )
    def example_api_call():
        # Simulate an API call that might fail
        import random
        if random.random() < 0.5:
            raise ConnectionError("API temporarily unavailable")
        return "Success!"
    
    try:
        result = example_api_call()
        print(f"API call result: {result}")
    except Exception as e:
        print(f"All retries failed: {str(e)}")

def main():
    """Run advanced feature examples"""
    try:
        # Setup logging
        logger = setup_logger(
            log_file="examples.log",
            console_level="INFO",
            file_level="DEBUG"
        )
        logger.info("Starting advanced features examples")
        
        # Load configuration
        config = load_config()
        
        # Run user input example
        user_input = user_input_example()
        logger.info("Collected user input successfully")
        
        # Example script for demonstration
        script = """
        [Scene 1] A traditional Italian pizzeria in Naples, circa 1889.
        The first Margherita pizza is being prepared for Queen Margherita.
        *Sound: Kitchen ambiance, fire crackling*
        
        [Scene 2] The pizza dough is tossed in the air with expert precision.
        *Sound: Whoosh effect, light background chatter*
        """
        
        # Generate music and SFX
        background_music, sfx_paths = music_sfx_example(config, script)
        logger.info("Generated music and downloaded SFX")
        
        # Example video path (would be created by VideoCreator)
        video_path = str(Path(config['system']['temp_dir']) / "example_video.mp4")
        
        # Advanced video editing
        srt_path, thumbnail_path = advanced_video_editing_example(
            config, video_path, script
        )
        logger.info("Completed advanced video editing")
        
        # Demonstrate retry mechanism
        retry_example()
        logger.info("Completed retry mechanism demonstration")
        
        # Clean up example files
        if config['system'].get('cleanup_temp_files', False):
            logger.info("Cleaning up temporary files")
            for path in [background_music, *sfx_paths, srt_path, thumbnail_path]:
                if os.path.exists(path):
                    os.remove(path)
        
        logger.info("All advanced feature examples completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 