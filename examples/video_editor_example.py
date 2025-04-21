#!/usr/bin/env python3

"""Example script demonstrating the usage of the VideoEditor class."""

import os
from pathlib import Path
from src.video_editing.video_editor import VideoEditor

def main():
    # Initialize VideoEditor with output directory
    output_dir = Path("output/videos")
    editor = VideoEditor(str(output_dir))
    
    # Example paths (replace with your actual paths)
    image_paths = [
        "assets/scene1.jpg",
        "assets/scene2.jpg",
        "assets/scene3.jpg"
    ]
    voiceover_path = "assets/voiceover.wav"
    background_music_path = "assets/background_music.mp3"
    
    # Create scene clips with Ken Burns effect
    scene_clips = []
    for image_path in image_paths:
        # Each scene is 10 seconds long with zoom effect
        clip = editor.create_scene_clip(
            image_path=image_path,
            duration=10.0,
            zoom_effect=True,
            zoom_scale=1.1
        )
        scene_clips.append(clip)
    
    # Apply transitions between scenes
    video_with_transitions = editor.apply_transitions(
        clips=scene_clips,
        transition_type='crossfade'
    )
    
    # Generate captions from voiceover
    captions = editor.generate_captions(
        voiceover_path=voiceover_path,
        video_duration=video_with_transitions.duration
    )
    
    # Synchronize audio and add captions
    video_with_audio = editor.sync_audio_with_scenes(
        scene_clips=scene_clips,
        voiceover_path=voiceover_path,
        background_music_path=background_music_path
    )
    
    # Add captions to video
    final_video = editor.add_captions_to_video(
        video=video_with_audio,
        captions=captions
    )
    
    # Export the video (both regular and short versions)
    regular_video_path = editor.export_video(
        video=final_video,
        output_filename="my_video",
        is_short=False
    )
    
    short_video_path = editor.export_video(
        video=final_video,
        output_filename="my_video_short",
        is_short=True
    )
    
    # Generate thumbnails
    regular_thumbnail = editor.generate_thumbnail(
        video=final_video,
        output_filename="my_video",
        time_position=0.5  # Take thumbnail from middle of video
    )
    
    # Clean up temporary files
    editor.cleanup_temp_files()
    
    print(f"Regular video exported to: {regular_video_path}")
    print(f"Short version exported to: {short_video_path}")
    print(f"Thumbnail generated at: {regular_thumbnail}")

if __name__ == "__main__":
    main() 