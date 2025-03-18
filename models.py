from database import Base
from sqlalchemy import Column, Integer, Boolean, Text, String, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy_utils.types import ChoiceType

class User(Base):
    __tablename__ = 'users'  # ✅ Use 'users' to avoid reserved keyword conflicts
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(25), unique=True, nullable=False)
    email = Column(String(80), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)  # ✅ Default to active user
    orders = relationship('Order', back_populates='user')  # ✅ Fix relationship

    def __repr__(self):
        return f"<User {self.username}>"

class Order(Base):

    ORDER_STATUSES = [
        ("PENDING", "PENDING"),
        ("IN-TRANSIT", "IN-TRANSIT"),
        ("DELIVERED", "DELIVERED")
    ]

    PIZZA_SIZES = [
        ("SMALL", "SMALL"),
        ("MEDIUM", "MEDIUM"),
        ("LARGE", "LARGE"),
        ("EXTRA-LARGE", "EXTRA-LARGE"),
    ]

    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer, nullable=False)
    order_status = Column(ChoiceType(ORDER_STATUSES, impl=String()), nullable=False, default="PENDING")
    pizza_size = Column(ChoiceType(PIZZA_SIZES, impl=String()), nullable=False, default="SMALL")
    user_id = Column(Integer, ForeignKey('users.id'))  # ✅ Fix ForeignKey reference
    paid = Column(Boolean, default=False)
    stripe_payment_id = Column(String, nullable=True)  # ✅ Store Stripe payment ID
    user = relationship('User', back_populates='orders')  # ✅ Fix relationship

    def __repr__(self):
        return f"<Order {self.id}>"

# ✅ Attach event listener at the class level
@event.listens_for(Order, "before_insert")
def set_pizza_size_before_insert(mapper, connection, target):
    """Ensure pizza_size is always uppercase before inserting into DB."""
    if isinstance(target.pizza_size, str):
        target.pizza_size = target.pizza_size.upper()