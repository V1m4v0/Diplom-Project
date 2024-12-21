from fastapi import APIRouter, Request, Depends, Form, Cookie
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Product
from temp import templates

router = APIRouter()

@router.get("/")
async def index(request: Request, user: str = Cookie(None), error: str = None, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first() if user else None
    return templates.TemplateResponse("index.html", {"request": request, "products": products, "user": user,
                                                     "admin_user": admin_user, "error": error})

@router.get("/login")
async def login(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        return RedirectResponse(url='/login?error=Неверные имя пользователя или пароль', status_code=303)
    response = RedirectResponse(url='/', status_code=303)
    response.set_cookie(key="user", value=username)
    return response

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@router.post("/register")
async def register_post(username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url='/register?error=Пользователь уже существует', status_code=303)
    if password != confirm_password:
        return RedirectResponse(url='/register?error=Пароли не совпадают', status_code=303)
    new_user = User(username=username, password=password)  # Используйте хеширование паролей в реальной жизни
    db.add(new_user)
    db.commit()
    response = RedirectResponse(url='/', status_code=303)
    response.set_cookie(key="user", value=username)
    return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url='/', status_code=303)
    response.delete_cookie(key="user")
    return response
