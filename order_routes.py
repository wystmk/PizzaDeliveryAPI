from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import datetime
from models import User, Order
from schemas import OrderModel, OrderStatusModel
from database import get_db
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

# Secret Key (Use same one from login)
SECRET_KEY = "cfbb97543a92c477a457f225ebb61f8b580907f7de5c22680677cfa54ca262da"
ALGORITHM = "HS256"

order_router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@order_router.get("/")
async def hello(token: str = Depends(oauth2_scheme)):
    """_summary_

    Args:
        token (str, optional): _description_. Defaults to Depends(oauth2_scheme).

    Raises:
        HTTPException: _description_
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        
        # Ensure the token contains the required subject (username)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    return {"message": "Hello World"}


@order_router.post("/order")
async def place_an_order(order: OrderModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch the user from the database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Create a new order (Ensure `OrderModel` has a `user_id` field)
        new_order = Order(
            pizza_size=order.pizza_size,
            quantity=order.quantity,
            user_id=user.id  # Fix: using `user_id` instead of `user`
        )

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        return {
            "pizza_size": new_order.pizza_size,
            "quantity": new_order.quantity,
            "id": new_order.id,
            "order_status": new_order.order_status
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
@order_router.get("/orders")
async def list_all_orders(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch user from the database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if the user has staff privileges
        if not user.is_staff:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view all orders")

        # Get all orders from the database
        orders = db.query(Order).all()

        return orders

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
    
@order_router.get("/orders/{id}")
async def get_order_by_id(id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        # Check is username is null/None
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch user from the database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if the user has staff privileges
        if not user.is_staff:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")

        # Retrieve the order by ID
        order = db.query(Order).filter(Order.id == id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        return jsonable_encoder(order)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
# Get a current user's orders
# This lists the orders made by the currently logged in users
@order_router.get('/user/orders')
async def get_user_orders(token: str=Depends(oauth2_scheme), db: Session=Depends(get_db)):
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username=payload.get("sub")
        
        # check if empty
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user=db.query(User).filter(User.username==username).first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return jsonable_encoder(user.orders)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
        
@order_router.get('/user/order/{id}/')
async def get_specific_order(id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # if username is empty
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        current_user = db.query(User).filter(User.username == username).first()
        
        # if no current_user in our db
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        order = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
        
        # if order is empty
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            
        return jsonable_encoder(order)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        
        
@order_router.put('/order/update/{id}/')
async def update_order(id: int, order: OrderModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # if username is empty
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Fetch the user from the database
        current_user = db.query(User).filter(User.username == username).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Find the order by ID and ensure it belongs to the user
        order_to_update = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
        if not order_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        # Update order details
        order_to_update.quantity = order.quantity
        order_to_update.pizza_size = order.pizza_size

        db.commit()
        db.refresh(order_to_update)
        
        return jsonable_encoder(order_to_update)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired, please log in again")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token, please check your credentials")

        

@order_router.patch('/order/update/{id}')
async def update_order_status(id: int, order: OrderStatusModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # if username is empty
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Fetch the user from the database
        current_user = db.query(User).filter(User.username == username).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Ensure the user is a staff member
        if not current_user.is_staff:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        
        # Find the order to update
        order_to_update = db.query(Order).filter(Order.id == id).first()
        if not order_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        
        # Extract valid statuses from the Order model
        valid_statuses = {status[0] for status in Order.ORDER_STATUSES}

        # Convert input order status to uppercase and validate
        new_status = order.order_status.upper()
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed statuses: {valid_statuses}"
            )
        
        # Update the order status
        order_to_update.order_status = new_status
        db.commit()
        db.refresh(order_to_update)

        return jsonable_encoder(order_to_update)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
@order_router.delete('/order/delete/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_an_order(id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Delete an Order
    This deletes an order by its ID.
    """

    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch the current user from the database
        current_user = db.query(User).filter(User.username == username).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Find the order in the database
        order_to_delete = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
        if not order_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or unauthorized")

        # Delete the order and commit changes
        db.delete(order_to_delete)
        db.commit()

        return  # No return body due to 204 No Content

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")