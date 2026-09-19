from fastapi import APIRouter
from app.api.v1.contracts import router as contracts_router
from app.api.v1.clauses import router as clauses_router
from app.api.v1.fields import router as fields_router
from app.api.v1.obligations import router as obligations_router
from app.api.v1.qa import router as qa_router
from app.api.v1.risk import router as risk_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(contracts_router)
api_v1_router.include_router(clauses_router)
api_v1_router.include_router(fields_router)
api_v1_router.include_router(obligations_router)
api_v1_router.include_router(qa_router)
api_v1_router.include_router(risk_router)


@api_v1_router.get("/")
def api_v1_root():
    return {"message": "ContractLens API v1"}



