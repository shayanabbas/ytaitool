import os
import time
import requests
from typing import Optional
from ..utils.config import Config
from ..utils.logger import logger

class MusicGenerator:
    def __init__(self):
        config = Config()
        self.api_key = config.get('api_keys.suno.api_key')
        self.settings = config.content_settings.get('music', {})
        self.temp_dir = config.get('system.temp_dir', 'temp')
        os.makedirs(os.path.join(self.temp_dir, 'music'), exist_ok=True)

    def _create_music_prompt(self, video_concept: str, is_short: bool) -> str:
        """Create a prompt for music generation based on video concept."""
        duration = "30 seconds" if is_short else "3 minutes"
        style = self.settings.get('music_style', 'upbeat and energetic')
        return f"Create a {duration} {style} background music track that matches the mood of: {video_concept}"

    def generate_background_music(self, video_concept: str, is_short: bool) -> Optional[str]:
        """Generate background music using Suno AI API."""
        try:
            logger.info("Starting background music generation...")
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Set generation parameters
            data = {
                'prompt': self._create_music_prompt(video_concept, is_short),
                'duration': 30 if is_short else 180,  # Duration in seconds
                'temperature': 0.7,
                'top_k': 250,
                'top_p': 0.95,
                'output_format': 'mp3',
                'sample_rate': 44100
            }
            
            # Start generation
            response = requests.post(
                'https://api.suno.ai/v1/generations',
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            generation_id = response.json()['id']
            
            # Wait for generation to complete
            max_attempts = 60  # Music generation might take longer
            attempt = 0
            while attempt < max_attempts:
                time.sleep(5)
                status_response = requests.get(
                    f'https://api.suno.ai/v1/generations/{generation_id}',
                    headers=headers
                )
                status_response.raise_for_status()
                
                status_data = status_response.json()
                if status_data['status'] == 'completed':
                    # Download the generated music
                    music_url = status_data['output_url']
                    music_response = requests.get(music_url)
                    music_response.raise_for_status()
                    
                    filename = 'background_music.mp3'
                    music_path = os.path.join(self.temp_dir, 'music', filename)
                    
                    with open(music_path, 'wb') as f:
                        f.write(music_response.content)
                    
                    logger.info("Background music generated successfully!")
                    return music_path
                
                attempt += 1
            
            raise TimeoutError("Music generation timed out")
            
        except Exception as e:
            logger.error(f"Error generating background music: {str(e)}")
            return None

    def cleanup(self):
        """Clean up temporary music files."""
        try:
            music_dir = os.path.join(self.temp_dir, 'music')
            for file in os.listdir(music_dir):
                if file.endswith('.mp3'):
                    os.remove(os.path.join(music_dir, file))
            logger.info("Cleaned up temporary music files.")
        except Exception as e:
            logger.error(f"Error cleaning up music files: {str(e)}") 