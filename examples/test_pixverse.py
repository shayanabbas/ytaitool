#!/usr/bin/env python3

"""
Test script for PixVerse animation integration.
This script demonstrates how to use the PixVerseAnimator to create
animated videos from static images.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.video_editing.pixverse_animator import PixVerseAnimator

# Setup logging with debug level
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_image_animation():
    """Test animating a single image."""
    # Load config
    config = Config()
    
    # Check if PixVerse API key exists
    pixverse_api_key = config.get('api_keys.pixverse.api_key')
    if not pixverse_api_key:
        logger.error("PixVerse API key not found in config. Please add it to config.yaml.")
        return
    
    # Create output directory
    output_dir = Path("temp/animations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize animator
    animator = PixVerseAnimator(output_dir=str(output_dir), config=config)
    
    # Get test image path
    test_image_dir = Path("temp/images")
    if not test_image_dir.exists() or not any(test_image_dir.iterdir()):
        logger.error(f"No test images found in {test_image_dir}. Please generate images first.")
        return
    
    # Get the first image file
    image_files = list(test_image_dir.glob("*.png")) + list(test_image_dir.glob("*.jpg"))
    if not image_files:
        logger.error(f"No PNG or JPG images found in {test_image_dir}.")
        return
    
    test_image = str(image_files[0])
    logger.info(f"Using test image: {test_image}")
    
    # Create animation prompt
    prompt = "Gentle camera movement with subtle animation effects"
    
    try:
        # Animate image - UPDATED to use 540p quality for free accounts
        logger.info(f"Animating image with prompt: {prompt}")
        animation_path = animator.animate_image(
            image_path=test_image,
            animation_prompt=prompt,
            settings={
                'duration': 5,
                'quality': '540p',  # Changed to 540p for free accounts
                'motion_mode': 'normal',
                'model': 'v3.5'
            }
        )
        
        logger.info(f"Animation created successfully: {animation_path}")
        logger.info(f"Animation file size: {os.path.getsize(animation_path) / (1024 * 1024):.2f} MB")
        
        return animation_path
        
    except Exception as e:
        logger.error(f"Animation failed: {str(e)}")
        return None

if __name__ == "__main__":
    logger.info("Testing PixVerse animation integration")
    animation_path = test_single_image_animation()
    
    if animation_path:
        logger.info(f"Test completed successfully. Animation saved to: {animation_path}")
        # Try to open the animation file with the default video player
        try:
            if sys.platform == "darwin":  # macOS
                os.system(f"open {animation_path}")
            elif sys.platform == "win32":  # Windows
                os.system(f"start {animation_path}")
            else:  # Linux
                os.system(f"xdg-open {animation_path}")
        except Exception as e:
            logger.warning(f"Could not open animation file: {str(e)}")
    else:
        logger.error("Test failed. Could not create animation.") 