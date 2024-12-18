from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from models import User, Product, Cart
from database import engine, SessionLocal, Base

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: str = Cookie(None), error: str = None, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first() if user else None
    return templates.TemplateResponse("index.html", {"request": request, "products": products, "user": user,
                                                     "admin_user": admin_user, "error": error})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request, error: str = None):
    return templates.TemplateResponse("register.html", {"request": request, "error": error})

@app.post("/logout")
async def logout():
    response = RedirectResponse(url='/', status_code=303)
    response.delete_cookie(key="user")
    return response

@app.get("/admin/register", response_class=HTMLResponse)
async def admin_register(request: Request, error: str = None):
    return templates.TemplateResponse("admin_register.html", {"request": request, "error": error})


@app.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        return RedirectResponse(url='/login?error=Неверные имя пользователя или пароль', status_code=303)

    response = RedirectResponse(url='/', status_code=303)
    response.set_cookie(key="user", value=username)
    return response


@app.post("/register")
async def register_post(username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...),
                        db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url='/register?error=Пользователь уже существует', status_code=303)

    if password != confirm_password:
        return RedirectResponse(url='/register?error=Пароли не совпадают', status_code=303)

    new_user = User(username=username, password=password)  # Используйте хеширование для паролей в реальной жизни
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = RedirectResponse(url='/', status_code=303)
    response.set_cookie(key="user", value=username)
    return response

@app.post("/admin/register")
async def admin_register_post(username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...),
                              db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url='/admin/register?error=Пользователь уже существует', status_code=303)

    if password != confirm_password:
        return RedirectResponse(url='/admin/register?error=Пароли не совпадают', status_code=303)

    new_user = User(username=username, password=password, admin=True)  # Устанавливаем admin=True для администратора
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = RedirectResponse(url='/', status_code=303)
    return response


@app.get("/admin/products/add", response_class=HTMLResponse)
async def add_product(request: Request, user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        return RedirectResponse(url='/', status_code=303)

    return templates.TemplateResponse("add_product.html", {"request": request})


@app.post("/admin/products/add")
async def add_product_post(name: str = Form(...), description: str = Form(...), price: float = Form(...), image_url: str = Form(None), user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    new_product = Product(name=name, description=description, price=price, image_url=image_url)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return RedirectResponse(url='/', status_code=303)


@app.post("/admin/products/remove/{product_id}")
async def remove_product(product_id: int, user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()

    return RedirectResponse(url='/', status_code=303)

@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request, user: str = Cookie(None), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")

    user_db = db.query(User).filter(User.username == user).first()
    cart_items = db.query(Cart).filter(Cart.user_id == user_db.id).all()

    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "user": user})

@app.post("/cart/add/{product_id}")
async def add_to_cart(product_id: int, user: str = Cookie(None), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")

    user_db = db.query(User).filter(User.username == user).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверка, не добавлен ли товар в корзину
    existing_cart_item = db.query(Cart).filter(Cart.user_id == user_db.id, Cart.product_id == product_id).first()
    if existing_cart_item:
        return RedirectResponse(url='/?error=Товар уже в корзине', status_code=303)

    # Добавление товара в корзину
    new_cart_item = Cart(user_id=user_db.id, product_id=product_id)
    db.add(new_cart_item)
    db.commit()

    return RedirectResponse(url='/', status_code=303)

@app.post("/cart/remove/{cart_item_id}")
async def remove_from_cart(cart_item_id: int, user: str = Cookie(None), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")

    user_db = db.query(User).filter(User.username == user).first()
    cart_item = db.query(Cart).filter(Cart.id == cart_item_id, Cart.user_id == user_db.id).first()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")

    db.delete(cart_item)
    db.commit()

    return RedirectResponse(url='/cart', status_code=303)

@app.post("/admin/products/remove/{product_id}")
async def remove_product(product_id: int, user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()

    return RedirectResponse(url='/', status_code=303)