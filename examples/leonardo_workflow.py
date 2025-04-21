#!/usr/bin/env python3

"""
Complete workflow example using Leonardo AI for both image generation and animation:
1. User input collection
2. Script generation
3. Visual asset generation with Leonardo AI 
4. Image-to-video animation with Leonardo AI
5. Voiceover generation
6. Music generation
7. Video creation (local output)

Includes basic resume functionality using a state file.
"""

import os
import sys
import yaml
import logging
import colorlog
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MoviePy components
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, CompositeVideoClip, ImageClip, concatenate_audioclips

from src.content_generation.script_generator import ScriptGenerator
from src.content_generation.visual_generator import VisualGenerator
from src.content_generation.voiceover_generator import VoiceoverGenerator
from src.video_editing.video_editor import VideoEditor
from src.video_editing.leonardo_animator import LeonardoAnimator
from src.audio_generation.music_generator import MusicGenerator
from src.utils.config import Config

# --- State Management Functions ---

def save_workflow_state(state_file_path: Path, state_data: Dict[str, Any]):
    """Saves the current workflow state to a JSON file."""
    try:
        # Write to a temporary file first for atomicity
        temp_state_file = state_file_path.with_suffix('.tmp')
        with open(temp_state_file, 'w') as f:
            json.dump(state_data, f, indent=4)
        # Rename the temporary file to the actual state file
        os.replace(temp_state_file, state_file_path)
        logging.debug(f"Workflow state saved to {state_file_path}")
    except Exception as e:
        logging.warning(f"Could not save workflow state: {e}")

def load_workflow_state(state_file_path: Path) -> Optional[Dict[str, Any]]:
    """Loads the workflow state from a JSON file."""
    if state_file_path.exists():
        try:
            with open(state_file_path, 'r') as f:
                state_data = json.load(f)
                logging.info(f"Loaded previous workflow state from {state_file_path}")
                return state_data
        except Exception as e:
            logging.warning(f"Could not load workflow state file {state_file_path}: {e}. Starting fresh.")
            return None
    return None

def clear_workflow_state(state_file_path: Path):
    """Deletes the workflow state file."""
    try:
        if state_file_path.exists():
            state_file_path.unlink()
            logging.info(f"Cleared workflow state file: {state_file_path}")
    except Exception as e:
        logging.warning(f"Could not clear workflow state file: {e}")

# --- End State Management Functions ---

def setup_logging() -> None:
    """Configure colorful logging"""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s:%(name)s:%(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))

    # Configure root logger
    root_logger = colorlog.getLogger()
    if not root_logger.hasHandlers(): # Avoid adding multiple handlers
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

def create_directories(config_instance: Config) -> Tuple[Path, Path, Path, Path]:
    """Create necessary temporary and output directories."""
    # Access settings via the Config instance properties or get method
    temp_dir = Path(config_instance.get('system.temp_dir'))
    output_dir = Path(config_instance.get('system.output_dir'))
    
    # Define subdirectories
    image_dir = temp_dir / 'images'
    audio_dir = temp_dir / 'audio'
    video_output_dir = output_dir / 'videos'
    
    # Create directories
    temp_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_output_dir.mkdir(parents=True, exist_ok=True)
    
    return image_dir, audio_dir, video_output_dir, temp_dir

def get_user_input() -> Dict[str, str]:
    """Get video topic and type from user"""
    print("\n=== Video Generation Setup ===")
    
    topic = input("\nEnter video topic: ").strip()
    while not topic:
        print("Topic cannot be empty!")
        topic = input("Enter video topic: ").strip()
    
    video_type = input("\nEnter video type (short/long): ").strip().lower()
    while video_type not in ['short', 'long']:
        print("Invalid video type! Please choose: short or long")
        video_type = input("Enter video type: ").strip().lower()
    
    context = input("\nEnter additional context (optional): ").strip()
    
    return {
        'topic': topic,
        'video_type': video_type,
        'context': context
    }

def review_script(script: str) -> bool:
    """Allow user to review and approve the generated script"""
    print("\n=== Generated Script ===")
    print(script)
    
    while True:
        response = input("\nDo you approve this script? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        print("Please answer 'yes' or 'no'")

async def main():
    """Main workflow execution"""
    logger = logging.getLogger(__name__)
    state: Dict[str, Any] = {} # Dictionary to hold workflow state
    resume_mode = False

    try:
        # Setup
        setup_logging()
        logger.info("Starting YouTube AI Content Generator workflow with Leonardo AI animation")
        
        config_instance = Config()
        image_dir, audio_dir, video_output_dir, temp_dir = create_directories(config_instance)
        # Create animations directory
        animations_dir = temp_dir / 'leonardo_animations'
        animations_dir.mkdir(parents=True, exist_ok=True)
        
        state_file_path = temp_dir / "leonardo_workflow_state.json"

        # --- Resume Logic ---
        loaded_state = load_workflow_state(state_file_path)
        if loaded_state:
            print("\n--- Previous Workflow State Found ---")
            # Display some state info? (e.g., topic)
            previous_topic = loaded_state.get('user_input', {}).get('topic', 'N/A')
            print(f"Previous Topic: {previous_topic}")
            while True:
                resume_choice = input("Do you want to resume this workflow? (yes/no): ").strip().lower()
                if resume_choice in ['yes', 'y']:
                    state = loaded_state
                    resume_mode = True
                    logger.info("Resuming previous workflow.")
                    break
                elif resume_choice in ['no', 'n']:
                    logger.info("Starting a new workflow.")
                    clear_workflow_state(state_file_path) # Clear old state
                    resume_mode = False
                    break
                else:
                    print("Please answer 'yes' or 'no'.")
        # --- End Resume Logic ---

        # Get user input if not resuming
        if not resume_mode:
            state['user_input'] = get_user_input()
            save_workflow_state(state_file_path, state) # Save initial state
        else:
            # Ensure essential keys exist even when resuming
            state.setdefault('user_input', {})
            state.setdefault('script', None)
            state.setdefault('image_paths', [])
            state.setdefault('animated_video_paths', [])
            state.setdefault('voiceover_segments', [])
            state.setdefault('background_music_path', None)

        user_input = state['user_input']
        is_short = user_input.get('video_type') == "short"
        
        # Initialize components
        script_generator = ScriptGenerator(
            api_key=config_instance.get('api_keys.openai.api_key'),
            script_settings=config_instance.get('content.script')
        )
        
        visual_generator = VisualGenerator(
            api_key=config_instance.get('api_keys.leonardo.api_key'),
            temp_dir=str(image_dir),
            video_type=user_input.get('video_type', 'long'),
            model_id=config_instance.get('api_keys.leonardo.model_id', 'd69c8273-6b17-4a30-a13e-d6637ae1c644')
        )
        
        voice_generator = VoiceoverGenerator()
        
        music_generator = MusicGenerator(
            output_dir=str(audio_dir),
            config=config_instance
        )
        
        # Initialize Leonardo animator
        leonardo_animator = LeonardoAnimator(
            api_key=config_instance.get('api_keys.leonardo.api_key'),
            output_dir=str(animations_dir)
        )
        logger.info("Leonardo animator initialized successfully")
        
        video_editor = VideoEditor(
            output_dir=str(video_output_dir),
            config=config_instance
        )
        
        # Calculate placeholder audio duration (needed whether resuming or not)
        approx_duration = config_instance.get('content.music.default_duration', 180)
        animation_duration = config_instance.get('content.visual.animation.duration', 5)
        
        # Calculate target number of scenes based on total duration and animation duration per scene
        target_scene_count = max(4, int(approx_duration / animation_duration))
        logger.info(f"Target number of scenes: {target_scene_count} (based on {approx_duration}s total duration with {animation_duration}s per scene)")
        
        logger.warning(f"Using placeholder audio duration: {approx_duration}s")

        # Generate and review script
        if not state.get('script'):
            logger.info("Generating script...")
            generated_content = script_generator.generate_script(
                topic=user_input['topic'],
                video_type=user_input['video_type'],
                context=user_input.get('context', ''),
                target_scenes=target_scene_count  # Pass the target scene count
            )
            state['script'] = generated_content['script']
            # Also store SEO data if needed later
            state['seo_titles'] = generated_content['titles']
            state['seo_description'] = generated_content['description']
            state['seo_hashtags'] = generated_content['hashtags']
            state['seo_tags'] = generated_content['tags']
            save_workflow_state(state_file_path, state)
        else:
             logger.info("Script found in loaded state, skipping generation.")

        script = state['script']
        if not review_script(script):
            logger.info("Script rejected. Exiting workflow and clearing state.")
            clear_workflow_state(state_file_path) # Clear state on rejection
            return
        
        # Generate visuals
        if not state.get('image_paths'):
            logger.info("Generating visuals for each scene...")
            visual_settings = config_instance.get('content.visual')
            
            # Don't override width and height for short videos - let VisualGenerator use its defaults
            is_short = user_input.get('video_type') == 'short'
            if is_short:
                state['image_paths'] = visual_generator.generate_scenes(
                    script_text=script,
                    style=visual_settings.get('image_style', 'cinematic'),
                    target_scene_count=target_scene_count
                )
            else:
                state['image_paths'] = visual_generator.generate_scenes(
                    script_text=script,
                    style=visual_settings.get('image_style', 'cinematic'),
                    width=visual_settings.get('width', 1024),
                    height=visual_settings.get('height', 1024),
                    target_scene_count=target_scene_count
                )
                
            logger.info(f"Generated {len(state['image_paths'])} images")
            if not state['image_paths']:
                raise ValueError("No images were generated. Cannot proceed.")
            
            # Extract scene texts from script for animation prompts
            scene_texts = extract_scene_texts(script, target_scene_count)
            if scene_texts and len(scene_texts) == len(state['image_paths']):
                state['scene_texts'] = scene_texts
            else:
                # If scene text extraction fails or count doesn't match image count
                logger.warning(f"Scene text count ({len(scene_texts)}) doesn't match image count ({len(state['image_paths'])})")
                # Adjust scene texts to match image count
                if len(scene_texts) < len(state['image_paths']):
                    # Duplicate the last scene text if we have fewer scene texts than images
                    scene_texts.extend([scene_texts[-1] if scene_texts else "Generic scene"] * 
                                      (len(state['image_paths']) - len(scene_texts)))
                elif len(scene_texts) > len(state['image_paths']):
                    # Truncate if we have more scene texts than images
                    scene_texts = scene_texts[:len(state['image_paths'])]
                state['scene_texts'] = scene_texts
                
            save_workflow_state(state_file_path, state)
        else:
            logger.info(f"Found {len(state['image_paths'])} images in loaded state, skipping generation.")
            # Verify files exist?
            state['image_paths'] = [p for p in state['image_paths'] if Path(p).exists()]
            if not state['image_paths']:
                logger.warning("Image files from state not found! Re-generating.")
                raise FileNotFoundError("Image files listed in state are missing.")
                
            # Ensure scene_texts exists
            if not state.get('scene_texts') or len(state['scene_texts']) != len(state['image_paths']):
                # Extract scene texts or create empty strings
                scene_texts = extract_scene_texts(script, target_scene_count)
                if scene_texts and len(scene_texts) == len(state['image_paths']):
                    state['scene_texts'] = scene_texts
                else:
                    state['scene_texts'] = [""] * len(state['image_paths'])
                save_workflow_state(state_file_path, state)
            
        # Leonardo Animation - Animate static images into videos
        if not state.get('animated_video_paths'):
            logger.info("Animating images with Leonardo AI...")
            
            animation_prompts = []
            
            # Prepare animation prompts using scene texts
            for scene_text in state['scene_texts']:
                if scene_text:
                    # Use the scene text as input for generating an appropriate animation prompt
                    animation_prompt = leonardo_animator.generate_animation_prompt_from_scene(scene_text)
                    animation_prompts.append(animation_prompt)
                else:
                    # Fallback to a generic animation prompt
                    animation_prompts.append("Subtle camera movement, gentle animation of the scene")
            
            logger.info("Converting images to animated videos using Leonardo AI...")
            
            # Process all images in batch
            animated_video_paths = leonardo_animator.animate_images_batch(
                scene_prompts=animation_prompts,
                timeout=120  # 2 minutes timeout per animation
            )
            
            if animated_video_paths:
                logger.info(f"Successfully animated {len(animated_video_paths)} images into videos with Leonardo AI")
                state['animated_video_paths'] = animated_video_paths
                save_workflow_state(state_file_path, state)
            else:
                logger.warning("No animated videos were created. Will use static images.")
        else:
            logger.info(f"Found {len(state['animated_video_paths'])} animated videos in loaded state, skipping animation.")
            # Verify animated video files exist
            state['animated_video_paths'] = [p for p in state['animated_video_paths'] if Path(p).exists()]
            if not state['animated_video_paths'] and state['image_paths']:
                logger.warning("Animated video files from state not found! Will use static images instead.")
        
        # Generate voiceover
        if not state.get('voiceover_segments'):
            logger.info("Generating voiceover audio...")
            state['voiceover_segments'] = voice_generator.generate_voiceover(script)
            logger.info(f"Generated {len(state['voiceover_segments'])} voiceover segments")
            if not state['voiceover_segments']:
                raise ValueError("No voiceover segments were generated. Cannot proceed.")
            save_workflow_state(state_file_path, state)
        else:
            logger.info(f"Found {len(state['voiceover_segments'])} voiceover segments in loaded state, skipping generation.")
            # Verify files exist?
            state['voiceover_segments'] = [seg for seg in state['voiceover_segments'] if Path(seg.get('file')).exists()]
            if not state['voiceover_segments']:
                 logger.warning("Voiceover files from state not found! Re-generating.")
                 raise FileNotFoundError("Voiceover files listed in state are missing.")

        # Generate background music
        if not state.get('background_music_path'):
            logger.info("Generating background music...")
            music_settings = config_instance.get('content.music')
            music_prompt = music_settings.get('prompt_template', "Upbeat fantasy music for {topic}").format(topic=user_input['topic'])

            state['background_music_path'] = await music_generator.generate_background_music(
                prompt=music_prompt
            )
            logger.info(f"Generated background music: {state['background_music_path']}")
            save_workflow_state(state_file_path, state)
        else:
            logger.info(f"Background music found in loaded state: {state['background_music_path']}. Skipping generation.")
            # Verify file exists?
            if not Path(state['background_music_path']).exists():
                 logger.warning(f"Background music file {state['background_music_path']} from state not found! Re-generating.")
                 raise FileNotFoundError("Background music file listed in state is missing.")

        # Check if the content is scary/spooky
        is_scary_content = any(word in user_input['topic'].lower() for word in 
                              ['scary', 'spooky', 'horror', 'ghost', 'monster', 'halloween'])
                              
        # Download SFX based on content type
        if not state.get('sfx_paths'):
            if is_scary_content:
                logger.info("Generating scary sound effects...")
                state['sfx_paths'] = await music_generator.generate_scary_sfx(
                    count=5  # Get 5 sound effects
                )
                logger.info(f"Generated {len(state['sfx_paths'])} scary sound effects")
            else:
                logger.info("Generating general sound effects...")
                # For non-scary content, generate general SFX
                sfx_category = "ambient"  # Use ambient sounds as default
                state['sfx_paths'] = await music_generator.generate_sfx(
                    category=sfx_category,
                    count=3
                )
                logger.info(f"Generated {len(state['sfx_paths'])} {sfx_category} sound effects")
                
            save_workflow_state(state_file_path, state)
        else:
            logger.info(f"Found {len(state['sfx_paths'])} sound effects in loaded state, skipping generation.")
            # Verify files exist
            state['sfx_paths'] = [path for path in state['sfx_paths'] if Path(path).exists()]
            logger.info(f"{len(state['sfx_paths'])} sound effect files still exist")

        # Video Creation Steps
        logger.info("Proceeding to video creation...")
        image_paths = state['image_paths']
        scene_texts = state.get('scene_texts', [""] * len(image_paths))
        animated_video_paths = state.get('animated_video_paths', [])
        voiceover_segments = state['voiceover_segments']
        background_music_path = state['background_music_path']
        sfx_paths = state.get('sfx_paths', [])
        
        # Calculate scene durations based on voiceover if available
        # If not, use default durations
        if len(voiceover_segments) == len(image_paths):
            # Use voiceover segment durations
            logger.info("Using voiceover segment durations for scenes")
            scene_durations = []
            for segment in voiceover_segments:
                # Add duration metadata if available, otherwise default
                duration = segment.get('duration', 5)
                scene_durations.append(duration)
        else:
            # Calculate even distribution based on total duration
            total_audio_duration = approx_duration
            num_scenes = len(image_paths)
            scene_duration = total_audio_duration / num_scenes if num_scenes > 0 else 5
            scene_durations = [scene_duration] * num_scenes
            logger.warning(f"Using estimated scene duration: {scene_duration:.2f}s")
        
        # Create scene clips using either animated videos or static images
        scene_clips = []
        if animated_video_paths and len(animated_video_paths) == len(image_paths):
            logger.info("Using Leonardo AI animated video clips...")
            # Load animated videos
            try:
                for video_path, duration in zip(animated_video_paths, scene_durations):
                    # Load video clip
                    clip = VideoFileClip(video_path)
                    
                    # Adjust duration if needed
                    if abs(clip.duration - duration) > 0.1:  # If more than 0.1s difference
                        if clip.duration > duration:
                            # Trim
                            clip = clip.subclip(0, duration)
                        else:
                            # Loop
                            repeats = int(duration / clip.duration) + 1
                            clip = concatenate_videoclips([clip] * repeats).subclip(0, duration)
                    
                    scene_clips.append(clip)
                
                logger.info(f"Created {len(scene_clips)} video clips from Leonardo AI animated videos")
            except Exception as e:
                logger.warning(f"Failed to load animated videos: {str(e)}. Falling back to static images.")
                scene_clips = []
        
        # If no animated clips were created or loaded, create static clips
        if not scene_clips:
            logger.info("Creating static scene clips...")
            try:
                # Create scene data with image paths and text for animation
                scene_data = []
                for img_path, text in zip(image_paths, scene_texts):
                    scene_data.append({
                        'image_path': img_path,
                        'text': text
                    })
                
                # Use video editor to create scene clips (static or with Ken Burns effect)
                scene_clips = [video_editor.create_scene_clip(scene['image_path'], duration=duration, animation_prompt=None, use_animation=False) 
                               for scene, duration in zip(scene_data, scene_durations)]
                
                logger.info(f"Created {len(scene_clips)} static scene clips with Ken Burns effect")
            except Exception as e:
                logger.error(f"Failed to create scene clips: {str(e)}")
                raise

        # Combine voiceover segments if needed
        # TODO: Handle multiple voiceover segments properly (e.g., concatenate audio)
        main_voiceover_path = voiceover_segments[0]['file'] if voiceover_segments else None
        if not main_voiceover_path or not Path(main_voiceover_path).exists():
            raise ValueError("Main voiceover file not found or state is corrupted.")

        # Sync Audio
        logger.info("Synchronizing audio with video...")
        if is_scary_content and sfx_paths:
            logger.info(f"Adding {len(sfx_paths)} scary sound effects to enhance mood")
            final_video_clip = video_editor.sync_audio_with_scenes(
                scene_clips=scene_clips,
                voiceover_path=main_voiceover_path,
                background_music_path=background_music_path,
                sfx_paths=sfx_paths
            )
        else:
            final_video_clip = video_editor.sync_audio_with_scenes(
                scene_clips=scene_clips,
                voiceover_path=main_voiceover_path,
                background_music_path=background_music_path
            )

        # Add Captions
        if config_instance.get('content.captions.enabled', False):
            logger.info("Generating and adding captions...")
            # TODO: Ensure voiceover path is correct if segments were combined
            captions = video_editor.generate_captions(
                voiceover_path=main_voiceover_path,
                video_duration=final_video_clip.duration
            )
            final_video_clip = video_editor.add_captions_to_video(final_video_clip, captions)
        else:
            logger.info("Caption generation skipped.")

        # Export Video
        logger.info("Exporting final video...")
        output_filename_base = f"{user_input['topic'].replace(' ', '_')}_{user_input['video_type']}_leonardo"
        video_path = video_editor.export_video(
            video=final_video_clip,
            output_filename=output_filename_base,
            is_short=is_short
        )
        logger.info(f"Video saved to: {video_path}")

        # Generate Thumbnail
        logger.info("Generating thumbnail...")
        thumbnail_path = video_editor.generate_thumbnail(
            video=final_video_clip,
            output_filename=output_filename_base
        )
        logger.info(f"Thumbnail saved to: {thumbnail_path}")

        # Cleanup
        if config_instance.get('system.cleanup_temp_files', True):
            logger.info("Cleaning up temporary files...")
            if hasattr(visual_generator, 'cleanup'): visual_generator.cleanup()
            if hasattr(voice_generator, 'cleanup'): voice_generator.cleanup()
            if hasattr(leonardo_animator, 'cleanup'): leonardo_animator.cleanup()
            # MusicGenerator cleanup?
            if hasattr(video_editor, 'cleanup_temp_files'): video_editor.cleanup_temp_files()

        # Clear state on successful completion
        clear_workflow_state(state_file_path)
        logger.info("Workflow completed successfully!")

    except Exception as e:
        logger.error(f"An error occurred during the workflow: {str(e)}", exc_info=True)
        # Note: State file is *not* cleared on error, allowing resume
        sys.exit(1)

# Add new helper function for extracting scene texts from script
def extract_scene_texts(script: str, target_count: Optional[int] = None) -> List[str]:
    """
    Extract individual scene descriptions from the script.
    
    Args:
        script: Full script text
        target_count: Target number of scenes expected
        
    Returns:
        List of scene text descriptions
    """
    try:
        # Look for scene descriptions in square brackets
        import re
        scene_descriptions = re.findall(r'\[(.*?)\]', script)
        
        if scene_descriptions:
            if target_count and len(scene_descriptions) != target_count:
                logger.warning(f"Expected {target_count} scenes but found {len(scene_descriptions)}. " 
                             f"{'Some scenes may need to be combined.' if len(scene_descriptions) > target_count else 'Some scenes may be missing or not properly formatted.'}")
            
            logger.info(f"Successfully extracted {len(scene_descriptions)} scene descriptions from script")
            return scene_descriptions
        
        # Alternative: Split by narrator or character lines if no bracketed scenes
        logger.warning("No scene descriptions in [brackets] found. Attempting alternative extraction methods.")
        lines = script.split('\n')
        current_scene = []
        scene_texts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # If line starts with ** and ends with **, it's likely a character speaking
            if line.startswith('**') and line.endswith('**'):
                # End of previous scene description
                if current_scene:
                    scene_texts.append(' '.join(current_scene))
                    current_scene = []
            elif not line.startswith('**'):
                # Part of scene description
                current_scene.append(line)
        
        # Add the last scene if any
        if current_scene:
            scene_texts.append(' '.join(current_scene))
        
        if scene_texts:
            if target_count and len(scene_texts) != target_count:
                logger.warning(f"Alternative extraction found {len(scene_texts)} scenes, but target was {target_count}.")
            logger.info(f"Used alternative extraction to find {len(scene_texts)} scene descriptions")
            return scene_texts
        
        # Last resort: create generic scenes based on target count or script length
        if target_count:
            logger.warning("Could not extract scenes automatically. Creating generic scenes based on target count.")
            return ["Generic scene description"] * target_count
        else:
            # Estimate based on word count
            word_count = len(script.split())
            estimated_scenes = max(1, word_count // 100)  # Rough estimate: 1 scene per 100 words
            logger.warning(f"Could not extract scenes automatically. Creating {estimated_scenes} generic scenes based on script length.")
            return ["Generic scene description"] * estimated_scenes
            
    except Exception as e:
        logging.warning(f"Failed to extract scene texts: {str(e)}")
        # Return generic fallback scenes
        return ["Generic scene"] * (target_count if target_count else 8)

if __name__ == "__main__":
    asyncio.run(main()) 