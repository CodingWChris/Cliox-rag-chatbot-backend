"""
Conversation Summarization Service
Handles creating and updating conversation summaries for contextual understanding
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from .s3_conversation_service import (
    conversation_storage, 
    ConversationMessage, 
    ConversationSummary
)
from .ollama_service import ollama_service, OllamaRequest
from ..config.settings import settings

logger = logging.getLogger(__name__)

class ConversationSummarizationService:
    """Service for creating and managing conversation summaries"""
    
    def __init__(self):
        self.summary_threshold = settings.conversation_summary_threshold
        self.max_tokens = 300  # Keep summaries concise
    
    async def should_update_summary(self, session_id: str) -> bool:
        """Determine if conversation summary needs updating"""
        try:
            # Load conversation and current summary
            messages = await conversation_storage.load_conversation(session_id)
            current_summary = await conversation_storage.load_summary(session_id)
            
            if not messages:
                return False
            
            # If no summary exists and we have enough messages, create one
            if not current_summary and len(messages) >= self.summary_threshold:
                logger.info(f"📊 No summary exists for session {session_id}, creating first summary")
                return True
            
            # If summary exists, check if we have enough new messages
            if current_summary:
                messages_since_summary = len(messages) - current_summary.messages_summarized
                if messages_since_summary >= self.summary_threshold:
                    logger.info(f"📊 {messages_since_summary} new messages for session {session_id}, updating summary")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking summary update need for session {session_id}: {e}")
            return False
    
    async def generate_summary(self, session_id: str) -> Optional[ConversationSummary]:
        """Generate or update conversation summary"""
        try:
            logger.info(f"🧠 Generating summary for session {session_id}")
            
            # Load full conversation
            messages = await conversation_storage.load_conversation(session_id)
            if not messages:
                logger.warning(f"⚠️ No messages found for session {session_id}")
                return None
            
            # Load existing summary if available
            current_summary = await conversation_storage.load_summary(session_id)
            
            # Build prompt for summarization
            summary_prompt = self._build_summary_prompt(messages, current_summary)
            
            # Generate summary using Ollama
            ollama_request = OllamaRequest(
                model=settings.default_model,
                prompt=summary_prompt,
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=self.max_tokens
            )
            
            summary_response = await ollama_service.generate(ollama_request)
            
            # Parse the generated summary
            summary_content = summary_response.response.strip()
            
            # Extract structured information from the summary
            parsed_summary = self._parse_summary_response(summary_content)
            
            # Create summary object
            now = datetime.now(timezone.utc).isoformat()
            version = "v1.0" if not current_summary else f"v{float(current_summary.summary_version[1:]) + 0.1:.1f}"
            
            conversation_summary = ConversationSummary(
                session_id=session_id,
                summary_version=version,
                created_at=current_summary.created_at if current_summary else now,
                last_updated=now,
                conversation_summary=parsed_summary.get("summary", summary_content),
                key_topics=parsed_summary.get("topics", []),
                user_context=parsed_summary.get("user_context", ""),
                messages_summarized=len(messages),
                last_message_id=messages[-1].id if messages else ""
            )
            
            # Save summary
            success = await conversation_storage.save_summary(session_id, conversation_summary)
            
            if success:
                logger.info(f"✅ Summary generated successfully for session {session_id}")
                return conversation_summary
            else:
                logger.error(f"❌ Failed to save summary for session {session_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to generate summary for session {session_id}: {e}")
            return None
    
    def _build_summary_prompt(self, messages: List[ConversationMessage], current_summary: Optional[ConversationSummary]) -> str:
        """Build prompt for conversation summarization"""
        
        # Format conversation history
        conversation_text = self._format_messages_for_prompt(messages)
        
        if current_summary:
            # Update existing summary
            prompt = f"""You are updating an existing conversation summary. 

Previous Summary:
{current_summary.conversation_summary}

Previous Key Topics: {', '.join(current_summary.key_topics)}

Previous User Context: {current_summary.user_context}

Full Conversation (including new messages):
{conversation_text}

Create an updated comprehensive summary that incorporates both the previous context and new information. Include:

1. SUMMARY: A brief overview of the entire conversation (2-3 sentences)
2. KEY_TOPICS: Important topics discussed (comma-separated list)
3. USER_CONTEXT: User's goals, preferences, background, and ongoing needs (1-2 sentences)

Format your response as:
SUMMARY: [your summary here]
KEY_TOPICS: [topic1, topic2, topic3]
USER_CONTEXT: [user context here]"""
        else:
            # Create new summary
            prompt = f"""Analyze this conversation and create a concise summary for future context.

Conversation:
{conversation_text}

Create a summary that captures:

1. SUMMARY: What has been discussed and any important conclusions (2-3 sentences)
2. KEY_TOPICS: Main topics covered (comma-separated list)
3. USER_CONTEXT: User's goals, preferences, background, and what they're trying to achieve (1-2 sentences)

Format your response as:
SUMMARY: [your summary here]
KEY_TOPICS: [topic1, topic2, topic3]
USER_CONTEXT: [user context here]"""
        
        return prompt
    
    def _format_messages_for_prompt(self, messages: List[ConversationMessage]) -> str:
        """Format messages for inclusion in summary prompt"""
        formatted_messages = []
        
        for msg in messages:
            role = "User" if msg.role == "user" else "Assistant"
            # Truncate very long messages to prevent prompt overflow
            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            formatted_messages.append(f"{role}: {content}")
        
        return "\n\n".join(formatted_messages)
    
    def _parse_summary_response(self, response: str) -> dict:
        """Parse the structured summary response from Ollama"""
        parsed = {
            "summary": "",
            "topics": [],
            "user_context": ""
        }
        
        try:
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("SUMMARY:"):
                    parsed["summary"] = line[8:].strip()
                elif line.startswith("KEY_TOPICS:"):
                    topics_str = line[11:].strip()
                    parsed["topics"] = [topic.strip() for topic in topics_str.split(',') if topic.strip()]
                elif line.startswith("USER_CONTEXT:"):
                    parsed["user_context"] = line[13:].strip()
            
            # Fallback: if parsing failed, use the whole response as summary
            if not parsed["summary"]:
                parsed["summary"] = response
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse summary response, using raw response: {e}")
            parsed["summary"] = response
        
        return parsed
    
    async def get_conversation_context(self, session_id: str, max_tokens: int = 1000) -> str:
        """Get conversation context for chat responses (summary + recent messages)"""
        try:
            context_parts = []
            
            # Load conversation summary
            summary = await conversation_storage.load_summary(session_id)
            if summary:
                context_parts.append(f"Previous conversation context: {summary.conversation_summary}")
                if summary.user_context:
                    context_parts.append(f"User context: {summary.user_context}")
            
            # Load recent messages for immediate context
            recent_messages = await conversation_storage.load_recent_messages(session_id, limit=5)
            if recent_messages:
                recent_text = "Recent conversation:\n"
                for msg in recent_messages[-3:]:  # Last 3 messages for immediate context
                    role = "User" if msg.role == "user" else "Assistant"
                    # Truncate long messages
                    content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    recent_text += f"{role}: {content}\n"
                context_parts.append(recent_text.strip())
            
            # Combine and ensure token limit
            full_context = "\n\n".join(context_parts)
            
            # Simple token estimation (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(full_context) // 4
            
            if estimated_tokens > max_tokens:
                # Prioritize summary over recent messages if we need to truncate
                if summary:
                    summary_text = f"Previous conversation context: {summary.conversation_summary}"
                    if summary.user_context:
                        summary_text += f"\nUser context: {summary.user_context}"
                    
                    remaining_tokens = max_tokens - (len(summary_text) // 4)
                    if remaining_tokens > 100 and recent_messages:
                        # Add some recent context if space allows
                        recent_text = f"Most recent exchange:\n"
                        if len(recent_messages) >= 2:
                            last_user = recent_messages[-2] if recent_messages[-2].role == "user" else None
                            last_assistant = recent_messages[-1] if recent_messages[-1].role == "assistant" else None
                            
                            if last_user:
                                recent_text += f"User: {last_user.content[:100]}...\n"
                            if last_assistant:
                                recent_text += f"Assistant: {last_assistant.content[:100]}..."
                        
                        full_context = f"{summary_text}\n\n{recent_text}"
                    else:
                        full_context = summary_text
            
            logger.info(f"📝 Generated context for session {session_id} (~{len(full_context)//4} tokens)")
            return full_context
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation context for session {session_id}: {e}")
            return ""

# Global instance
conversation_summarizer = ConversationSummarizationService()
