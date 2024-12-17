from fastapi import APIRouter
from app.api.v1.endpoints import webhook

api_router = APIRouter()

api_router.include_router(
    webhook.router,
    prefix="/webhook",
    tags=["webhook"]
)

# 之後可以在這裡加入其他路由
# api_router.include_router(
#     messages.router,
#     prefix="/messages",
#     tags=["messages"]
# ) 