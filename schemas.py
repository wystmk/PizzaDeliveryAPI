from pydantic import BaseModel
from typing import Optional

class SignUpModel(BaseModel):
    id: Optional[int] = None
    username:str
    email:str
    password:str
    is_staff:Optional[bool]
    is_active:Optional[bool]
    
    
    class Config:
        from_attributes = True  # Fix for Pydantic v2
        orm_mode=True
        schema_extra={
            'example':{
                "username":"wyst",
                "email":"wyst@gmail.com",
                "password":"password",
                "is_staff":False,
                "is_active":True
            }
        }
        
        
        
class Settings(BaseModel):
    authjwt_secret_key:str='cfbb97543a92c477a457f225ebb61f8b580907f7de5c22680677cfa54ca262da'
    
    
class LoginModel(BaseModel):
    username:str
    password:str
    

class OrderModel(BaseModel):
    id:Optional[int] = None
    quantity:int
    order_status: Optional[str] = "PENDING"
    pizza_size: Optional[str]="SMALL"
    user_id:Optional[int] = None
    
    class Config:
        orm_model=True
        schema_extra={
            "example":{
                "quantity":2,
                "pizza_size":"LARGE"
            }
        }
        
        
class OrderStatusModel(BaseModel):
    order_status: Optional[str] = "PENDING"
    
    class Config:
        orm_mode=True
        schema_extra={
            "example":{
                "order_status":"PENDING"
            }
        }