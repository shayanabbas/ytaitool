#!/usr/bin/env python3

"""
AnimationGenerator module for animating static images using Pika Labs API.
"""

import os
import time
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from retry import retry
from ..utils.logger import logger
from ..utils.config import Config

class AnimationError(Exception):
    """Raised when animation generation fails."""
    pass

class APIKeyError(Exception):
    """Raised when API key is missing or invalid."""
    pass

class AnimationGenerator:
    """Handles animation of static images using Pika Labs API."""
    
    def __init__(self, output_dir: str, config: Config):
        """
        Initialize the AnimationGenerator.
        
        Args:
            output_dir: Directory to save animated files
            config: Configuration object containing API keys and settings
            
        Raises:
            APIKeyError: If Pika Labs API key is missing
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize API key from config
        self.api_key = config.get('apis.pika.api_key')
        if not self.api_key:
            raise APIKeyError("Pika Labs API key not found in configuration")
            
        # Animation settings
        self.default_settings = {
            'motion_scale': 0.5,  # Scale of motion (0.1 to 1.0)
            'duration': 3.0,      # Duration in seconds
            'fps': 30,            # Frames per second
            'quality': 'high',    # Output quality
            'format': 'mp4'       # Output format
        }
        
        self.logger = logger
    
    def _create_animation_prompt(
        self,
        focus_subject: str,
        motion_type: str = "gentle",
        camera_motion: Optional[str] = None
    ) -> str:
        """
        Create a formatted prompt for animation generation.
        
        Args:
            focus_subject: Main subject to focus on in the animation
            motion_type: Type of motion (e.g., 'gentle', 'dynamic', 'subtle')
            camera_motion: Optional camera motion description
            
        Returns:
            Formatted prompt string
        """
        prompt = f"Animate with {motion_type} motion, focus on {focus_subject}"
        if camera_motion:
            prompt += f", {camera_motion}"
        return prompt

    @retry(tries=3, delay=2, backoff=2)
    async def animate_image(
        self,
        image_path: str,
        focus_subject: str,
        motion_type: str = "gentle",
        camera_motion: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Animate a single image using Pika Labs API.
        
        Args:
            image_path: Path to the input image
            focus_subject: Main subject to focus on in the animation
            motion_type: Type of motion to apply
            camera_motion: Optional camera motion description
            settings: Optional animation settings to override defaults
            
        Returns:
            Path to the animated video file
            
        Raises:
            AnimationError: If animation generation fails
            FileNotFoundError: If input image doesn't exist
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Input image not found: {image_path}")
            
            # Merge settings with defaults
            current_settings = self.default_settings.copy()
            if settings:
                current_settings.update(settings)
            
            # Create animation prompt
            prompt = self._create_animation_prompt(
                focus_subject=focus_subject,
                motion_type=motion_type,
                camera_motion=camera_motion
            )
            
            # Prepare API request
            url = "https://api.pika.art/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "multipart/form-data"
            }
            
            # Prepare the image file
            with open(image_path, 'rb') as img:
                files = {'image': img}
                data = {
                    'prompt': prompt,
                    'motion_scale': current_settings['motion_scale'],
                    'duration': current_settings['duration'],
                    'fps': current_settings['fps'],
                    'quality': current_settings['quality']
                }
                
                # Start animation generation
                response = requests.post(url, headers=headers, data=data, files=files)
                response.raise_for_status()
                
                generation_id = response.json()['id']
            
            # Wait for animation completion
            status_url = f"{url}/status/{generation_id}"
            while True:
                status_response = requests.get(status_url, headers=headers)
                status_response.raise_for_status()
                status = status_response.json()
                
                if status['status'] == 'completed':
                    # Download the animated video
                    video_url = status['video_url']
                    video_response = requests.get(video_url)
                    video_response.raise_for_status()
                    
                    # Save the animated video
                    output_filename = f"{Path(image_path).stem}_animated.{current_settings['format']}"
                    output_path = self.output_dir / output_filename
                    
                    with open(output_path, 'wb') as f:
                        f.write(video_response.content)
                    
                    self.logger.info(f"Animation generated successfully: {output_path}")
                    return str(output_path)
                
                elif status['status'] == 'failed':
                    raise AnimationError(f"Animation generation failed: {status.get('error', 'Unknown error')}")
                
                time.sleep(5)  # Wait before checking status again
                
        except requests.exceptions.RequestException as e:
            raise AnimationError(f"API request failed: {str(e)}")
        except Exception as e:
            raise AnimationError(f"Animation generation failed: {str(e)}")

    async def animate_scene_batch(
        self,
        scene_data: List[Dict[str, str]],
        settings: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Animate a batch of scenes with their respective focus subjects and motions.
        
        Args:
            scene_data: List of dictionaries containing scene information:
                       {'image_path': str, 'focus_subject': str,
                        'motion_type': str, 'camera_motion': str}
            settings: Optional animation settings to override defaults
            
        Returns:
            List of paths to animated video files
        """
        animated_paths = []
        total_scenes = len(scene_data)
        
        for i, scene in enumerate(scene_data, 1):
            try:
                self.logger.info(f"Animating scene {i}/{total_scenes}")
                
                animated_path = await self.animate_image(
                    image_path=scene['image_path'],
                    focus_subject=scene['focus_subject'],
                    motion_type=scene.get('motion_type', 'gentle'),
                    camera_motion=scene.get('camera_motion'),
                    settings=settings
                )
                
                animated_paths.append(animated_path)
                
                # Add delay between animations to respect API rate limits
                if i < total_scenes:
                    time.sleep(2)
                    
            except Exception as e:
                self.logger.error(f"Failed to animate scene {i}: {str(e)}")
                continue
        
        return animated_paths

    def cleanup_temp_files(self):
        """Remove temporary animation files."""
        try:
            # Remove temporary files with specific patterns
            patterns = ['*_temp.*', '*_animated_temp.*']
            for pattern in patterns:
                for file in self.output_dir.glob(pattern):
                    try:
                        file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to delete temporary file {file}: {str(e)}")
                        
            self.logger.info("Cleaned up temporary animation files")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}") 