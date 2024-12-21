from fastapi import APIRouter, Request, Depends, Form, Cookie, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Product
from temp import templates

router = APIRouter()


@router.get("/admin/register")
async def admin_register(request: Request, error: str = None):
    return templates.TemplateResponse("admin_register.html", {"request": request, "error": error})


@router.post("/admin/register")
async def admin_register_post(username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...),
                              db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse(url='/admin/register?error=Пользователь уже существует', status_code=303)
    if password != confirm_password:
        return RedirectResponse(url='/admin/register?error=Пароли не совпадают', status_code=303)
    new_user = User(username=username, password=password, admin=True)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url='/', status_code=303)


@router.get("/admin/products/add", response_class=HTMLResponse)
async def add_product(request: Request, user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        return RedirectResponse(url='/', status_code=303)
    return templates.TemplateResponse("add_product.html", {"request": request})


@router.post("/admin/products/add")
async def add_product_post(name: str = Form(...), description: str = Form(...), price: float = Form(...),
                           image_url: str = Form(None), user: str = Cookie(None), db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.username == user, User.admin == True).first()
    if not admin_user:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    new_product = Product(name=name, description=description, price=price, image_url=image_url)
    db.add(new_product)
    db.commit()
    return RedirectResponse(url='/', status_code=303)


@router.post("/admin/products/remove/{product_id}")
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
