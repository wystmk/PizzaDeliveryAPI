from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import datetime
from models import User, Order
from schemas import OrderModel, OrderStatusModel
from database import get_db
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from auth_routes import get_current_user
import logging
import stripe

# Secret Key (Use same one from login)
SECRET_KEY = "cfbb97543a92c477a457f225ebb61f8b580907f7de5c22680677cfa54ca262da"
ALGORITHM = "HS256"
stripe.api_key = "sk_test_51R2pSlEF1zwsTrESuEWfMCejOCsFw26SzO781KUFTaiKJ15lN1VDR2bg3qkfqA3qMCJjjg7QOrKafnHMsSduBni000ULECEpj6"

order_router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ✅ Store Orders
ORDERS = []

@order_router.get("/hello")
async def hello(token: str = Depends(oauth2_scheme)):
    """_summary_

    Args:
        token (str, optional): _description_. Defaults to Depends(oauth2_scheme).

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token

    Returns:
        dict: Welcome message
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


# @order_router.post("/order")
# async def place_an_order(order: OrderModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     """_summary_

#     Args:
#         order (OrderModel): Order details
#         token (str, optional): Defaults to Depends(oauth2_scheme).
#         db (Session): Database session

#     Raises:
#         HTTPException: Token expired
#         HTTPException: Invalid token
#         HTTPException: User not found

#     Returns:
#         dict: Created order details
#     """
#     try:
#         # Decode the JWT token
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")

#         if not username:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

#         # Fetch the user from the database
#         user = db.query(User).filter(User.username == username).first()
#         if not user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#         # Create a new order (Ensure `OrderModel` has a `user_id` field)
#         new_order = Order(
#             pizza_size=order.pizza_size,
#             quantity=order.quantity,
#             user_id=user.id  # Fix: using `user_id` instead of `user`
#         )

#         db.add(new_order)
#         db.commit()
#         db.refresh(new_order)

#         return {
#             "pizza_size": new_order.pizza_size,
#             "quantity": new_order.quantity,
#             "id": new_order.id,
#             "order_status": new_order.order_status
#         }

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    
@order_router.post("/order", status_code=status.HTTP_201_CREATED)
async def place_an_order(
    order: OrderModel, 
    user: dict = Depends(get_current_user),  # ✅ Require Login
    db: Session = Depends(get_db)
):
    """Place an order (Requires authentication)."""
    
    # ✅ Fetch the user from the database
    db_user = db.query(User).filter(User.username == user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Create a new order
    new_order = Order(
        pizza_size=order.pizza_size,
        quantity=order.quantity,
        user_id=db_user.id  # ✅ Assign order to logged-in user
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    logging.info(f"🛒 {user['username']} placed an order: {order}")

    return {
        "pizza_size": new_order.pizza_size.value,  # ✅ Extract only the string value
        "quantity": new_order.quantity,
        "id": new_order.id,
        "order_status": new_order.order_status.value  # ✅ Extract only the string value
    }
    
@order_router.get("/")
async def list_all_orders(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """_summary_

    Args:
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found
        HTTPException: Not authorized

    Returns:
        list: All orders
    """
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
    """_summary_

    Args:
        id (int): Order ID
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found
        HTTPException: Not authorized
        HTTPException: Order not found

    Returns:
        dict: Order details
    """
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
    """_summary_

    Args:
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found

    Returns:
        list: Orders of the currently logged-in user
    """
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
    """_summary_

    Args:
        id (int): Order ID
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found
        HTTPException: Order not found

    Returns:
        dict: Details of the specific order belonging to the user
    """
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

        
        
# @order_router.put('/order/update/{id}/')
# async def update_order(id: int, order: OrderModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     """_summary_

#     Args:
#         id (int): Order ID
#         order (OrderModel): Updated order data
#         token (str, optional): Defaults to Depends(oauth2_scheme).
#         db (Session): Database session

#     Raises:
#         HTTPException: Token expired
#         HTTPException: Invalid token
#         HTTPException: User not found
#         HTTPException: Order not found

#     Returns:
#         dict: Updated order details
#     """
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
        
#         # if username is empty
#         if not username:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
#         # Fetch the user from the database
#         current_user = db.query(User).filter(User.username == username).first()
#         if not current_user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#         # Find the order by ID and ensure it belongs to the user
#         order_to_update = db.query(Order).filter(Order.id == id, Order.user_id == current_user.id).first()
#         if not order_to_update:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
#         # Update order details
#         order_to_update.quantity = order.quantity
#         order_to_update.pizza_size = order.pizza_size

#         db.commit()
#         db.refresh(order_to_update)
        
#         return jsonable_encoder(order_to_update)

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired, please log in again")

#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token, please check your credentials")

@order_router.put('/order/update/{id}/')
async def update_order(id: int, order: OrderModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """_summary_

    Args:
        id (int): Order ID
        order (OrderModel): Updated order data
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found
        HTTPException: Order not found

    Returns:
        dict: Updated order details
    """
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
        
        return {
            "id": order_to_update.id,
            "quantity": order_to_update.quantity,
            "pizza_size": order_to_update.pizza_size.value,  # Extract string value of pizza_size
            "order_status": order_to_update.order_status.value  # Extract string value of order_status
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired, please log in again")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token, please check your credentials")


@order_router.patch('/order/update/{id}')
async def update_order_status(id: int, order: OrderStatusModel, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Update the order status (only accessible by staff)."""

    try:
        # Decode the JWT token to get user info
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        # Check if username exists
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Fetch the current user from the database
        current_user = db.query(User).filter(User.username == username).first()
        if not current_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if the user is a staff member
        if not current_user.is_staff:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

        # Fetch the order to update
        order_to_update = db.query(Order).filter(Order.id == id).first()
        if not order_to_update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        # Extract valid statuses from the Order model
        valid_statuses = {status[0] for status in Order.ORDER_STATUSES}

        # Convert input status to uppercase and validate
        new_status = order.order_status.upper()  # Ensure the status is uppercase to match database values
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed statuses: {valid_statuses}"
            )

        # Update the order's status
        order_to_update.order_status = new_status
        db.commit()
        db.refresh(order_to_update)

        # Return the updated order status with the order details
        return jsonable_encoder(order_to_update)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
@order_router.delete('/order/delete/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_an_order(id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """_summary_

    Args:
        id (int): Order ID
        token (str, optional): Defaults to Depends(oauth2_scheme).
        db (Session): Database session

    Raises:
        HTTPException: Token expired
        HTTPException: Invalid token
        HTTPException: User not found
        HTTPException: Order not found

    Returns:
        None: No response body (204 No Content)
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
    
    
# ✅ Stripe Payment Endpoint
@order_router.post("/payment/{order_id}")
async def process_payment(order_id: int, user: int = Depends(get_current_user), db: Session = Depends(get_db)):
    """Process a real payment using Stripe."""
    
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user).first()  # 🔥 Fix here!

    if not order:
        raise HTTPException(status_code=404, detail="Order not found or not accessible")

    if order.paid:
        raise HTTPException(status_code=400, detail="Order is already paid")

    # ✅ Create Stripe Payment Intent
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(order.quantity * 10 * 100),  # Price: $10 per pizza (converted to cents)
            currency="usd",
            payment_method_types=["card"],
            metadata={"order_id": order.id, "user_id": user}  # 🔥 Fix here!
        )

        # ✅ Store Stripe Payment ID
        order.stripe_payment_id = intent["id"]
        db.commit()
        db.refresh(order)

        logging.info(f"💳 Payment initiated for order {order_id}: {intent['id']}")

        return {
            "client_secret": intent["client_secret"],  # ✅ Send this to the frontend for payment
            "order_id": order.id,
            "amount": order.quantity * 10
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
    