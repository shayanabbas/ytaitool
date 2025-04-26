#!/usr/bin/env python3

"""Test cases for the MusicGenerator class."""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
import requests
from src.audio_generation.music_generator import (
    MusicGenerator,
    MusicGenerationError,
    SFXDownloadError,
    APIKeyError
)
from src.utils.config import Config

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=Config)
    config.get.side_effect = lambda x: {
        'apis.suno.api_key': 'mock_suno_key',
        'apis.pixabay.api_key': 'mock_pixabay_key'
    }.get(x)
    return config

@pytest.fixture
def mock_config_missing_keys():
    """Create a mock configuration with missing API keys."""
    config = Mock(spec=Config)
    config.get.return_value = None
    return config

@pytest.fixture
def music_generator(tmp_path, mock_config):
    """Create a MusicGenerator instance with temporary directory."""
    return MusicGenerator(str(tmp_path), mock_config)

def test_init_missing_suno_key(tmp_path, mock_config_missing_keys):
    """Test initialization with missing Suno API key."""
    with pytest.raises(APIKeyError) as exc_info:
        MusicGenerator(str(tmp_path), mock_config_missing_keys)
    assert "Suno AI API key not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_background_music_success(music_generator):
    """Test successful background music generation."""
    mock_response = Mock()
    mock_response.json.return_value = {'audio_url': 'http://example.com/music.mp3'}
    mock_response.content = b'mock_audio_data'
    
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        mock_post.return_value = mock_response
        mock_get.return_value = mock_response
        
        output_path = await music_generator.generate_background_music(
            prompt="Test music",
            duration=30.0
        )
        
        assert os.path.exists(output_path)
        assert output_path.endswith('.mp3')

@pytest.mark.asyncio
async def test_generate_background_music_no_url(music_generator):
    """Test handling of missing audio URL in response."""
    mock_response = Mock()
    mock_response.json.return_value = {}  # Empty response without audio_url
    
    with patch('requests.post') as mock_post:
        mock_post.return_value = mock_response
        
        with pytest.raises(MusicGenerationError) as exc_info:
            await music_generator.generate_background_music(
                prompt="Test music",
                duration=30.0
            )
        assert "No audio URL in API response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_background_music_request_error(music_generator):
    """Test handling of request errors in music generation."""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.RequestException("Connection error")
        
        with pytest.raises(MusicGenerationError) as exc_info:
            await music_generator.generate_background_music(
                prompt="Test music",
                duration=30.0
            )
        assert "API request failed" in str(exc_info.value)
        assert "Connection error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_download_sfx_invalid_category(music_generator):
    """Test handling of invalid SFX category."""
    with pytest.raises(ValueError) as exc_info:
        await music_generator.download_sfx(
            category='invalid_category',
            max_duration=5.0
        )
    assert "Invalid SFX category" in str(exc_info.value)

@pytest.mark.asyncio
async def test_download_sfx_request_error(music_generator):
    """Test handling of request errors in SFX download."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(SFXDownloadError) as exc_info:
            await music_generator.download_sfx(
                category='magic',
                max_duration=5.0
            )
        assert "API request failed" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_download_sfx_partial_failure(music_generator):
    """Test handling of partial failures in SFX download."""
    mock_search_response = Mock()
    mock_search_response.json.return_value = {
        'hits': [
            {'id': '1', 'audio_url': 'http://example.com/sfx1.mp3'},
            {'id': '2', 'audio_url': 'http://example.com/sfx2.mp3'}
        ]
    }
    
    def mock_get_side_effect(url, **kwargs):
        if 'pixabay.com/api/audio' in url:
            return mock_search_response
        elif 'sfx1.mp3' in url:
            return Mock(content=b'audio1')
        else:
            raise requests.RequestException("Download failed")
    
    with patch('requests.get', side_effect=mock_get_side_effect):
        paths = await music_generator.download_sfx(
            category='magic',
            max_duration=5.0
        )
        assert len(paths) == 1  # Only one file should be successfully downloaded

@pytest.mark.asyncio
async def test_download_sfx_all_downloads_fail(music_generator):
    """Test handling of all SFX downloads failing."""
    mock_search_response = Mock()
    mock_search_response.json.return_value = {
        'hits': [
            {'id': '1', 'audio_url': 'http://example.com/sfx1.mp3'},
            {'id': '2', 'audio_url': 'http://example.com/sfx2.mp3'}
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            mock_search_response,  # First call for search
            requests.RequestException("Download failed"),  # First download
            requests.RequestException("Download failed")   # Second download
        ]
        
        with pytest.raises(SFXDownloadError) as exc_info:
            await music_generator.download_sfx(
                category='magic',
                max_duration=5.0
            )
        assert "Failed to download any sound effects" in str(exc_info.value)

def test_cleanup_temp_files_permission_error(music_generator, tmp_path):
    """Test handling of permission errors during cleanup."""
    temp_file = tmp_path / 'test.temp.mp3'
    temp_file.touch()
    
    with patch('pathlib.Path.unlink', side_effect=PermissionError("Permission denied")):
        music_generator.cleanup_temp_files()
        assert temp_file.exists()  # File should still exist due to permission error

def test_cleanup_temp_files(music_generator, tmp_path):
    """Test cleanup of temporary files."""
    # Create some temp files
    temp_files = [
        tmp_path / 'test1.temp.mp3',
        tmp_path / 'test2.temp.mp3'
    ]
    for file in temp_files:
        file.touch()
    
    music_generator.cleanup_temp_files()
    
    # Verify files are deleted
    for file in temp_files:
        assert not file.exists()

def test_cleanup_temp_files_no_files(music_generator):
    """Test cleanup when no temporary files exist."""
    try:
        music_generator.cleanup_temp_files()
    except Exception as e:
        pytest.fail(f"cleanup_temp_files raised {e} unexpectedly!")

def test_invalid_category(music_generator):
    """Test handling of invalid SFX category."""
    assert music_generator.sfx_categories.get('invalid') is None
    assert music_generator.sfx_categories.get('magic') is not None 