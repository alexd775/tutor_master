from typing import List, Dict, Any, Tuple
import openai
import uuid
import pystache
from datetime import datetime, UTC
from app.core.config import settings
from app.models import Agent, Session, ChatMessage, MessageRole, User, Topic
from sqlalchemy.orm import Session as DBSession

class AIService:
    """Service for handling AI agent interactions."""
    
    def __init__(self, db: DBSession):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.renderer = pystache.Renderer()

    def get_client(self, ai_service: str):
        if ai_service in ["openai", "", None]:
            # default to openai
            return openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Invalid AI service: {ai_service}")
        
    def _prepare_template_data(self, session: Session) -> Dict[str, Any]:
        """Prepare data for template rendering."""
        # Get user data
        user = session.user
        # user = self.db.query(User).filter(User.id == session.user_id).first()
        
        # Get topic data
        topic = session.topic
        # topic = self.db.query(Topic).filter(Topic.id == session.topic_id).first()
        
        # Prepare template data
        return {
            "user": {
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role
            },
            "topic": {
                "title": topic.title,
                "description": topic.description,
                "difficulty_level": topic.difficulty_level,
                "content": topic.content
            },
            "session": {
                "id": session.id,
                "completion_rate": session.completion_rate,
                "duration": session.duration
            }
        }
        
    async def initialize_session(self, session: Session) -> ChatMessage:
        """Initialize a new session with the AI agent."""
        # Prepare template data
        template_data = self._prepare_template_data(session)
        
        # Render system prompt with template data
        rendered_prompt = self.renderer.render(
            session.agent.system_prompt,
            template_data
        )
        
        # Create system message
        system_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.SYSTEM,
            content=rendered_prompt
        )
        
        # Render welcome message with template data
        rendered_welcome = self.renderer.render(
            session.agent.welcome_message,
            template_data
        )
        
        # Create welcome message
        welcome_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=rendered_welcome
        )
        
        self.db.add_all([system_msg, welcome_msg])
        self.db.commit()
        
        return welcome_msg
    
    async def client_send_message(self, agent: Agent, messages: List[Dict[str, Any]]) -> Tuple[str, int, float]:
        client = self.get_client(agent.ai_service)
        print(messages)
        response = client.chat.completions.create(
            model='gpt-3.5-turbo-0125',#'chatgpt-4o-latest',##agent.config["model"],
            messages=messages,
            temperature=agent.config.get("temperature", 0.7),
            max_tokens=agent.config.get("max_tokens", 500)
        )

        message = response.choices[0].message
        content=message.content
        tokens=response.usage.total_tokens
        if message.function_call and "completion_rate" in message.function_call:
            completion_rate=message.function_call["completion_rate"]
        else:
            completion_rate=0.0
        return content, tokens, completion_rate
    
    async def process_message(
        self,
        session: Session,
        user_message: str,
        context_window: int = 10
    ) -> List[ChatMessage]:
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
        content, tokens, completion_rate = await self.client_send_message(session.agent, messages)
        
        # Create response message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=content,
            tokens=tokens
        )
        self.db.add(assistant_msg)
        
        # Update session metrics
        self._update_session_metrics(session, completion_rate)
        
        # Update interaction data
        self._update_interaction_data(session, tokens)
        
        self.db.commit()
        return [user_msg, assistant_msg]
    
    def _update_session_metrics(
        self,
        session: Session,
        completion_rate: float
    ) -> None:
        """Update session metrics based on interaction."""
        # Update completion rate based on agent's assessment
        session.completion_rate = max(session.completion_rate, completion_rate)
        
    def _update_interaction_data(self, session: Session, total_tokens: int) -> None:
        # Update interaction data
        if not session.interaction_data:
            session.interaction_data = {}
        
        session.interaction_data.update({
            "total_messages": session.interaction_data.get("total_messages", 0) + 1,
            "total_tokens": session.interaction_data.get("total_tokens", 0) + total_tokens,
            "last_interaction": datetime.now(UTC).isoformat()
        }) 