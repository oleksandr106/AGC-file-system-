from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False, unique=True)
    category = Column(String(100), index=True)
    status = Column(String(50), index=True, default="APPROVED")  # DRAFT | PENDING_APPROVAL | APPROVED | ARCHIVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Vztah 1:N na verze dokumentu
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = 'document_versions'

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    version_number = Column(Float, nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_text = Column(Text, nullable=True)  # Text vyextrahovaný z PDF
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    uploaded_by = Column(String(255), nullable=True)  # Uživatel, který nahrál verzi

    # Zpětný vztah na dokument
    document = relationship("Document", back_populates="versions")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # "admin" nebo "user"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
