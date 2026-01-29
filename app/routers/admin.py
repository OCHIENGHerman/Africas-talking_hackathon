"""
Admin router for viewing data (basic endpoints for hackathon demo).
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserResponse(BaseModel):
    """User record (phone, city_code, location, created_at)."""
    id: int
    phone_number: str
    city_code: str | None = None
    location: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    """Order record (items, total_price, status)."""
    id: int
    user_id: int
    items: str
    total_price: float
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


@router.get("/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    """Get all users."""
    users = db.query(User).all()
    return users


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Returns a single user by numeric ID.",
    response_description="User details",
    responses={404: {"description": "User not found"}},
)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get(
    "/orders",
    response_model=List[OrderResponse],
    summary="List all orders",
    description="Returns all orders (items, total price, status).",
    response_description="List of orders",
)
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Returns a single order by numeric ID.",
    response_description="Order details",
    responses={404: {"description": "Order not found"}},
)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
