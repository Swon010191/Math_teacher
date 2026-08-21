from pydantic import BaseModel, ConfigDict, Field


class KnowledgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str = Field(..., min_length=1, max_length=500)
    include_original: bool = True
    include_vietnamese: bool = True


class KnowledgeCitation(BaseModel):
    id: str
    source_id: str
    title: str
    url: str
    contributors_url: str
    license_name: str
    license_url: str
    revision: str
    retrieved_at: str


class KnowledgeItem(BaseModel):
    id: str
    source_id: str
    title: str
    original_text: str | None = None
    vietnamese_text: str | None = None
    original_language: str
    translation_status: str
    citation_id: str
    cache_status: str


class KnowledgeCacheProvenance(BaseModel):
    policy: str = "bounded-memory-ttl-stale-if-error"
    statuses: list[str]
    external_attempted: bool


class KnowledgeResponse(BaseModel):
    schema_version: str = "1.0"
    topic: str
    items: list[KnowledgeItem]
    citations: list[KnowledgeCitation]
    cache: KnowledgeCacheProvenance
    warning: str
