"""
Video animation using Leonardo.AI's motion generation API.
"""

import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from ..utils.logger import logger

class LeonardoAnimator:
    """Class for animating images using Leonardo.AI's motion generation API."""
    
    def __init__(self, api_key: str, output_dir: str):
        """
        Initialize the animator.
        
        Args:
            api_key: Leonardo.AI API key
            output_dir: Directory for output files
        """
        self.api_key = api_key
        self.output_dir = output_dir
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Leonardo animator initialized with output directory: {output_dir}")

    def _wait_for_generation(self, generation_id: str, timeout: int = 60) -> Optional[Dict]:
        """
        Wait for a generation to complete and return the result.
        
        Args:
            generation_id: The generation ID to check
            timeout: Maximum time to wait in seconds
            
        Returns:
            Generation data if successful, None if failed or timed out
        """
        url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                # Log response for debugging
                logger.debug(f"Generation status check response: {json.dumps(data, indent=2)}")
                
                # Get generation status
                generation = data.get('generations_by_pk', {})
                status = generation.get('status')
                
                logger.debug(f"Generation status after {time.time() - start_time:.2f} seconds: {status}")
                
                if status == "COMPLETE":
                    # For text-to-video, the video URL is in the response
                    video_url = generation.get('videoUrl')
                    if video_url:
                        return {"videoUrl": video_url}
                    else:
                        logger.error("Generation complete but no video URL found")
                        return None
                elif status == "FAILED":
                    logger.error(f"Generation failed: {json.dumps(data, indent=2)}")
                    return None
                    
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error checking generation status: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                time.sleep(2)
                
        logger.error(f"Generation timed out after {timeout} seconds")
        return None

    def _get_video_url(self, generation_data: Dict) -> Optional[str]:
        """Extract video URL from generation data."""
        try:
            return generation_data.get('motionMP4URL')
        except Exception as e:
            logger.error(f"Error extracting video URL: {str(e)}")
            return None

    def animate(self, animation_prompts: List[str], scene_numbers: List[int]) -> List[str]:
        """
        Generate animations using Leonardo's text-to-video endpoint.
        
        Args:
            animation_prompts: List of prompts to generate animations from
            scene_numbers: List of scene numbers to identify each animation
            
        Returns:
            List of paths to downloaded video files
        """
        if not animation_prompts:
            raise ValueError("No animation prompts provided")
            
        if len(animation_prompts) != len(scene_numbers):
            raise ValueError("Number of prompts must match number of scene numbers")
            
        logger.info(f"Generating {len(animation_prompts)} animations...")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        video_paths = []
        for prompt, scene_num in zip(animation_prompts, scene_numbers):
            try:
                # Generate the video
                logger.info(f"Generating animation for scene {scene_num} with prompt: {prompt}")
                
                url = "https://cloud.leonardo.ai/api/rest/v1/generations-text-to-video"
                payload = {
                    "height": 480,
                    "width": 832,
                    "prompt": prompt,
                    "frameInterpolation": True,
                    "isPublic": False,
                    "promptEnhance": True
                }
                
                response = requests.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                
                generation_id = data.get('sdGenerationJob', {}).get('generationId')
                if not generation_id:
                    logger.error(f"Failed to get generation ID for scene {scene_num}")
                    continue
                    
                # Wait for generation to complete
                result = self._wait_for_generation(generation_id)
                if not result:
                    logger.error(f"Generation failed or timed out for scene {scene_num}")
                    continue
                    
                video_url = result.get('videoUrl')
                if not video_url:
                    logger.error(f"No video URL found for scene {scene_num}")
                    continue
                    
                # Download the video
                output_path = os.path.join(self.output_dir, f"scene_{scene_num}.mp4")
                logger.info(f"Downloading video for scene {scene_num} to {output_path}")
                
                video_response = requests.get(video_url)
                video_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                    
                video_paths.append(output_path)
                logger.info(f"Successfully generated and downloaded video for scene {scene_num}")
                
            except Exception as e:
                logger.error(f"Error generating animation for scene {scene_num}: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                continue
                
        if not video_paths:
            raise RuntimeError("Failed to generate any animations")
            
        return video_paths

    def animate_images_batch(
        self,
        scene_prompts: List[str],
        timeout: int = 120
    ) -> List[str]:
        """
        Generate animations for multiple scenes in batch.
        
        Args:
            scene_prompts: List of prompts for each scene
            timeout: Maximum time to wait for each generation in seconds
            
        Returns:
            List of paths to downloaded video files
        """
        if not scene_prompts:
            raise ValueError("No scene prompts provided")
            
        logger.info(f"Starting batch animation for {len(scene_prompts)} scenes")
        
        # Generate scene numbers (1-based indexing)
        scene_numbers = list(range(1, len(scene_prompts) + 1))
        
        try:
            # Generate all animations in one batch
            video_paths = self.animate(scene_prompts, scene_numbers)
            logger.info(f"Successfully generated {len(video_paths)} animations")
            return video_paths
            
        except Exception as e:
            logger.error(f"Error in batch animation: {str(e)}")
            raise

    def generate_animation_prompt_from_scene(self, scene_text: str) -> str:
        """
        Generate an animation prompt from a scene description.
        Not used in direct animation but kept for compatibility.
        """
        return "Subtle camera movement with natural motion"

    def cleanup(self):
        """Clean up any temporary files."""
        # Implementation depends on your cleanup needs
        pass 