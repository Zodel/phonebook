import secrets
import io
import csv
import hashlib
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import crud
from database import init_db

init_db()

app = FastAPI(docs_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SESSION_COOKIE = "pb_session"
active_sessions = set()

# Вычисляет SHA256 хеш для пароля
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Проверяет, авторизован ли пользователь через сессию
def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token and token in active_sessions:
        return "admin"
    return None

# Отображает главную страницу с поиском контактов
@app.get("/", response_class=HTMLResponse)
def index(request: Request, search: str = ""):
    contacts = crud.get_all_contacts(search)
    dept_groups = crud.group_contacts_by_department(contacts)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dept_groups": dept_groups,
        "search": search,
    })

# Отображает форму входа в систему
@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

# Обрабатывает POST-запрос формы входа и проверяет пароль
@app.post("/admin/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    admin = crud.get_admin(username)
    if admin and admin["password"] == hash_password(password):
        token = secrets.token_hex(16)
        active_sessions.add(token)
        resp = RedirectResponse("/admin", status_code=302)
        resp.set_cookie(SESSION_COOKIE, token, httponly=True, max_age=3600 * 8)
        return resp
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Неверный логин или пароль"},
        status_code=401,
    )

# Завершает сессию и удаляет cookies
@app.get("/admin/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    active_sessions.discard(token)
    resp = RedirectResponse("/admin/login", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

# Показывает главную страницу администрирования
@app.get("/admin", response_class=HTMLResponse)
def admin_contacts(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    contacts = crud.get_all_contacts()
    departments = crud.get_all_departments()
    return templates.TemplateResponse("admin/contacts.html", {
        "request": request,
        "contacts": contacts,
        "departments": departments,
        "msg": request.query_params.get("msg", ""),
    })

# Показывает страницу для добавления нового контакта
@app.get("/admin/contacts/add", response_class=HTMLResponse)
def contact_add_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    departments = crud.get_all_departments()
    return templates.TemplateResponse("admin/contacts_form.html", {
        "request": request, "contact": None, "departments": departments, "error": "",
    })

# Сохраняет данные нового контакта в БД
@app.post("/admin/contacts/add")
def contact_add_post(request: Request,
    department_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(...), internal_phone: str = Form(""),
    external_phone: str = Form(""), office: str = Form("")):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.create_contact({
        "department_id": department_id,
        "position": position.strip(),
        "full_name": full_name.strip(),
        "internal_phone": internal_phone.strip(),
        "external_phone": external_phone.strip(),
        "office": office.strip(),
    })
    return RedirectResponse("/admin?msg=added", status_code=302)

# Показывает страницу редактирования контакта
@app.get("/admin/contacts/{cid}/edit", response_class=HTMLResponse)
def contact_edit_page(cid: int, request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    contact = crud.get_contact(cid)
    departments = crud.get_all_departments()
    return templates.TemplateResponse("admin/contacts_form.html", {
        "request": request, "contact": contact, "departments": departments, "error": "",
    })

# Обновляет информацию о существующем контакте
@app.post("/admin/contacts/{cid}/edit")
def contact_edit_post(cid: int, request: Request,
    department_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(...), internal_phone: str = Form(""),
    external_phone: str = Form(""), office: str = Form("")):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.update_contact(cid, {
        "department_id": department_id,
        "position": position.strip(),
        "full_name": full_name.strip(),
        "internal_phone": internal_phone.strip(),
        "external_phone": external_phone.strip(),
        "office": office.strip(),
    })
    return RedirectResponse("/admin?msg=updated", status_code=302)

# Удаляет контакт из базы
@app.post("/admin/contacts/{cid}/delete")
def contact_delete(cid: int, request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.delete_contact(cid)
    return RedirectResponse("/admin?msg=deleted", status_code=302)

# Показывает список отделов в админпанели
@app.get("/admin/departments", response_class=HTMLResponse)
def admin_depts(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    departments = crud.get_all_departments()
    counts = crud.get_department_counts()
    return templates.TemplateResponse("admin/departments.html", {
        "request": request,
        "departments": departments,
        "counts": counts,
        "msg": request.query_params.get("msg", ""),
    })

# Показывает форму создания нового отдела
@app.get("/admin/departments/add", response_class=HTMLResponse)
def dept_add_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    return templates.TemplateResponse("admin/departments_form.html", {"request": request, "dept": None, "error": ""})

# Сохраняет новый отдел в базу
@app.post("/admin/departments/add")
def dept_add_post(request: Request, name: str = Form(...), sort_order: int = Form(0)):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.create_department(name.strip(), sort_order)
    return RedirectResponse("/admin/departments?msg=added", status_code=302)

# Показывает страницу редактирования отдела
@app.get("/admin/departments/{did}/edit", response_class=HTMLResponse)
def dept_edit_page(did: int, request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    dept = crud.get_department(did)
    return templates.TemplateResponse("admin/departments_form.html", {"request": request, "dept": dept, "error": ""})

# Сохраняет изменения в отделе
@app.post("/admin/departments/{did}/edit")
def dept_edit_post(did: int, request: Request, name: str = Form(...), sort_order: int = Form(0)):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.update_department(did, name.strip(), sort_order)
    return RedirectResponse("/admin/departments?msg=updated", status_code=302)

# Удаляет отдел из базы
@app.post("/admin/departments/{did}/delete")
def dept_delete(did: int, request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    crud.delete_department(did)
    return RedirectResponse("/admin/departments?msg=deleted", status_code=302)

# Страница смены пароля
@app.get("/admin/password", response_class=HTMLResponse)
def password_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    return templates.TemplateResponse("admin/password.html", {"request": request, "msg": "", "error": ""})

# Обрабатывает смену пароля админа
@app.post("/admin/password")
def password_post(request: Request,
    old_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    admin = crud.get_admin("admin")
    ctx = {"request": request, "msg": "", "error": ""}
    if admin["password"] != hash_password(old_password):
        ctx["error"] = "Текущий пароль неверен"
        return templates.TemplateResponse("admin/password.html", ctx)
    if new_password != confirm_password:
        ctx["error"] = "Новые пароли не совпадают"
        return templates.TemplateResponse("admin/password.html", ctx)
    if len(new_password) < 4:
        ctx["error"] = "Пароль должен быть не менее 4 символов"
        return templates.TemplateResponse("admin/password.html", ctx)
    crud.update_admin_password("admin", hash_password(new_password))
    ctx["msg"] = "Пароль успешно изменён"
    return templates.TemplateResponse("admin/password.html", ctx)

# Показывает страницу импорта
@app.get("/admin/import", response_class=HTMLResponse)
def import_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    return templates.TemplateResponse("admin/import.html", {"request": request, "msg": "", "error": ""})

# Выгружает данные контактов в CSV
@app.get("/admin/export")
def export_csv(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    contacts = crud.get_all_contacts()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["department", "position", "full_name", "internal_phone", "external_phone", "office"])
    for c in contacts:
        writer.writerow([
            c["dept_name"], c["position"], c["full_name"],
            c["internal_phone"] or "", c["external_phone"] or "", c["office"] or "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=phonebook.csv"},
    )

# Обрабатывает импорт контактов из CSV-файла
@app.post("/admin/import")
async def import_post(request: Request):
    if not get_current_user(request):
        return RedirectResponse("/admin/login", status_code=302)
    ctx = {"request": request, "msg": "", "error": ""}
    form = await request.form()
    file = form.get("csvfile")
    if not file or not getattr(file, "filename", None):
        ctx["error"] = "Выберите CSV-файл"
        return templates.TemplateResponse("admin/import.html", ctx)
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except Exception:
        text = content.decode("cp1251", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    departments_by_name = {d["name"]: d["id"] for d in crud.get_all_departments()}
    imported = 0
    for row in reader:
        dept_name = (row.get("department") or "").strip()
        if not dept_name:
            continue
        if dept_name not in departments_by_name:
            crud.create_department(dept_name, 0)
            departments_by_name = {d["name"]: d["id"] for d in crud.get_all_departments()}
        crud.create_contact({
            "department_id": departments_by_name[dept_name],
            "position": (row.get("position") or "").strip(),
            "full_name": (row.get("full_name") or "").strip(),
            "internal_phone": (row.get("internal_phone") or "").strip(),
            "external_phone": (row.get("external_phone") or "").strip(),
            "office": (row.get("office") or "").strip(),
        })
        imported += 1
    ctx["msg"] = f"Импортировано записей: {imported}"
    return templates.TemplateResponse("admin/import.html", ctx)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)