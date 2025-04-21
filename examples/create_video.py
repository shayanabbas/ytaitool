#!/usr/bin/env python3

"""
Example script demonstrating how to create a video from generated images using the VideoEditor.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

# Add the parent directory to the Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.video_editing.video_editor import VideoEditor
from src.utils.logger import get_logger

logger = get_logger(__name__)

def prepare_scene_data(image_paths: List[str], voiceover_paths: List[str]) -> List[Dict[str, str]]:
    """
    Prepare scene data by pairing images with voiceovers.
    
    Args:
        image_paths: List of paths to scene images
        voiceover_paths: List of paths to voiceover audio files
        
    Returns:
        List of dictionaries containing scene data
    """
    scenes = []
    for img_path, audio_path in zip(image_paths, voiceover_paths):
        scenes.append({
            'file': img_path,
            'text': f"Scene {len(scenes) + 1}"  # Example caption
        })
    return scenes

def main():
    # Example paths (these would normally come from the generate_scenes.py script)
    image_dir = Path("output/example_scenes")
    audio_dir = Path("output/example_audio")
    
    # Ensure directories exist
    image_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get sorted lists of image and audio files
        image_paths = sorted(list(image_dir.glob("scene_*.png")))
        voiceover_paths = sorted(list(audio_dir.glob("voiceover_*.mp3")))
        
        if not image_paths:
            logger.error("No image files found in the output directory!")
            return
            
        if not voiceover_paths:
            logger.warning("No voiceover files found. Video will be created without audio.")
            # Create dummy voiceover paths to match number of images
            voiceover_paths = [None] * len(image_paths)
        
        # Initialize the video editor
        editor = VideoEditor()
        
        # Prepare scene data
        scenes = prepare_scene_data(
            [str(p) for p in image_paths],
            [str(p) if p else None for p in voiceover_paths]
        )
        
        # Example background music (you would need to provide this)
        background_music = "assets/background_music.mp3"
        
        # Create video for both short and long form content
        for is_short in [True, False]:
            format_type = "short" if is_short else "long"
            logger.info(f"Creating {format_type} form video...")
            
            output_path = editor.create_video(
                scenes=scenes,
                voiceovers=[{'file': vo, 'text': f"Scene {i+1}"} if vo else None 
                           for i, vo in enumerate(voiceover_paths)],
                background_music=background_music,
                is_short=is_short
            )
            
            if output_path:
                logger.info(f"Successfully created {format_type} form video: {output_path}")
            else:
                logger.error(f"Failed to create {format_type} form video")
    
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 