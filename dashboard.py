from fastapi import APIRouter

overview_router = APIRouter(prefix="/overview")

@overview_router.get("/")
async def get_overview():
    return {"status": "Dashboard Overview Router Initialized"}
