from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from .database import Base


class LoadTest(Base):
    __tablename__ = "load_tests"
    id = mapped_column(String(36), primary_key=True)
    project_name = mapped_column(String(255), index=True, nullable=False)
    url = mapped_column(Text, nullable=False)
    status = mapped_column(String(20), nullable=False)
    result_json = mapped_column(JSON, nullable=True)
    analysis = mapped_column(Text, nullable=True)
    pdf_path = mapped_column(Text, nullable=True)
    user_id = mapped_column(String(36), nullable=True, index=True)
    username = mapped_column(String(255), nullable=True)
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )


class User(Base):
    __tablename__ = "users"
    id = mapped_column(String(36), primary_key=True)
    username = mapped_column(String(255), unique=True, index=True, nullable=False)
    email = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password = mapped_column(Text, nullable=False)
    role = mapped_column(String(16), nullable=False, server_default="user")
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )


class UserLLMSettings(Base):
    __tablename__ = "user_llm_settings"
    id = mapped_column(String(36), primary_key=True)
    user_id = mapped_column(String(36), unique=True, index=True, nullable=False)
    # LLM Provider: "gemini", "openai", or "local"
    provider = mapped_column(String(16), nullable=False, server_default="gemini")
    # Gemini settings
    gemini_api_key = mapped_column(Text, nullable=True)
    gemini_model = mapped_column(String(64), nullable=True)
    # OpenAI settings
    openai_api_key = mapped_column(Text, nullable=True)
    openai_model = mapped_column(String(64), nullable=True)
    openai_base_url = mapped_column(Text, nullable=True)
    # Common settings
    temperature = mapped_column(String(8), nullable=False, server_default="0.2")
    max_tokens = mapped_column(String(8), nullable=False, server_default="2048")
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
