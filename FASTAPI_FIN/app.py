from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routes import auth, admin, cart
from temp import templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(cart.router)

