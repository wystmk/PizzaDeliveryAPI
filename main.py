# from fastapi import FastAPI, Request, Response
# from fastapi.openapi.utils import get_openapi
# from fastapi.security import OAuth2PasswordBearer
# from auth_routes import auth_router
# from order_routes import order_router
# from menu_routes import menu_router 
# from fastapi_cache import FastAPICache
# from fastapi_cache.backends.redis import RedisBackend
# from redis import asyncio as aioredis
# from contextlib import asynccontextmanager
# import logging
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# from starlette.responses import JSONResponse

# # ✅ Configure Logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# # ✅ Initialize Redis using lifespan event handler
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     redis = aioredis.from_url(
#         "redis://localhost:6379",
#         encoding="utf-8",  # Ensures Redis stores data in UTF-8
#         decode_responses=False  # ✅ Prevents FastAPI-Cache decoding errors
#     )
#     FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
#     yield

# # ✅ Initialize FastAPI app
# app = FastAPI(lifespan=lifespan)

# # ✅ Log Incoming Requests
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     logging.info(f"📥 Received request: {request.method} {request.url}")
    
#     # ✅ Capture Response and Log It
#     response = await call_next(request)

#     # ✅ Handle Streaming Responses Correctly
#     response_body = b""
#     async for chunk in response.body_iterator:
#         response_body += chunk

#     response_text = response_body.decode("utf-8")

#     logging.info(f"📤 Response status: {response.status_code}, Body: {response_text}")

#     # ✅ Return a new Response object with the original response data
#     return Response(
#         content=response_body,
#         status_code=response.status_code,
#         headers=dict(response.headers),
#         media_type=response.media_type,
#     )

# # ✅ Initialize Rate Limiter (Limit requests per IP)
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter

# # ✅ Handle Rate Limit Exceeded Errors
# @app.exception_handler(RateLimitExceeded)
# async def rate_limit_exceeded_handler(request, exc):
#     return JSONResponse(
#         {"error": "Too many requests. Please try again later."},
#         status_code=429
#     )

# # ✅ OAuth2 Bearer Token Setup
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# # ✅ Fix Swagger UI to recognize Bearer Tokens
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema

#     openapi_schema = get_openapi(
#         title="FastAPI JWT Authentication",
#         version="1.0.0",
#         description="API that uses JWT authentication via PyJWT",
#         routes=app.routes,
#     )

#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#         }
#     }

#     for path in openapi_schema["paths"]:
#         for method in openapi_schema["paths"][path]:
#             openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app.openapi = custom_openapi

# # ✅ Include API routes
# app.include_router(auth_router)
# app.include_router(order_router)
# app.include_router(menu_router)  # ✅ menu_routes.py will handle rate limiting

# @app.get("/")
# async def root():
#     return {"message": "Welcome to the API"}


import os
from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from auth_routes import auth_router
from order_routes import order_router
from menu_routes import menu_router 
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend  # ✅ Add In-Memory Cache
from redis import asyncio as aioredis
from contextlib import asynccontextmanager
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

# ✅ Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ✅ Initialize Redis using lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application lifespan events."""
    
    if os.getenv("TESTING") == "1":
        logging.info("⚡ Running in TESTING mode: Using In-Memory Cache")
        FastAPICache.init(InMemoryBackend(), prefix="test-cache")  # ✅ Ensure in-memory cache is used
    else:
        logging.info("🚀 Running in PRODUCTION mode: Using Redis Cache")
        redis = aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=False  
        )
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

    yield  # ✅ Yield control to FastAPI
    
# ✅ Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

# ✅ Log Incoming Requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"📥 Received request: {request.method} {request.url}")
    
    # ✅ Capture Response and Log It
    response = await call_next(request)

    # ✅ Handle Streaming Responses Correctly
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    response_text = response_body.decode("utf-8")

    logging.info(f"📤 Response status: {response.status_code}, Body: {response_text}")

    # ✅ Return a new Response object with the original response data
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )

# ✅ Initialize Rate Limiter (Limit requests per IP)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ✅ Handle Rate Limit Exceeded Errors
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        {"error": "Too many requests. Please try again later."},
        status_code=429
    )

# ✅ OAuth2 Bearer Token Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ✅ Fix Swagger UI to recognize Bearer Tokens
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FastAPI JWT Authentication",
        version="1.0.0",
        description="API that uses JWT authentication via PyJWT",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ✅ Include API routes
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(menu_router)  # ✅ menu_routes.py will handle rate limiting

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}