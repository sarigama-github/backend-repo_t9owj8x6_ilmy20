"""
Database Schemas for Food Ordering App

Each Pydantic model corresponds to a MongoDB collection. The collection name is the
lowercase of the class name (e.g., Restaurant -> "restaurant").

Collections:
- Restaurant: Basic details about a restaurant
- MenuItem: Individual food items linked to a restaurant
- Order: A placed order with items and totals
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class Restaurant(BaseModel):
    name: str = Field(..., description="Restaurant name")
    cuisine: str = Field(..., description="Cuisine type, e.g., Indian, Chinese")
    rating: float = Field(4.2, ge=0, le=5, description="Average rating 0-5")
    delivery_time: int = Field(30, ge=10, le=120, description="Estimated delivery in minutes")
    image_url: Optional[str] = Field(None, description="Hero image URL")
    location: Optional[str] = Field(None, description="Area or city")
    is_open: bool = Field(True, description="Whether accepting orders")

class MenuItem(BaseModel):
    restaurant_id: str = Field(..., description="Reference to Restaurant _id as string")
    name: str = Field(..., description="Dish name")
    price: float = Field(..., ge=0, description="Price in INR")
    description: Optional[str] = Field(None, description="Short description")
    image_url: Optional[str] = Field(None, description="Image of the dish")
    veg: bool = Field(True, description="Vegetarian indicator")
    category: Optional[str] = Field(None, description="Category e.g., Mains, Starters")

class OrderItem(BaseModel):
    item_id: str = Field(..., description="Menu item id")
    name: str = Field(...)
    qty: int = Field(..., ge=1)
    price: float = Field(..., ge=0)

class Order(BaseModel):
    restaurant_id: str = Field(...)
    items: List[OrderItem] = Field(...)
    subtotal: float = Field(..., ge=0)
    delivery_fee: float = Field(30.0, ge=0)
    total: float = Field(..., ge=0)
    customer_name: str = Field(...)
    address: str = Field(...)
    status: str = Field("placed", description="placed, preparing, on_the_way, delivered, cancelled")
