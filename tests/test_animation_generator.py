import os
import pytest
import aiohttp
import tempfile
from unittest.mock import Mock, patch
from src.content_generation.animation_generator import AnimationGenerator, AnimationError, APIKeyError

@pytest.fixture
def mock_config():
    return {
        'api_keys': {
            'pika_labs': 'test_api_key'
        }
    }

@pytest.fixture
def animation_generator(mock_config):
    with tempfile.TemporaryDirectory() as temp_dir:
        yield AnimationGenerator(temp_dir, mock_config)

@pytest.mark.asyncio
async def test_animate_image_success(animation_generator):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'id': 'test_animation_id',
            'status': 'completed',
            'output_url': 'http://example.com/animation.mp4'
        }
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png') as temp_image:
            result = await animation_generator.animate_image(
                temp_image.name,
                'person',
                'walking',
                'static'
            )
            assert result.endswith('.mp4')
            assert os.path.exists(result)

@pytest.mark.asyncio
async def test_animate_image_api_error(animation_generator):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.status = 500
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        with tempfile.NamedTemporaryFile(suffix='.png') as temp_image:
            with pytest.raises(AnimationError):
                await animation_generator.animate_image(
                    temp_image.name,
                    'person',
                    'walking',
                    'static'
                )

@pytest.mark.asyncio
async def test_animate_scene_batch(animation_generator):
    scene_data = [
        {
            'image_path': 'test1.png',
            'focus_subject': 'person',
            'motion_type': 'walking',
            'camera_motion': 'static'
        },
        {
            'image_path': 'test2.png',
            'focus_subject': 'car',
            'motion_type': 'driving',
            'camera_motion': 'pan'
        }
    ]

    with patch.object(animation_generator, 'animate_image') as mock_animate:
        mock_animate.side_effect = [
            'output1.mp4',
            'output2.mp4'
        ]
        results = await animation_generator.animate_scene_batch(scene_data)
        assert len(results) == 2
        assert all(result.endswith('.mp4') for result in results)

def test_invalid_api_key():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {'api_keys': {}}
        with pytest.raises(APIKeyError):
            AnimationGenerator(temp_dir, config)

def test_cleanup_temp_files(animation_generator):
    # Create temporary files
    temp_files = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(3):
            temp_file = os.path.join(temp_dir, f'temp_animation_{i}.mp4')
            with open(temp_file, 'w') as f:
                f.write('test')
            temp_files.append(temp_file)

        # Verify files exist
        for temp_file in temp_files:
            assert os.path.exists(temp_file)

        # Clean up
        animation_generator.cleanup_temp_files()

        # Verify files are deleted
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)

def test_create_animation_prompt(animation_generator):
    prompt = animation_generator._create_animation_prompt(
        'person',
        'walking',
        'static'
    )
    assert 'person' in prompt.lower()
    assert 'walking' in prompt.lower()
    assert 'static' in prompt.lower() 