import os
import pickle
import time
from typing import Dict, Optional, List
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from ..utils.logger import logger

class YouTubeUploader:
    def __init__(self, client_secrets_file: str, credentials_path: str, scopes: List[str] = ['https://www.googleapis.com/auth/youtube.upload']):
        """
        Initialize the YouTube uploader.
        
        Args:
            client_secrets_file: Path to the OAuth 2.0 client secrets file.
            credentials_path: Path to store/load user credentials.
            scopes: List of OAuth 2.0 scopes required.
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_path = credentials_path
        self.scopes = scopes
        self.credentials = None
        self.youtube = None
        
        # Ensure the directory for credentials exists
        credentials_dir = os.path.dirname(self.credentials_path)
        if credentials_dir:
            os.makedirs(credentials_dir, exist_ok=True)

    def _authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        try:
            # Load existing credentials
            if os.path.exists(self.credentials_path):
                with open(self.credentials_path, 'rb') as token:
                    self.credentials = pickle.load(token)
                    logger.info(f"Loaded credentials from {self.credentials_path}")

            # Refresh or get new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    logger.info("Credentials refreshed successfully.")
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, self.scopes)
                    self.credentials = flow.run_local_server(port=0)  # Let the system pick an available port
                    logger.info("Authentication successful.")

                # Save credentials
                with open(self.credentials_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                    logger.info(f"Credentials saved to {self.credentials_path}")

            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def _create_metadata(
        self,
        title: str,
        description: str,
        tags: list,
        privacy: str,
        publish_at: Optional[datetime] = None
    ) -> Dict:
        """Create video metadata for upload."""
        metadata = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }
        
        if publish_at and privacy == 'private':
            metadata['status']['publishAt'] = publish_at.isoformat()
        
        return metadata

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        privacy_status: str = 'private',
        publish_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Optional[str]:
        """Upload video to YouTube with metadata."""
        try:
            if not self._authenticate():
                raise Exception("YouTube authentication failed")

            logger.info("Starting YouTube upload...")
            
            # Prepare metadata
            metadata = self._create_metadata(title, description, tags, privacy_status, publish_at)
            
            # Prepare media file
            media = MediaFileUpload(
                video_path,
                mimetype='video/mp4',
                chunksize=1024*1024,
                resumable=True
            )
            
            # Start upload
            upload_request = self.youtube.videos().insert(
                part=','.join(metadata.keys()),
                body=metadata,
                media_body=media
            )
            
            # Handle upload with progress tracking and retries
            response = None
            retries = 0
            
            while response is None and retries < max_retries:
                try:
                    status, response = upload_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Upload progress: {progress}%")
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    logger.warning(f"Upload chunk failed, retrying... ({retries}/{max_retries})")
                    time.sleep(retry_delay)

            if response:
                video_id = response['id']
                logger.info(f"Video uploaded successfully! Video ID: {video_id}")
                
                if publish_at:
                    logger.info(f"Video scheduled for publication at {publish_at}")
                
                return video_id
            
            raise Exception("Upload failed after maximum retries")
            
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return None 