from fastapi import APIRouter

router = APIRouter(prefix="/launcher", tags=["Launcher Management"])


@router.get("/")
async def launcher_status():
    """Endpoint to check the status of the launcher."""
    return {"message": "Launcher is running."}
