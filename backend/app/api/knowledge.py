from fastapi import APIRouter, HTTPException

from app.schemas.knowledge import KnowledgeRequest, KnowledgeResponse
from app.services.knowledge_service import knowledge_service
from app.services.math_service import MathEngineError

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/related", response_model=KnowledgeResponse)
def related(request: KnowledgeRequest) -> KnowledgeResponse:
    try:
        return knowledge_service.related(request)
    except MathEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
