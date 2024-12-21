from fastapi import APIRouter, Request, Depends, Cookie, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from temp import templates
from database import get_db
from models import User, Cart

router = APIRouter()

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request, user: str = Cookie(None), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")
    user_db = db.query(User).filter(User.username == user).first()
    cart_items = db.query(Cart).filter(Cart.user_id == user_db.id).all()
    return templates.TemplateResponse("cart.html", {"request": request, "cart_items": cart_items, "user": user})

@router.post("/cart/add/{product_id}")
async def add_to_cart(product_id: int, user: str = Cookie(None), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=403, detail="Пользователь не авторизован")
    user_db = db.query(User).filter(User.username == user).first()
    if not user_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    existing_cart_item = db.query(Cart).filter(Cart.user_id == user_db.id, Cart.product_id == product_id).first()
    if existing_cart_item:
        return RedirectResponse(url='/?error=Товар уже в корзине', status_code=303)
    new_cart_item = Cart(user_id=user_db.id, product_id=product_id)
    db.add(new_cart_item)
    db.commit()
    return RedirectResponse(url='/', status_code=303)

@router.post("/cart/remove/{cart_item_id}")
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
