import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Restaurant as RestaurantSchema, MenuItem as MenuItemSchema, Order as OrderSchema

app = FastAPI(title="Food Ordering API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"]) if isinstance(doc["_id"], ObjectId) else doc["_id"]
    # convert nested ids if present
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        if isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict):
                    new_list.append(serialize_doc(item))
                elif isinstance(item, ObjectId):
                    new_list.append(str(item))
                else:
                    new_list.append(item)
            doc[k] = new_list
    return doc


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ------------ Food Ordering API -------------

@app.get("/api/restaurants")
async def list_restaurants():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    docs = get_documents("restaurant")
    return [serialize_doc(d) for d in docs]


@app.get("/api/restaurants/{restaurant_id}/menu")
async def get_menu(restaurant_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        # menu items where restaurant_id matches (stored as string)
        items = get_documents("menuitem", {"restaurant_id": restaurant_id})
        return [serialize_doc(i) for i in items]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SeedResponse(BaseModel):
    restaurants: int
    menu_items: int


@app.post("/api/seed", response_model=SeedResponse)
async def seed_data():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Seed only if empty
    rest_count = db["restaurant"].count_documents({})
    menu_count = db["menuitem"].count_documents({})
    if rest_count > 0 and menu_count > 0:
        return SeedResponse(restaurants=rest_count, menu_items=menu_count)

    # Sample restaurants
    restaurants = [
        RestaurantSchema(name="Spice Hub", cuisine="Indian", rating=4.5, delivery_time=30, image_url="https://images.unsplash.com/photo-1604908177079-325c9c9e8f26", location="Bangalore"),
        RestaurantSchema(name="Dragon Wok", cuisine="Chinese", rating=4.2, delivery_time=35, image_url="https://images.unsplash.com/photo-1553621042-f6e147245754", location="Mumbai"),
        RestaurantSchema(name="Pasta Point", cuisine="Italian", rating=4.3, delivery_time=25, image_url="https://images.unsplash.com/photo-1523986371872-9d3ba2e2f642", location="Delhi"),
    ]

    rest_ids = []
    for r in restaurants:
        _id = create_document("restaurant", r)
        rest_ids.append(_id)

    # Sample menu items
    menu_items = [
        MenuItemSchema(restaurant_id=rest_ids[0], name="Paneer Tikka", price=220, description="Smoky grilled paneer", veg=True, category="Starters", image_url="https://images.unsplash.com/photo-1604908177079-325c9c9e8f26"),
        MenuItemSchema(restaurant_id=rest_ids[0], name="Butter Naan", price=60, description="Soft butter naan", veg=True, category="Breads"),
        MenuItemSchema(restaurant_id=rest_ids[1], name="Veg Hakka Noodles", price=180, description="Stir-fried noodles", veg=True, category="Mains", image_url="https://images.unsplash.com/photo-1543357480-c60d7abff9b9"),
        MenuItemSchema(restaurant_id=rest_ids[1], name="Chilli Paneer", price=200, description="Spicy paneer cubes", veg=True, category="Starters"),
        MenuItemSchema(restaurant_id=rest_ids[2], name="Margherita Pizza", price=320, description="Classic cheese pizza", veg=True, category="Pizza", image_url="https://images.unsplash.com/photo-1548365328-9f547fb09501"),
    ]

    for m in menu_items:
        create_document("menuitem", m)

    return SeedResponse(restaurants=len(rest_ids), menu_items=len(menu_items))


@app.post("/api/orders")
async def create_order(order: OrderSchema):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        order_id = create_document("order", order)
        return {"order_id": order_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        doc = db["order"].find_one({"_id": ObjectId(order_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Order not found")
        return serialize_doc(doc)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid order id")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
