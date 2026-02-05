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
    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
