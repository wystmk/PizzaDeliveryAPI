from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from schemas import SignUpModel, LoginModel
from models import User
from database import get_db, SessionLocal
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, UTC

# Secret key for JWT
SECRET_KEY = "cfbb97543a92c477a457f225ebb61f8b580907f7de5c22680677cfa54ca262da"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# # ✅ Extract User Data & Role from JWT Token
# def get_current_user(token: str = Depends(oauth2_scheme)):
#     """Decode JWT and return the authenticated user's details (username & role)."""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id = payload.get("id")
#         username = payload.get("sub")
#         is_staff = payload.get("is_staff", False)  # ✅ Extract is_staff role

#         if user_id is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#         if not username:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
#         #return {"username": username, "user_id": user_id, "is_staff": is_staff}  # ✅ Return user details with role
#         return user_id

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ✅ Extract User Data & Role from JWT Token
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decode JWT and return the authenticated user's details (username & role)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")  # ✅ User ID from JWT
        username = payload.get("sub")  # ✅ Username from JWT
        is_staff = payload.get("is_staff", False)  # ✅ Extract is_staff role

        if user_id is None or not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # ✅ Return full user dictionary instead of just `user_id`
        return {"id": user_id, "username": username, "is_staff": is_staff}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
# ✅ Ensure Only Admins Can Access Certain Routes
def require_admin(user: dict = Depends(get_current_user)):
    """Check if the user is an admin before granting access."""
    if not user["is_staff"]:  # ✅ Check if user is an admin
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return user  # ✅ Return user details if they are admin

session = SessionLocal()


@auth_router.get("/")
async def hello(token: str = Depends(oauth2_scheme)):
    """_summary_

    Args:
        token (str, optional): Defaults to Depends(oauth2_scheme).

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token

    Returns:
        dict: Greeting message with the username
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")  # Get username from token

        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")

        return {"message": f"Hello, {username}!"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    


@auth_router.post('/signup', response_model=SignUpModel,
                  status_code=status.HTTP_201_CREATED)
async def signup(user:SignUpModel):
    """_summary_

    Args:
        user (SignUpModel): User registration data

    Raises:
        HTTPException: User with the same email already exists
        HTTPException: User with the same username already exists

    Returns:
        dict: Created user details
    """
    
    db_email=session.query(User).filter(User.email==user.email).first()
    
    if db_email is not None: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="User with the email already exists")
        
        
    db_username=session.query(User).filter(User.username==user.username).first()
    
    if db_username is not None: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                             detail="User with the email already exists")
        
    new_user=User(
        username=user.username,
        email=user.email,
        password=generate_password_hash(user.password),
        is_active=user.is_active,
        is_staff=user.is_staff
    )
    
    session.add(new_user)
    
    session.commit()
    
    return new_user



# Login Route
@auth_router.post('/login')
async def login(user: LoginModel, db: Session = Depends(get_db)):
    """_summary_

    Args:
        user (LoginModel): User login credentials
        db (Session): Database session

    Raises:
        HTTPException: Invalid username or password

    Returns:
        dict: Access token and refresh token
    """
    db_user = db.query(User).filter(User.username == user.username).first()

    if db_user and check_password_hash(db_user.password, user.password):
        # expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        # refresh_expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        expiration = datetime.now(UTC) + timedelta(minutes=15)  # ✅ Use `datetime.now(UTC)`
        refresh_expiration = datetime.now(UTC) + timedelta(days=7)

        # Include role (`is_staff`) in JWT Token
        access_token = jwt.encode(
            {"sub": db_user.username, "id": db_user.id, "exp": expiration},  # Add "id": db_user.id
            SECRET_KEY,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            {"sub": db_user.username, "id": db_user.id, "exp": refresh_expiration},  # Add "id": db_user.id
            SECRET_KEY,
            algorithm="HS256"
        )

        response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        return jsonable_encoder(response)

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username or password")



@auth_router.post("/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """_summary_

    Args:
        token (str, optional): Defaults to Depends(oauth2_scheme).

    Raises:
        HTTPException: Refresh token expired
        HTTPException: Invalid refresh token

    Returns:
        dict: New access token
    """
    try:
        # Decode the refresh token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Generate a new access token
        access_expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        new_access_token = jwt.encode({"sub": payload["sub"], "exp": access_expiration}, SECRET_KEY, algorithm=ALGORITHM)

        return jsonable_encoder({"access_token": new_access_token, "token_type": "bearer"})

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")