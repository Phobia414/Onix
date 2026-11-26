from aiogram import Router
from . import client, orders, admin, referral, reviews, blocked_users # <-- Добавили blocked_users

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(blocked_users.router) # <-- Добавили
    main_router.include_router(referral.router)
    main_router.include_router(client.router)
    main_router.include_router(reviews.router)
    main_router.include_router(orders.router)
    main_router.include_router(admin.router)
    return main_router