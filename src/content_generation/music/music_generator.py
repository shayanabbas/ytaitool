#!/usr/bin/env python3

"""
MusicGenerator module for handling background music generation in the YouTube AI Content Generator.
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from time import sleep

class MusicGenerator:
    """Handles generation of background music for videos."""
    
    def __init__(self, api_key: str, output_dir: str):
        """
        Initialize the MusicGenerator.
        
        Args:
            api_key: API key for the music generation service
            output_dir: Directory to save generated music files
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings for music generation
        self.default_settings = {
            'tempo': 120,  # BPM
            'duration': 30,  # seconds
            'genre': 'ambient',
            'mood': 'calm',
            'instruments': ['piano', 'strings'],
            'format': 'mp3',
            'quality': 'high'
        }

    def generate_music(
        self,
        duration: int,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        tempo: Optional[int] = None,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate background music with specified parameters.
        
        Args:
            duration: Length of music in seconds
            genre: Music genre (e.g., 'ambient', 'electronic', 'orchestral')
            mood: Emotional mood of the music (e.g., 'calm', 'energetic', 'dramatic')
            tempo: Beats per minute
            output_filename: Name for the output file (without extension)
            
        Returns:
            str: Path to the generated music file
        """
        # Use default settings if parameters not provided
        settings = self.default_settings.copy()
        settings['duration'] = duration
        if genre:
            settings['genre'] = genre
        if mood:
            settings['mood'] = mood
        if tempo:
            settings['tempo'] = tempo

        # Generate unique filename if not provided
        if not output_filename:
            output_filename = f"music_{genre or settings['genre']}_{duration}s"
        
        output_path = self.output_dir / f"{output_filename}.{settings['format']}"

        try:
            # Make API request to music generation service
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.musicgen.example.com/v1/generate',  # Example API endpoint
                headers=headers,
                json=settings
            )
            response.raise_for_status()
            
            # Get generation task ID
            task_id = response.json()['task_id']
            
            # Poll for completion
            while True:
                status_response = requests.get(
                    f'https://api.musicgen.example.com/v1/status/{task_id}',
                    headers=headers
                )
                status_response.raise_for_status()
                
                status = status_response.json()['status']
                if status == 'completed':
                    # Download the generated music file
                    download_url = status_response.json()['download_url']
                    music_response = requests.get(download_url)
                    music_response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        f.write(music_response.content)
                    break
                elif status == 'failed':
                    raise Exception(f"Music generation failed: {status_response.json().get('error')}")
                
                sleep(5)  # Wait before polling again
            
            return str(output_path)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Music generation failed: {str(e)}")

    def adjust_music_length(self, music_file: str, target_duration: float) -> str:
        """
        Adjust the length of a music file to match the target duration.
        
        Args:
            music_file: Path to the input music file
            target_duration: Desired duration in seconds
            
        Returns:
            str: Path to the adjusted music file
        """
        from moviepy.editor import AudioFileClip
        
        try:
            # Load the audio file
            audio = AudioFileClip(music_file)
            
            # Calculate how many times to loop the audio
            current_duration = audio.duration
            if target_duration <= current_duration:
                # Trim the audio if target duration is shorter
                adjusted_audio = audio.subclip(0, target_duration)
            else:
                # Loop the audio if target duration is longer
                loops_needed = int(target_duration / current_duration) + 1
                adjusted_audio = audio.loop(n=loops_needed).subclip(0, target_duration)
            
            # Generate output filename
            output_path = str(music_file).replace('.mp3', '_adjusted.mp3')
            
            # Write the adjusted audio
            adjusted_audio.write_audiofile(output_path)
            
            # Clean up
            audio.close()
            adjusted_audio.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to adjust music length: {str(e)}")

    def mix_audio_tracks(self, tracks: list[str], output_file: str) -> str:
        """
        Mix multiple audio tracks together.
        
        Args:
            tracks: List of paths to audio files to mix
            output_file: Path for the output mixed audio file
            
        Returns:
            str: Path to the mixed audio file
        """
        from moviepy.editor import AudioFileClip, CompositeAudioClip
        
        try:
            # Load all audio tracks
            audio_clips = [AudioFileClip(track) for track in tracks]
            
            # Create composite audio
            mixed_audio = CompositeAudioClip(audio_clips)
            
            # Write the mixed audio
            mixed_audio.write_audiofile(output_file)
            
            # Clean up
            for clip in audio_clips:
                clip.close()
            mixed_audio.close()
            
            return output_file
            
        except Exception as e:
            raise Exception(f"Failed to mix audio tracks: {str(e)}")

    def apply_fade(
        self,
        audio_file: str,
        fade_in: float = 0,
        fade_out: float = 0
    ) -> str:
        """
        Apply fade-in and fade-out effects to an audio file.
        
        Args:
            audio_file: Path to the input audio file
            fade_in: Duration of fade-in in seconds
            fade_out: Duration of fade-out in seconds
            
        Returns:
            str: Path to the audio file with fades applied
        """
        from moviepy.editor import AudioFileClip
        
        try:
            # Load the audio file
            audio = AudioFileClip(audio_file)
            
            # Apply fades
            if fade_in > 0:
                audio = audio.audio_fadein(fade_in)
            if fade_out > 0:
                audio = audio.audio_fadeout(fade_out)
            
            # Generate output filename
            output_path = str(audio_file).replace('.mp3', '_faded.mp3')
            
            # Write the processed audio
            audio.write_audiofile(output_path)
            
            # Clean up
            audio.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to apply audio fades: {str(e)}")

    def cleanup_temp_files(self, keep_original: bool = True):
        """
        Clean up temporary music files.
        
        Args:
            keep_original: Whether to keep the original generated music files
        """
        try:
            for file in self.output_dir.glob('*_adjusted.mp3'):
                file.unlink()
            for file in self.output_dir.glob('*_faded.mp3'):
                file.unlink()
            if not keep_original:
                for file in self.output_dir.glob('music_*.mp3'):
                    file.unlink()
        except Exception as e:
            raise Exception(f"Failed to cleanup temporary files: {str(e)}") 