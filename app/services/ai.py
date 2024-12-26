from typing import Optional, List, Dict, Any
import openai
import uuid
from datetime import datetime, UTC
from app.core.config import settings
from app.models import Agent, Session, ChatMessage, MessageRole
from sqlalchemy.orm import Session as DBSession

class AIService:
    """Service for handling AI agent interactions."""
    
    def __init__(self, db: DBSession):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def initialize_session(self, session: Session) -> ChatMessage:
        """Initialize a new session with the AI agent."""
        # Create system message
        system_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.SYSTEM,
            content=session.agent.system_prompt
        )
        
        # Create welcome message
        welcome_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=session.agent.welcome_message
        )
        
        self.db.add_all([system_msg, welcome_msg])
        self.db.commit()
        
        return welcome_msg
    
    async def process_message(
        self,
        session: Session,
        user_message: str,
        context_window: int = 10
    ) -> ChatMessage:
        """Process a user message and return the agent's response."""
        # Create user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.USER,
            content=user_message
        )
        self.db.add(user_msg)
        
        # Get recent context
        recent_messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(context_window)
            .all()
        )
        
        # Prepare messages for API
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(recent_messages)
        ]
        messages.append({"role": "user", "content": user_message})
        
        # Get agent response
        response = await self.client.chat.completions.create(
            model=session.agent.config["model"],
            messages=messages,
            temperature=session.agent.config.get("temperature", 0.7),
            max_tokens=session.agent.config.get("max_tokens", 1000)
        )
        
        # Create response message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=response.choices[0].message.content,
            tokens=response.usage.total_tokens
        )
        self.db.add(assistant_msg)
        
        # Update session metrics
        self._update_session_metrics(session, user_message, response)
        
        self.db.commit()
        return assistant_msg
    
    def _update_session_metrics(
        self,
        session: Session,
        user_message: str,
        response: Any
    ) -> None:
        """Update session metrics based on interaction."""
        # Update completion rate based on agent's assessment
        if "completion_rate" in response.choices[0].message.function_call:
            new_rate = float(response.choices[0].message.function_call["completion_rate"])
            session.completion_rate = max(session.completion_rate, new_rate)
        
        # Update interaction data
        if not session.interaction_data:
            session.interaction_data = {}
        
        session.interaction_data.update({
            "total_messages": session.interaction_data.get("total_messages", 0) + 1,
            "total_tokens": session.interaction_data.get("total_tokens", 0) + response.usage.total_tokens,
            "last_interaction": datetime.now(UTC).isoformat()
        }) 