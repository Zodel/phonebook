import hashlib
import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

import crud
from schemas import ContactCreate, ContactOut, DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/api")
security = HTTPBasic()

# Вычисляет SHA256 хеш пароля
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Проверяет логин и пароль администратора через Basic Auth
def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    admin = crud.get_admin(credentials.username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверный логин или пароль",
                            headers={"WWW-Authenticate": "Basic"})
    # Сравниваем хеши через secrets.compare_digest чтобы избежать timing attack
    expected = hash_password(credentials.password)
    if not secrets.compare_digest(admin["password"], expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Неверный логин или пароль",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username

# Возвращает список всех отделов
@router.get("/departments", response_model=List[DepartmentOut])
def api_get_departments(admin: str = Depends(require_admin)):
    return crud.get_all_departments()

# Добавляет новый отдел
@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def api_create_department(data: DepartmentCreate, admin: str = Depends(require_admin)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название отдела не может быть пустым")
    crud.create_department(name, data.sort_order)
    # Возвращаем только что созданный отдел
    departments = crud.get_all_departments()
    return next(d for d in reversed(departments) if d["name"] == name)

# Возвращает список всех контактов
@router.get("/contacts", response_model=List[ContactOut])
def api_get_contacts(admin: str = Depends(require_admin)):
    return crud.get_all_contacts()

# Добавляет новый контакт
@router.post("/contacts", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def api_create_contact(data: ContactCreate, admin: str = Depends(require_admin)):
    if not data.full_name.strip():
        raise HTTPException(status_code=400, detail="ФИО не может быть пустым")
    dept = crud.get_department(data.department_id)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Отдел с id={data.department_id} не найден")
    crud.create_contact({
        "department_id": data.department_id,
        "position":       data.position.strip(),
        "full_name":      data.full_name.strip(),
        "internal_phone": (data.internal_phone or "").strip(),
        "external_phone": (data.external_phone or "").strip(),
        "office":         (data.office or "").strip(),
    })
    # Возвращаем только что созданный контакт (последний с таким full_name)
    contacts = crud.get_all_contacts()
    return next(c for c in reversed(contacts) if c["full_name"] == data.full_name.strip())