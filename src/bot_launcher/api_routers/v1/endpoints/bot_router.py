from fastapi import APIRouter

router = APIRouter(prefix="/bots", tags=["Bot Management"])

@router.get("/")
async def list_bots():
    """Endpoint to list all active bots."""
    return {"message": "List of active bots will be here."}


