#!/usr/bin/env python3

"""
Example script demonstrating the usage of visual generator and YouTube uploader.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.content_generation.visual_generator import VisualGenerator
from src.upload.youtube_uploader import YouTubeUploader
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    # Example script content with scene descriptions
    script_content = """
[SCENE: Mountain Landscape]
A majestic mountain range stretches across the horizon, its snow-capped peaks piercing through wispy clouds. The morning sun casts a golden glow on the rocky slopes, while a crystal-clear alpine lake reflects the stunning scenery like a mirror.

[SCENE: Dense Forest]
Towering ancient trees create a dense canopy overhead, with shafts of sunlight filtering through the leaves. The forest floor is carpeted with vibrant moss and delicate ferns, while colorful mushrooms dot the landscape between gnarled roots.

[SCENE: Coastal Scene]
Waves crash against rugged cliffs as seabirds soar overhead. The setting sun paints the sky in brilliant hues of orange and purple, while the salty breeze carries the sound of the ocean's eternal rhythm.
"""

    # Create necessary directories
    temp_dir = Path("temp")
    output_dir = Path("output/example_scenes")
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the script content to a file
    script_path = temp_dir / "example_script.txt"
    with open(script_path, "w") as f:
        f.write(script_content)

    try:
        # Initialize the visual generator
        generator = VisualGenerator(
            api_key="your_leonardo_ai_api_key",
            temp_dir=str(temp_dir),
            style="cinematic, high quality, detailed",
            model_id="1e7737d7-545e-469f-857f-e4b46eaa151d"  # Default Leonardo Creative model
        )

        # Generate images for each scene
        logger.info("Generating images from script...")
        image_paths = generator.generate_scenes(str(script_path), str(output_dir))

        if not image_paths:
            logger.error("No images were generated!")
            return

        logger.info(f"Generated {len(image_paths)} images successfully!")

        # Initialize the YouTube uploader
        uploader = YouTubeUploader(
            client_secrets_file="path/to/your/client_secrets.json",
            credentials_path="path/to/your/credentials.json"
        )

        # Set up video metadata
        video_metadata = {
            "title": "Beautiful Nature Scenes",
            "description": "A journey through stunning landscapes, from majestic mountains to ancient forests and coastal vistas.",
            "tags": ["nature", "landscape", "mountains", "forest", "ocean", "cinematic", "4K"],
            "category": "22",  # People & Blogs
            "privacyStatus": "private"
        }

        # Upload the video
        logger.info("Uploading video to YouTube...")
        video_id = uploader.upload_video(
            video_path="path/to/your/video.mp4",
            **video_metadata
        )

        if video_id:
            logger.info(f"Video uploaded successfully! Video ID: {video_id}")
            
            # Update privacy to public after review
            uploader.update_video_privacy(video_id, "public")
            logger.info("Video privacy updated to public")
        else:
            logger.error("Failed to upload video")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up the generator
        if 'generator' in locals():
            generator.cleanup()

if __name__ == "__main__":
    main() 