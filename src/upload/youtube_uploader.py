"""
YouTube video uploader module.
"""

import os
import pickle
import logging
import time
from typing import List, Optional, Dict, Any

import googleapiclient.discovery
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from dateutil import parser

# Configure logger
logger = logging.getLogger(__name__)

class YouTubeUploader:
    """
    Class for uploading videos to YouTube via the YouTube Data API.
    """
    
    # YouTube API constants
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
              'https://www.googleapis.com/auth/youtube',
              'https://www.googleapis.com/auth/youtube.force-ssl']

    def __init__(self, client_secrets_file: str, credentials_path: str):
        """
        Initialize the YouTube uploader.
        
        Args:
            client_secrets_file (str): Path to the client secrets JSON file
            credentials_path (str): Path to store/load OAuth credentials
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_path = credentials_path
        self.credentials = None
        self.youtube = None
        
        # Check if client secrets file exists
        if not os.path.exists(client_secrets_file):
            logger.error(f"Client secrets file not found: {client_secrets_file}")
        
        # Ensure credentials directory exists
        os.makedirs(os.path.dirname(credentials_path), exist_ok=True)
        
        # Attempt authentication on initialization
        self._authenticate()

    def _authenticate(self) -> bool:
        """
        Authenticate with the YouTube API using OAuth.
        
        Returns:
            bool: True if authentication is successful, False otherwise
        """
        # Check if client secrets file exists
        if not os.path.exists(self.client_secrets_file):
            logger.error(f"Client secrets file not found: {self.client_secrets_file}")
            return False
            
        # Ensure credentials directory exists
        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
        
        try:
            # Try to load existing credentials
            if os.path.exists(self.credentials_path):
                with open(self.credentials_path, 'rb') as token:
                    self.credentials = pickle.load(token)
                    
                logger.debug("Loaded existing credentials")
                
                # Check if credentials are expired and refresh if needed
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.debug("Credentials expired, refreshing...")
                    try:
                        self.credentials.refresh(Request())
                        logger.debug("Credentials refreshed successfully")
                        # Save refreshed credentials
                        with open(self.credentials_path, 'wb') as token:
                            pickle.dump(self.credentials, token)
                    except RefreshError as e:
                        logger.warning(f"Failed to refresh credentials: {e}. Need to re-authenticate.")
                        self.credentials = None
                        
            # If no valid credentials, run the OAuth flow
            if not self.credentials or not self.credentials.valid:
                logger.info("No valid credentials found, starting OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.SCOPES)
                self.credentials = flow.run_local_server(port=0)
                
                # Save the new credentials
                with open(self.credentials_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                logger.info("Authentication completed and credentials saved")
            
            # Test credentials by building the service
            self.youtube = googleapiclient.discovery.build(
                self.API_SERVICE_NAME, self.API_VERSION, credentials=self.credentials)
            logger.info("Successfully authenticated with YouTube API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self.youtube = None
            return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = 'unlisted',
        category_id: str = '22',
        thumbnail_path: str = None,
        made_for_kids: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a video to YouTube.

        Args:
            video_path (str): Path to the video file
            title (str): Video title
            description (str): Video description
            tags (List[str]): List of tags for the video
            privacy_status (str, optional): Privacy status - 'public', 'unlisted', or 'private'. Defaults to 'unlisted'.
            category_id (str, optional): YouTube category ID. Defaults to '22' (People & Blogs).
            thumbnail_path (str, optional): Path to thumbnail image. Defaults to None.
            made_for_kids (bool, optional): Whether this content is made for kids. Defaults to False.

        Returns:
            Optional[Dict[str, Any]]: Response from YouTube API or None if upload fails
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        if not self._authenticate():
            logger.error("Failed to authenticate with YouTube API")
            return None

        if privacy_status not in ['public', 'unlisted', 'private']:
            logger.warning(f"Invalid privacy status '{privacy_status}', defaulting to 'unlisted'")
            privacy_status = 'unlisted'

        try:
            logger.info(f"Uploading video: {title}")
            
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': made_for_kids
                }
            }

            # Create upload request
            media = MediaFileUpload(
                video_path,
                mimetype='video/*',
                resumable=True,
                chunksize=1024*1024*5  # 5MB chunks
            )
            
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            # Execute chunked upload with retries and progress reporting
            response = self._execute_upload_request(request)
            
            if response:
                video_id = response.get('id')
                logger.info(f"Video uploaded successfully, ID: {video_id}")
                
                # Set thumbnail if provided
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self._set_thumbnail(video_id, thumbnail_path)
                
                return response
            else:
                logger.error("Upload failed, received empty response")
                return None

        except HttpError as e:
            logger.error(f"HTTP error during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            return None

    def update_video(
        self,
        video_id: str,
        title: str = None,
        description: str = None,
        tags: List[str] = None,
        category_id: str = None,
        privacy_status: str = None,
        made_for_kids: bool = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update metadata for an existing YouTube video.
        
        Args:
            video_id (str): The YouTube video ID to update
            title (str, optional): New video title. Defaults to None.
            description (str, optional): New video description. Defaults to None.
            tags (List[str], optional): New list of tags. Defaults to None.
            category_id (str, optional): New category ID. Defaults to None.
            privacy_status (str, optional): New privacy status. Defaults to None.
            made_for_kids (bool, optional): Whether content is made for kids. Defaults to None.
            
        Returns:
            Optional[Dict[str, Any]]: The updated video resource or None if update fails
        """
        if not self._authenticate():
            logger.error("Failed to authenticate with YouTube API")
            return None
            
        # Build parts and body dictionaries
        parts = []
        body = {'id': video_id}
        
        # Add snippet properties if any are provided
        snippet = {}
        if title is not None:
            snippet['title'] = title
        if description is not None:
            snippet['description'] = description
        if tags is not None:
            snippet['tags'] = tags
        if category_id is not None:
            snippet['categoryId'] = category_id
            
        if snippet:
            parts.append('snippet')
            body['snippet'] = snippet
            
        # Add status properties if any are provided
        status = {}
        if privacy_status is not None:
            if privacy_status not in ['public', 'unlisted', 'private']:
                logger.warning(f"Invalid privacy status '{privacy_status}', defaulting to 'unlisted'")
                privacy_status = 'unlisted'
            status['privacyStatus'] = privacy_status
            
        if made_for_kids is not None:
            status['selfDeclaredMadeForKids'] = made_for_kids
            
        if status:
            parts.append('status')
            body['status'] = status
            
        # If nothing to update, return early
        if not parts:
            logger.warning("No properties provided for update")
            return None
            
        try:
            logger.info(f"Updating video {video_id}")
            
            response = self.youtube.videos().update(
                part=','.join(parts),
                body=body
            ).execute()
            
            logger.info(f"Video {video_id} updated successfully")
            return response
            
        except HttpError as e:
            logger.error(f"HTTP error updating video: {e}")
            return None
        except Exception as e:
            logger.error(f"Error updating video: {e}")
            return None
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from YouTube.
        
        Args:
            video_id (str): The YouTube video ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._authenticate():
            logger.error("Failed to authenticate with YouTube API")
            return False
            
        try:
            logger.info(f"Deleting video {video_id}")
            
            self.youtube.videos().delete(
                id=video_id
            ).execute()
            
            logger.info(f"Video {video_id} deleted successfully")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error deleting video: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            return False

    def _set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Set a thumbnail for a video.
        
        Args:
            video_id (str): YouTube video ID
            thumbnail_path (str): Path to thumbnail image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(thumbnail_path):
            logger.error(f"Thumbnail file not found: {thumbnail_path}")
            return False
            
        try:
            logger.info(f"Setting thumbnail for video {video_id}")
                
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            )
            response = request.execute()
            
            logger.info(f"Thumbnail set successfully for video {video_id}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error setting thumbnail: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")
            return False

    def _execute_upload_request(self, request):
        """
        Execute a resumable upload request with progress reporting.
        
        Args:
            request: The YouTube API upload request object
            
        Returns:
            dict: The response from the YouTube API if successful
            
        Raises:
            Exception: If upload fails after retries
        """
        response = None
        error = None
        retry = 0
        max_retries = 10
        
        logger.info("Starting chunked upload")
        
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Server error, retry with exponential backoff
                    retry += 1
                    if retry > max_retries:
                        logger.error(f"Upload failed after {max_retries} retries")
                        raise Exception(f"Upload failed after {max_retries} retries: {e}")
                    
                    sleep_seconds = 2 ** retry
                    logger.warning(f"Retrying upload in {sleep_seconds} seconds... (Attempt {retry}/{max_retries})")
                    time.sleep(sleep_seconds)
                else:
                    # Other HTTP errors are fatal
                    logger.error(f"HTTP error during upload: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error during upload: {e}")
                raise
        
        return response 
