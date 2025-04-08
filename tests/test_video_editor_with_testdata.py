import os
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, concatenate_audioclips, TextClip, CompositeVideoClip
from src.video_editing.video_editor import VideoEditor
import PIL

# Paths
TESTDATA_DIR = Path('testdata')
ANIM_DIR = TESTDATA_DIR / 'animations'
AUDIO_DIR = TESTDATA_DIR / 'audio'
VOICEOVER_DIR = TESTDATA_DIR / 'voiceover'
OUTPUT_DIR = Path('output/videos')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output video size for YouTube Shorts (9:16)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

def resize_clip(clip, target_size):
    return clip.resize(newsize=target_size)

# Collect scene clips (animations)
scene_files = sorted(ANIM_DIR.glob('*.mp4'))
scene_clips = [resize_clip(VideoFileClip(str(f)), (TARGET_WIDTH, TARGET_HEIGHT)) for f in scene_files]

# Collect background music
bg_music_path = AUDIO_DIR / 'background_music.mp3'
if not bg_music_path.exists():
    bg_music_path = None

# Collect SFX (scary and ambient)
sfx_files = sorted(list(AUDIO_DIR.glob('sfx_*.mp3')) + list(AUDIO_DIR.glob('scary_sfx_*.mp3')) + list(AUDIO_DIR.glob('ambient_sfx_*.mp3')))
sfx_paths = [str(f) for f in sfx_files]

# Collect voiceover parts
voiceover_parts = sorted(VOICEOVER_DIR.glob('voiceover_part_*.mp3'))
voiceover_clips = [AudioFileClip(str(f)) for f in voiceover_parts]

# Match number of scenes and voiceover parts
num_scenes = len(scene_clips)
num_voiceovers = len(voiceover_clips)

if num_scenes == 0 or num_voiceovers == 0:
    raise RuntimeError('No scene clips or voiceover parts found in testdata.')

# If more scenes than voiceovers, leave extra scenes silent or loop voiceovers
audio_for_scenes = []
for i in range(num_scenes):
    if i < num_voiceovers:
        audio_for_scenes.append(voiceover_clips[i])
    else:
        # Option 1: Leave silent
        audio_for_scenes.append(None)
        # Option 2: Loop voiceovers: audio_for_scenes.append(voiceover_clips[i % num_voiceovers])

# Assign each voiceover part to its scene
scene_clips_with_audio = []
for clip, audio in zip(scene_clips, audio_for_scenes):
    if audio:
        # If the audio is longer than the scene, cut it; if shorter, loop or leave as is
        if audio.duration > clip.duration:
            audio = audio.subclip(0, clip.duration)
        elif audio.duration < clip.duration:
            # Optionally, loop or leave as is; here, leave as is
            pass
        clip = clip.set_audio(audio)
    scene_clips_with_audio.append(clip)

# Concatenate the scene clips (each with its own audio)
video = concatenate_videoclips(scene_clips_with_audio, method="compose")

# Prepare audio tracks for mixing
audio_tracks = []

# Add background music at higher volume for debugging (0.5)
if bg_music_path:
    print(f"[DEBUG] Loading background music from: {bg_music_path}")
    background_music = AudioFileClip(str(bg_music_path))
    print(f"[DEBUG] Background music duration: {background_music.duration:.2f} seconds")
    if background_music.duration < video.duration:
        loops_needed = int(video.duration / background_music.duration) + 1
        print(f"[DEBUG] Looping background music {loops_needed} times to match video duration.")
        looped_clips_list = [background_music] * loops_needed
        background_music = concatenate_audioclips(looped_clips_list)
    background_music = (background_music
                        .subclip(0, video.duration)
                        .volumex(0.5))  # Raised volume for debugging
    print(f"[DEBUG] Background music final duration: {background_music.duration:.2f} seconds")
    audio_tracks.append(background_music)
else:
    print("[DEBUG] No background music found.")

# Place SFX at the start of each scene (or as many as available, no overlap)
sfx_to_use = min(len(sfx_paths), len(scene_clips_with_audio))
sfx_placements = []
current_time = 0.0
for i in range(sfx_to_use):
    sfx_placements.append(current_time)
    current_time += scene_clips_with_audio[i].duration

for sfx_path, placement in zip(sfx_paths, sfx_placements):
    try:
        print(f"[DEBUG] Adding SFX: {sfx_path} at {placement:.2f}s")
        sfx_clip = AudioFileClip(sfx_path)
        sfx_clip = sfx_clip.volumex(1.2)  # Prominent volume
        sfx_with_timing = sfx_clip.set_start(placement)
        audio_tracks.append(sfx_with_timing)
    except Exception as e:
        print(f"Failed to add SFX {sfx_path}: {e}")

# Mix all audio tracks (background music and SFX) with the video's own audio
print(f"[DEBUG] Mixing {len(audio_tracks)} additional audio tracks with video audio.")
if audio_tracks:
    combined_audio = CompositeAudioClip([video.audio] + audio_tracks)
    print(f"[DEBUG] Setting CompositeAudioClip as final video audio.")
    video = video.set_audio(combined_audio)
else:
    print("[DEBUG] No additional audio tracks to mix.")

# Optionally, generate dummy captions for testing
captions = [(0, video.duration, "Test Caption")]  # One caption for the whole video
video_editor = VideoEditor(output_dir=str(OUTPUT_DIR))
final_video = video_editor.add_captions_to_video(video, captions)

# Export the video as 9:16
output_path = OUTPUT_DIR / 'test_output.mp4'
print(f"Exporting test video to {output_path}")
video_editor.export_video(final_video, output_filename='test_output', is_short=True)

# Cleanup
for c in voiceover_clips:
    c.close()
if bg_music_path:
    background_music.close()
print("Test video creation complete!") 