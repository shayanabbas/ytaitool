# YouTube AI Content Generator

This project is an end-to-end pipeline for generating YouTube-ready videos using AI for script writing, image generation, animation, voiceover, background music, sound effects, and video editing. It supports both full AI-powered workflows and local testing with pre-generated assets to save on API costs.

---

## Features
- **Script Generation**: Uses AI to generate engaging scripts based on your topic.
- **Visual Generation**: Creates images and animations for each scene.
- **Voiceover**: Generates voiceover audio for each scene.
- **Music & SFX**: Adds background music and sound effects.
- **Video Editing**: Assembles everything into a final video with captions and transitions.
- **Test Mode**: Use local test data to avoid API costs during development.

---

## Directory Structure
```
.
├── src/                # Main source code (modularized by function)
├── testdata/           # Pre-generated test assets (animations, audio, voiceover)
├── output/videos/      # Final rendered videos
├── tests/              # Test scripts
├── examples/           # Example workflows
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── ...
```

---

## Setup
1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure API keys** (for full workflow):
   - Copy your config example and fill in your API keys for OpenAI, ElevenLabs, Suno, Leonardo, PixVerse, etc.
   - Place your config file in the appropriate location (see `src/utils/config.py` for details).

---

## Running the Full AI Workflow
To generate a video using all AI features:
```bash
python examples/complete_workflow.py
```
- You will be prompted for a topic and video type.
- The workflow will generate all assets and assemble the video.
- Output will be in `output/videos/`.

---

## Running with Test Data (No API Costs)
To assemble a video using only pre-generated test assets:
```bash
PYTHONPATH=. python tests/test_video_editor_with_testdata.py
```
- This uses files from `testdata/animations/`, `testdata/audio/`, and `testdata/voiceover/`.
- No API calls are made.
- Output will be in `output/videos/test_output.mp4`.

---

## Test Data Structure
- Place your test assets as follows:
  - `testdata/animations/scene_001.mp4`, ...
  - `testdata/audio/background_music_*.mp3`, `testdata/audio/sfx_*.mp3`, ...
  - `testdata/voiceover/voiceover_part_001.mp3`, ...

---

## Troubleshooting
- **ModuleNotFoundError**: Run scripts with `PYTHONPATH=.` or as a module (e.g., `python -m tests.test_video_editor_with_testdata`).
- **Pillow/ANTIALIAS error**: The test script patches this automatically for compatibility with Pillow 10+.
- **No background music found**: Ensure your background music files are in `testdata/audio/` and named like `background_music_*.mp3`.
- **API costs**: Use the test script to avoid unnecessary API calls during development.

---

## Contributing
Pull requests and issues are welcome! Please:
- Follow the code style and modular structure.
- Add tests for new features.
- Document any new configuration or dependencies.

---

## License
[MIT License](LICENSE) 