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


# Secret key for JWT
SECRET_KEY = "cfbb97543a92c477a457f225ebb61f8b580907f7de5c22680677cfa54ca262da"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

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
        expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        refresh_expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)

        access_token = jwt.encode(
            {"sub": db_user.username, "exp": expiration},
            SECRET_KEY,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            {"sub": db_user.username, "exp": refresh_expiration},
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