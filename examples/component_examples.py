#!/usr/bin/env python3

"""
Individual examples for each component of the YouTube AI Content Generator.
Each example demonstrates how to use a specific component with the configuration.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content_generation.script_generator import ScriptGenerator
from src.content_generation.visual_generator import VisualGenerator
from src.content_generation.voice_generator import VoiceGenerator
from src.video_creation.video_creator import VideoCreator
from src.upload.youtube_uploader import YouTubeUploader

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

def script_generator_example(config: Dict[str, Any]) -> str:
    """Example usage of ScriptGenerator"""
    print("\n=== Script Generator Example ===")
    
    generator = ScriptGenerator(
        api_key=config['api_keys']['openai']['api_key'],
        model="gpt-4-turbo-preview",
        min_words=config['content']['script']['min_words_short'],
        max_words=config['content']['script']['max_words_short'],
        temperature=config['content']['script']['temperature']
    )
    
    script = generator.generate_script(
        topic="The History of Pizza",
        video_type="short",
        context="Focus on interesting facts and the evolution of pizza through different cultures"
    )
    
    print(f"Generated script:\n{script}")
    return script

def visual_generator_example(config: Dict[str, Any], script: str) -> list:
    """Example usage of VisualGenerator"""
    print("\n=== Visual Generator Example ===")
    
    # Ensure temp directory exists
    temp_dir = Path(config['system']['temp_dir'])
    (temp_dir / 'images').mkdir(parents=True, exist_ok=True)
    
    generator = VisualGenerator(
        api_key=config['api_keys']['leonardo']['api_key'],
        temp_dir=config['content']['visual']['temp_dir'],
        image_style=config['content']['visual']['image_style'],
        aspect_ratio=config['content']['visual']['aspect_ratio_short'],
        resolution=config['content']['visual']['resolution'],
        model_id=config['api_keys']['leonardo'].get('model_id', '1e7737d7-545e-469f-857f-e4b46eaa151d'),
        video_type="short"
    )
    
    image_paths = generator.generate_scenes(script)
    print(f"Generated {len(image_paths)} images:")
    for path in image_paths:
        print(f"- {path}")
    
    return image_paths

def voice_generator_example(script, config):
    """Example of generating a voiceover."""
    print("\nRunning voice generator example...")
    
    # Ensure temp directory exists
    audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['content']['voice']['temp_dir'])
    os.makedirs(audio_dir, exist_ok=True)
    
    generator = VoiceGenerator(
        api_key=config['api_keys']['elevenlabs']['api_key'],
        model_id=config['api_keys']['elevenlabs'].get('model_id', 'eleven_turbo_v2'),
        voice_id=config['api_keys']['elevenlabs'].get('voice_id', 'pNInz6obpgDQGcFmaJgB'),  # Added voice_id parameter
        temp_dir=config['content']['voice']['temp_dir']
    )
    
    audio_path = generator.generate_voiceover(script)
    print(f"Generated voiceover at: {audio_path}")
    
    return audio_path

def video_creator_example(config: Dict[str, Any], image_paths: list, audio_path: str) -> str:
    """Example usage of VideoCreator"""
    print("\n=== Video Creator Example ===")
    
    # Ensure output directory exists
    output_dir = Path(config['system']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    creator = VideoCreator(
        fps=config['content']['visual']['fps'],
        transition_duration=config['video']['transitions']['duration'],
        background_music_volume=config['content']['music']['volume'],
        caption_font=config['video']['captions']['font'],
        caption_size=config['video']['captions']['size'],
        caption_color=config['video']['captions']['color']
    )
    
    output_path = str(output_dir / 'example_video.mp4')
    video_path = creator.create_video(
        image_paths=image_paths,
        audio_path=audio_path,
        output_path=output_path,
        video_dimensions=(
            config['video']['short_form']['width'],
            config['video']['short_form']['height']
        )
    )
    
    print(f"Created video: {video_path}")
    return video_path

def youtube_uploader_example(config: Dict[str, Any], video_path: str) -> str:
    """Example usage of YouTubeUploader"""
    print("\n=== YouTube Uploader Example ===")
    
    # Create paths for client secrets and credentials
    config_dir = Path(__file__).parent.parent / 'config'
    client_secrets_file = config_dir / 'client_secrets.json'
    credentials_path = config_dir / 'youtube_credentials.pickle'
    
    uploader = YouTubeUploader(
        client_secrets_file=str(client_secrets_file),
        credentials_path=str(credentials_path)
    )
    
    video_id = uploader.upload_video(
        video_path=video_path,
        title="The History of Pizza - AI Generated Content",
        description="An AI-generated video exploring the fascinating history of pizza.\n\n"
                   "Generated using YouTube AI Content Generator",
        tags=["pizza", "history", "food", "AI generated"],
        privacy_status=config['upload']['default_privacy']
    )
    
    print(f"Uploaded video: https://youtube.com/watch?v={video_id}")
    return video_id

def cleanup_example_files(config: Dict[str, Any], image_paths: list, audio_path: str, video_path: str):
    """Clean up files created during the example"""
    print("\n=== Cleaning up example files ===")
    
    # Remove generated images
    for path in image_paths:
        os.remove(path)
        print(f"Removed: {path}")
    
    # Remove audio file
    os.remove(audio_path)
    print(f"Removed: {audio_path}")
    
    # Remove video file
    os.remove(video_path)
    print(f"Removed: {video_path}")

def main():
    """Run all component examples"""
    try:
        config = load_config()
        
        # Run examples in sequence
        script = script_generator_example(config)
        image_paths = visual_generator_example(config, script)
        audio_path = voice_generator_example(script, config)
        video_path = video_creator_example(config, image_paths, audio_path)
        video_id = youtube_uploader_example(config, video_path)
        
        # Clean up example files
        if config['system'].get('cleanup_temp_files', False):
            cleanup_example_files(config, image_paths, audio_path, video_path)
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 