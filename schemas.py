from pydantic import BaseModel
from typing import Optional
 
 
# Схема для создания отдела
class DepartmentCreate(BaseModel):
    name: str
    sort_order: int = 0

# Схема для отображения отдела в ответе
class DepartmentOut(BaseModel):
    id: int
    name: str
    sort_order: int

# Схема для создания контакта
class ContactCreate(BaseModel):
    department_id: int
    position: str
    full_name: str
    internal_phone: Optional[str] = ""
    external_phone: Optional[str] = ""
    office: Optional[str] = ""

# Схема для отображения контакта в ответе
class ContactOut(BaseModel):
    id: int
    department_id: int
    position: str
    full_name: str
    internal_phone: Optional[str]
    external_phone: Optional[str]
    office: Optional[str]
    dept_name: Optional[str] = None