import logging
import json
from fastapi import APIRouter, Request
from fastapi_cache.decorator import cache
from slowapi.util import get_remote_address
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from auth_routes import require_admin
from fastapi import APIRouter, Depends, HTTPException, status

# ✅ Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

menu_router = APIRouter()

# ✅ Apply Rate Limiting
limiter = Limiter(key_func=get_remote_address)

PIZZA_MENU = [
    {"name": "Margherita", "price": 8.99},
    {"name": "Pepperoni", "price": 10.99},
    {"name": "BBQ Chicken", "price": 11.99},
    {"name": "Veggie Supreme", "price": 9.99},
]

@menu_router.get("/menu")
@limiter.limit("5/minute")  # ✅ Apply Rate Limiting (5 requests per minute per user)
@cache(expire=300)  # ✅ Cache for 5 minutes
async def get_menu(request: Request):
    """
    Fetches the menu with Redis caching and logs when data is fetched from the database.
    """
    logging.info("🔥 Fetching menu from the database!!")  # ✅ Log when DB fetch occurs

    response = {"menu": PIZZA_MENU}

    # ✅ Ensure response is always a dictionary (Fix Redis string issue)
    if isinstance(response, str):
        response = json.loads(response)

    logging.info(f"📤 Returning Menu: {response}")  # ✅ Log the response data

    return response


# ✅ Require Admin Role to Modify Menu
@menu_router.post("/admin/menu")
async def add_menu_item(item: dict, user: dict = Depends(require_admin)):  # ✅ Admins Only
    logging.info(f"🔧 Admin {user['username']} is adding a new menu item: {item}")
    PIZZA_MENU.append(item)
    return {"message": "Item added!", "menu": PIZZA_MENU}