from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DATABASE_URL = "postgresql://user:password@host:port/database_name"  # Replace with your actual database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    make = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer)
    price = Column(Float)
    stock = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    customer_name = Column(String)
    quantity = Column(Integer, default=1)

# Dependency injection for database sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/cars/", response_model=List[Car])
async def read_cars(db: Session = Depends(get_db)):
    return db.query(Car).all()

@app.get("/cars/{car_id}", response_model=Car)
async def read_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

@app.post("/cars/", response_model=Car)
async def create_car(car: Car, db: Session = Depends(get_db)):
    db_car = Car(**car.dict())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

@app.put("/cars/{car_id}", response_model=Car)
async def update_car(car_id: int, car: Car, db: Session = Depends(get_db)):
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    db_car.make = car.make
    db_car.model = car.model
    db_car.year = car.year
    db_car.price = car.price 
    db.commit()
    db.refresh(db_car)
    return db_car

@app.delete("/cars/{car_id}")
async def delete_car(car_id: int, db: Session = Depends(get_db)):
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    db.delete(db_car)
    db.commit()
    return {"message": f"Car {car_id} deleted successfully"}

@app.post("/orders/", response_model=Order)
async def create_order(order: Order, db: Session = Depends(get_db)):
    db_car = db.query(Car).filter(Car.id == order.car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
    if db_car.stock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    db_car.stock -= order.quantity
    db_order = Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/", response_model=List[Order])
async def read_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()

@app.get("/orders/{order_id}", response_model=Order)
async def read_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

if __name__ == "__main__":
    uvicorn main:app --reload