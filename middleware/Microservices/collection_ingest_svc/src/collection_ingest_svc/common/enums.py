from enum import Enum


class CollectionCategory(str, Enum):
    LINKS = "Links"
    ANNOUNCEMENTS = "Announcements"
    ARTICLES = "Articles"
    KNOWLEDGE_BASE = "KnowledgeBase"


class FileFormat(str, Enum):
    PDF = "pdf"
    DOCS = "docs"
    EXCEL = "excel"
    IMAGES = "images"
    CSV = "csv"


class IngestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # some vector DBs succeeded, some failed
