#!/usr/bin/env python3

"""
PixVerse Animator module for creating animated videos from static images.
Uses the PixVerse AI API to transform static images into dynamic videos.
"""

import os
import time
import uuid
import json
import requests
import logging
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import time
from ..utils.config import Config
from ..utils.logger import logger
from retry import retry

class PixVerseAnimationError(Exception):
    """Custom exception for PixVerse animation errors."""
    pass

class PixVerseAnimator:
    """Handles animation of static images using PixVerse AI API."""
    
    def __init__(self, output_dir: str, config: Config):
        """
        Initialize the PixVerseAnimator.
        
        Args:
            output_dir: Directory to save animated video files
            config: Configuration object containing API keys and settings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        
        # Initialize API key from config
        self.api_key = self.config.get('api_keys.pixverse.api_key')
        if not self.api_key:
            raise ValueError("PixVerse API key not found in configuration")
        
        # API endpoints - Updated to current endpoints
        self.base_url = "https://app-api.pixverse.ai"
        # Update the upload URL to the current endpoint
        self.upload_url = f"{self.base_url}/openapi/v2/image/upload"
        # Update the image-to-video URL to the current endpoint for v4 model
        self.img2video_url = f"{self.base_url}/openapi/v2/video/img/generate"
        self.status_url = f"{self.base_url}/openapi/v2/video/result"
        
        # Default settings - Use 540p for free accounts
        self.default_settings = {
            'aspect_ratio': "16:9",
            'duration': 5,  # seconds
            'model': "v3.5",  # Default to v3.5, since that's what's mentioned in docs
            'motion_mode': "normal",  # normal or fast
            'quality': "540p",  # Changed from 720p to 540p for free accounts (360p, 540p, 720p, 1080p)
            'seed': 0,  # 0 for random seed
            'water_mark': False
        }
        
        # Get animation prompt prefix from config
        self.prompt_prefix = self.config.get(
            'content.visual.animation.prompt_prefix', 
            "Subtle camera movement, gentle animation of"
        )
        
        self.logger = logging.getLogger(__name__)

    def _get_headers(self, trace_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate headers for API requests.
        
        Args:
            trace_id: Optional trace ID for request tracking
            
        Returns:
            Dict with header values
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())
            
        return {
            "API-KEY": self.api_key,
            "Ai-trace-ID": trace_id,
            "Content-Type": "application/json"
        }

    @retry(exceptions=(requests.RequestException,), tries=3, delay=2, backoff=2)
    def upload_image(self, image_path: Union[str, Path]) -> int:
        """
        Upload image to PixVerse server.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image ID from PixVerse
            
        Raises:
            PixVerseAnimationError: If upload fails
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        trace_id = str(uuid.uuid4())
        headers = {
            "API-KEY": self.api_key,
            "Ai-trace-ID": trace_id
        }
        
        try:
            with open(image_path, 'rb') as image_file:
                # Update file field name to 'image' based on new API
                files = {'image': (image_path.name, image_file, f'image/{image_path.suffix[1:]}')}
                
                self.logger.info(f"Uploading image {image_path.name} to PixVerse")
                response = requests.post(self.upload_url, headers=headers, files=files)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('ErrCode') != 0:
                    raise PixVerseAnimationError(f"Image upload failed: {result.get('ErrMsg')}")
                
                # Updated response structure - img_id is now under Resp
                img_id = result.get('Resp', {}).get('img_id')
                if not img_id:
                    raise PixVerseAnimationError("No image ID returned from upload")
                
                self.logger.info(f"Successfully uploaded image, received img_id: {img_id}")
                return img_id
                
        except requests.RequestException as e:
            self.logger.error(f"Request error during image upload: {str(e)}")
            raise PixVerseAnimationError(f"Failed to upload image: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during image upload: {str(e)}")
            raise PixVerseAnimationError(f"Failed to upload image: {str(e)}") from e

    @retry(exceptions=(requests.RequestException,), tries=3, delay=2, backoff=2)
    def create_animation(
        self, 
        img_id: int,
        prompt: Optional[str] = None,
        settings: Optional[Dict[str, any]] = None
    ) -> int:
        """
        Create animation from uploaded image.
        
        Args:
            img_id: Image ID from upload_image
            prompt: Text prompt to guide animation (optional)
            settings: Optional custom settings to override defaults
            
        Returns:
            Video ID for status checking
            
        Raises:
            PixVerseAnimationError: If animation creation fails
        """
        # Merge default settings with custom settings
        merged_settings = self.default_settings.copy()
        if settings:
            merged_settings.update(settings)
            
        # Create request payload - updated for current API
        # According to current PixVerse API docs
        payload = {
            "img_id": img_id,
            "aspect_ratio": merged_settings['aspect_ratio'],
            "duration": merged_settings['duration'],
            "model": merged_settings['model'],
            "motion_mode": merged_settings['motion_mode'],
            "quality": merged_settings['quality'],
            "seed": merged_settings['seed'],
            "water_mark": merged_settings['water_mark']
        }
        
        # Add prompt if provided
        if prompt:
            payload["prompt"] = prompt
            
        trace_id = str(uuid.uuid4())
        headers = {
            "API-KEY": self.api_key,
            "Ai-trace-ID": trace_id,
            "Content-Type": "application/json"
        }
        
        try:
            self.logger.info(f"Creating animation from image {img_id} with prompt: {prompt}")
            self.logger.debug(f"Animation request payload: {payload}")
            self.logger.debug(f"Animation request headers: {headers}")
            
            # Add more detailed logging and error handling
            response = requests.post(self.img2video_url, headers=headers, json=payload)
            
            # Log the raw response for debugging
            self.logger.debug(f"Animation API response status: {response.status_code}")
            self.logger.debug(f"Animation API response headers: {response.headers}")
            try:
                self.logger.debug(f"Animation API response body: {response.text}")
            except:
                self.logger.debug("Could not log response body")
            
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ErrCode') != 0:
                error_msg = result.get('ErrMsg', 'Unknown error')
                self.logger.error(f"Animation API returned error: {error_msg}")
                raise PixVerseAnimationError(f"Animation creation failed: {error_msg}")
            
            # Get video_id from response
            video_id = result.get('Resp', {}).get('video_id')
            if not video_id:
                raise PixVerseAnimationError("No video ID returned from animation creation")
            
            self.logger.info(f"Successfully created animation task, received video_id: {video_id}")
            return video_id
            
        except requests.exceptions.HTTPError as e:
            error_details = ""
            try:
                if e.response is not None:
                    error_details = f"Status code: {e.response.status_code}, Response: {e.response.text}"
            except:
                pass
            
            self.logger.error(f"HTTP error during animation creation: {str(e)} - {error_details}")
            raise PixVerseAnimationError(f"Failed to create animation: {str(e)} - {error_details}") from e
        except requests.RequestException as e:
            self.logger.error(f"Request error during animation creation: {str(e)}")
            raise PixVerseAnimationError(f"Failed to create animation: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during animation creation: {str(e)}")
            raise PixVerseAnimationError(f"Failed to create animation: {str(e)}") from e

    @retry(exceptions=(requests.RequestException,), tries=3, delay=2, backoff=2)
    def check_animation_status(self, video_id: int) -> Dict[str, any]:
        """
        Check status of animation task.
        
        Args:
            video_id: Video ID from create_animation
            
        Returns:
            Dict with status information
            
        Raises:
            PixVerseAnimationError: If status check fails
        """
        url = f"{self.status_url}/{video_id}"
        headers = self._get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ErrCode') != 0:
                raise PixVerseAnimationError(f"Status check failed: {result.get('ErrMsg')}")
            
            return result.get('Resp', {})
            
        except requests.RequestException as e:
            self.logger.error(f"Request error during status check: {str(e)}")
            raise PixVerseAnimationError(f"Failed to check animation status: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during status check: {str(e)}")
            raise PixVerseAnimationError(f"Failed to check animation status: {str(e)}") from e

    @retry(exceptions=(requests.RequestException,), tries=3, delay=5, backoff=2)
    def download_animation(self, video_url: str, output_path: Optional[Union[str, Path]] = None) -> str:
        """
        Download completed animation.
        
        Args:
            video_url: URL from status check response
            output_path: Optional custom output path, defaults to output_dir
            
        Returns:
            Path to downloaded video file
            
        Raises:
            PixVerseAnimationError: If download fails
        """
        if not output_path:
            output_filename = f"pixverse_animation_{int(time.time())}.mp4"
            output_path = self.output_dir / output_filename
        else:
            output_path = Path(output_path)
            
        try:
            self.logger.info(f"Downloading animation from {video_url}")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Successfully downloaded animation to {output_path}")
            return str(output_path)
            
        except requests.RequestException as e:
            self.logger.error(f"Request error during animation download: {str(e)}")
            raise PixVerseAnimationError(f"Failed to download animation: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during animation download: {str(e)}")
            raise PixVerseAnimationError(f"Failed to download animation: {str(e)}") from e

    def animate_image(
        self, 
        image_path: Union[str, Path],
        animation_prompt: Optional[str] = None,
        settings: Optional[Dict[str, any]] = None,
        output_path: Optional[Union[str, Path]] = None,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> str:
        """
        Full workflow to animate an image.
        
        Args:
            image_path: Path to image file
            animation_prompt: Text prompt to guide animation
            settings: Custom animation settings
            output_path: Custom output path for video
            poll_interval: Time between status checks (seconds)
            timeout: Maximum time to wait for completion (seconds)
            
        Returns:
            Path to downloaded animation file
            
        Raises:
            PixVerseAnimationError: If any step fails
            TimeoutError: If animation takes too long
        """
        start_time = time.time()
        
        try:
            # 1. Upload image
            img_id = self.upload_image(image_path)
            
            # 2. Create animation
            video_id = self.create_animation(img_id, animation_prompt, settings)
            
            # 3. Poll for completion
            video_url = None
            while time.time() - start_time < timeout:
                status_info = self.check_animation_status(video_id)
                
                # Status 1 = complete, 5 = processing
                if status_info.get('status') == 1:
                    video_url = status_info.get('url')
                    if not video_url:
                        raise PixVerseAnimationError(f"Animation completed (video_id: {video_id}) but no URL returned")
                    break
                elif status_info.get('status') == 5:
                    self.logger.info(f"Animation in progress (video_id: {video_id}), waiting {poll_interval}s...")
                    time.sleep(poll_interval)
                else:
                    # Any other status is unexpected
                    raise PixVerseAnimationError(f"Unexpected animation status: {status_info.get('status')}")
            
            if not video_url:
                raise TimeoutError(f"Animation timed out after {timeout} seconds")
            
            # 4. Download completed animation
            return self.download_animation(video_url, output_path)
            
        except Exception as e:
            self.logger.error(f"Error in animate_image workflow: {str(e)}")
            raise

    def animate_images_batch(
        self,
        image_paths: List[Union[str, Path]],
        animation_prompts: Optional[List[str]] = None,
        settings: Optional[Dict[str, any]] = None,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> List[str]:
        """
        Animate multiple images in batch.
        
        Args:
            image_paths: List of paths to images
            animation_prompts: List of prompts for each image (optional)
            settings: Animation settings to apply to all images
            poll_interval: How often to check animation status in seconds
            timeout: Maximum time to wait for each animation in seconds
            
        Returns:
            List of paths to animated video files
        """
        if not image_paths:
            logger.warning("No images provided for animation")
            return []
            
        if animation_prompts and len(animation_prompts) != len(image_paths):
            logger.warning(f"Number of prompts ({len(animation_prompts)}) doesn't match number of images ({len(image_paths)})")
            return []
            
        animated_videos = []
        
        for i, image_path in enumerate(image_paths):
            try:
                # Extract scene number from filename (e.g., scene_001_uuid.png -> 001)
                scene_num = Path(image_path).stem.split('_')[1]
                output_filename = f"scene_{scene_num}.mp4"
                output_path = self.output_dir / output_filename
                
                prompt = None
                if animation_prompts and i < len(animation_prompts):
                    prompt = animation_prompts[i]
                
                logger.info(f"Animating image {i+1}/{len(image_paths)}: {Path(image_path).name}")
                video_path = self.animate_image(
                    image_path=str(Path(image_path).resolve()),  # Use full path of actual image
                    animation_prompt=prompt,
                    settings=settings,
                    output_path=output_path,
                    poll_interval=poll_interval,
                    timeout=timeout
                )
                
                if video_path:
                    animated_videos.append(video_path)
                    logger.info(f"Successfully animated image {i+1}/{len(image_paths)}")
                else:
                    logger.warning(f"Failed to animate image {i+1}")
                
                # Add a small delay between requests to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error animating image {i+1}: {str(e)}")
                continue
        
        success_rate = len(animated_videos) / len(image_paths) if image_paths else 0
        logger.info(f"Animation batch completed. Success rate: {success_rate:.1%} ({len(animated_videos)}/{len(image_paths)} images)")
        return animated_videos

    def generate_animation_prompt_from_scene(self, scene_text: str) -> str:
        """
        Generate an appropriate animation prompt from scene description.
        
        Args:
            scene_text: Text description of the scene
            
        Returns:
            Animation prompt optimized for PixVerse
        """
        # Extract key elements from scene
        words = scene_text.split()
        # Take first 30 words or less if scene is shorter
        key_words = words[:min(30, len(words))]
        short_description = " ".join(key_words)
        
        # Add motion directives using the prompt prefix from config
        prompt = f"{self.prompt_prefix} {short_description}"
        
        return prompt 