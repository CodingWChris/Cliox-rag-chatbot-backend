"""
S3 Conversation Storage Service
Handles storing and retrieving conversation data from AWS S3
"""

import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Single message in a conversation"""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConversationMetadata:
    """Session metadata information"""
    session_id: str
    created_at: str
    last_updated: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    last_activity: str
    
@dataclass
class ConversationSummary:
    """Conversation summary for contextual understanding"""
    session_id: str
    summary_version: str
    created_at: str
    last_updated: str
    conversation_summary: str
    key_topics: List[str]
    user_context: str
    messages_summarized: int
    last_message_id: str

class S3ConversationService:
    """Service for managing conversation storage in S3"""
    
    def __init__(self):
        self.bucket_name = settings.s3_conversation_bucket
        self.region = settings.aws_default_region
        self._s3_client = None
        
    @property
    def s3_client(self):
        """Lazy initialization of S3 client"""
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=self.region
                )
                logger.info(f"🔗 S3 client initialized for bucket: {self.bucket_name}")
            except NoCredentialsError:
                logger.error("❌ AWS credentials not found")
                raise
            except Exception as e:
                logger.error(f"❌ Failed to initialize S3 client: {e}")
                raise
        return self._s3_client
    
    def _get_session_key(self, session_id: str, file_type: str) -> str:
        """Generate S3 key for session file"""
        return f"conversations/{session_id}/{file_type}.json"
    
    async def save_message(self, session_id: str, message: ConversationMessage) -> bool:
        """Add a new message to the conversation"""
        try:
            logger.info(f"💬 Saving message for session {session_id}: {message.role}")
            
            # Load existing conversation
            conversation = await self._load_json(
                self._get_session_key(session_id, "messages")
            )
            
            if not conversation:
                # First message for this session - initialize conversation
                logger.info(f"📝 Initializing conversation for session {session_id}")
                now = datetime.now(timezone.utc).isoformat()
                conversation = {
                    "session_id": session_id,
                    "created_at": now,
                    "messages": []
                }
                
                # Also create initial metadata
                metadata = ConversationMetadata(
                    session_id=session_id,
                    created_at=now,
                    last_updated=now,
                    total_messages=0,
                    user_messages=0,
                    assistant_messages=0,
                    last_activity=now
                )
                
                await self._save_json(
                    self._get_session_key(session_id, "metadata"),
                    asdict(metadata)
                )
            
            # Add new message
            conversation["messages"].append(asdict(message))
            conversation["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Save updated conversation
            await self._save_json(
                self._get_session_key(session_id, "messages"),
                conversation
            )
            
            # Update metadata
            await self._update_metadata(session_id, message.role)
            
            logger.info(f"✅ Message saved for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save message for session {session_id}: {e}")
            return False
    
    async def load_conversation(self, session_id: str) -> Optional[List[ConversationMessage]]:
        """Load full conversation history"""
        try:
            conversation = await self._load_json(
                self._get_session_key(session_id, "messages")
            )
            
            if not conversation:
                logger.info(f"📭 No conversation found for session {session_id}")
                return None
            
            messages = [
                ConversationMessage(**msg) 
                for msg in conversation.get("messages", [])
            ]
            
            logger.info(f"📚 Loaded {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Failed to load conversation for session {session_id}: {e}")
            return None
    
    async def load_recent_messages(self, session_id: str, limit: int = 10) -> Optional[List[ConversationMessage]]:
        """Load recent messages from conversation"""
        try:
            messages = await self.load_conversation(session_id)
            if not messages:
                return None
            
            recent = messages[-limit:] if len(messages) > limit else messages
            logger.info(f"📱 Loaded {len(recent)} recent messages for session {session_id}")
            return recent
            
        except Exception as e:
            logger.error(f"❌ Failed to load recent messages for session {session_id}: {e}")
            return None
    
    async def save_summary(self, session_id: str, summary: ConversationSummary) -> bool:
        """Save conversation summary"""
        try:
            logger.info(f"📄 Saving summary for session {session_id}")
            
            await self._save_json(
                self._get_session_key(session_id, "summary"),
                asdict(summary)
            )
            
            logger.info(f"✅ Summary saved for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save summary for session {session_id}: {e}")
            return False
    
    async def load_summary(self, session_id: str) -> Optional[ConversationSummary]:
        """Load conversation summary"""
        try:
            summary_data = await self._load_json(
                self._get_session_key(session_id, "summary")
            )
            
            if not summary_data:
                logger.info(f"📭 No summary found for session {session_id}")
                return None
            
            summary = ConversationSummary(**summary_data)
            logger.info(f"📄 Loaded summary for session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to load summary for session {session_id}: {e}")
            return None
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if session exists in S3"""
        try:
            metadata_key = self._get_session_key(session_id, "metadata")
            
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=metadata_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete all session files from S3"""
        try:
            logger.info(f"🗑️ Deleting session {session_id}")
            
            # Delete all session files
            files_to_delete = ["metadata", "messages", "summary"]
            
            for file_type in files_to_delete:
                key = self._get_session_key(session_id, file_type)
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                except ClientError as e:
                    if e.response['Error']['Code'] != '404':
                        raise
            
            logger.info(f"✅ Session {session_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {e}")
            return False
    
    async def _save_json(self, key: str, data: Dict) -> None:
        """Save JSON data to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(data, indent=2),
                ContentType="application/json",
                ServerSideEncryption="AES256"
            )
        except Exception as e:
            logger.error(f"❌ Failed to save {key} to S3: {e}")
            raise
    
    async def _load_json(self, key: str) -> Optional[Dict]:
        """Load JSON data from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            logger.error(f"❌ Failed to load {key} from S3: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load {key} from S3: {e}")
            raise
    
    async def _update_metadata(self, session_id: str, message_role: str) -> None:
        """Update session metadata after adding a message"""
        try:
            metadata_data = await self._load_json(
                self._get_session_key(session_id, "metadata")
            )
            
            if metadata_data:
                metadata_data["last_updated"] = datetime.now(timezone.utc).isoformat()
                metadata_data["last_activity"] = datetime.now(timezone.utc).isoformat()
                metadata_data["total_messages"] += 1
                
                if message_role == "user":
                    metadata_data["user_messages"] += 1
                elif message_role == "assistant":
                    metadata_data["assistant_messages"] += 1
                
                await self._save_json(
                    self._get_session_key(session_id, "metadata"),
                    metadata_data
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to update metadata for session {session_id}: {e}")

# Global instance
conversation_storage = S3ConversationService()
