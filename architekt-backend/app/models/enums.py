from enum import Enum


class QuestionType(str, Enum):
    DEFINITION = "definition"
    SCENARIO = "scenario"
    TRADEOFF = "tradeoff"
    IDENTIFICATION = "identification"


class QuestionSource(str, Enum):
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"


class ReviewStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    RETIRED = "retired"


class QuizMode(str, Enum):
    CATEGORY = "category"
    ADAPTIVE = "adaptive"
    REVIEW = "review"


class QuizSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class MasterySignal(str, Enum):
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    MISS = "MISS"


class MasteryState(str, Enum):
    UNSEEN = "UNSEEN"
    ATTEMPTED = "ATTEMPTED"
    STRUGGLING = "STRUGGLING"
    DEVELOPING = "DEVELOPING"
    COMPETENT = "COMPETENT"
    MASTERED = "MASTERED"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
