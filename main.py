from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from auth_routes import auth_router
from order_routes import order_router
from fastapi.security import OAuth2PasswordBearer

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from auth_routes import auth_router
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Fix Swagger UI to recognize Bearer Tokens
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

app.include_router(auth_router)
app.include_router(order_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}