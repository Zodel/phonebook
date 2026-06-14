from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#Фиктивные данные
DEPARTMENTS = [
    {"id": 1, "name": "Руководство"},
    {"id": 2, "name": "Отдел информационных технологий"},
    {"id": 3, "name": "Бухгалтерия"},
    {"id": 4, "name": "Отдел кадров"},
]

CONTACTS = [
    {"id": 1, "dept_id": 1, "dept": "Руководство",                          "position": "Генеральный директор",       "full_name": "Иванов Иван Иванович",      "internal": "1000", "external": "+7 (495) 000-00-01", "office": "101"},
    {"id": 2, "dept_id": 1, "dept": "Руководство",                          "position": "Заместитель директора",      "full_name": "Петрова Мария Сергеевна",   "internal": "1001", "external": "+7 (495) 000-00-02", "office": "102"},
    {"id": 3, "dept_id": 1, "dept": "Руководство",                          "position": "Помощник руководителя",      "full_name": "Соколова Анна Дмитриевна",  "internal": "1002", "external": "+7 (495) 000-00-03", "office": "103"},
    {"id": 4, "dept_id": 2, "dept": "Отдел информационных технологий",      "position": "Начальник отдела",           "full_name": "Сидоров Алексей Петрович",  "internal": "2000", "external": "+7 (495) 000-00-04", "office": "210"},
    {"id": 5, "dept_id": 2, "dept": "Отдел информационных технологий",      "position": "Программист",                "full_name": "Козлова Ольга Николаевна",  "internal": "2001", "external": "+7 (495) 000-00-05", "office": "211"},
    {"id": 6, "dept_id": 2, "dept": "Отдел информационных технологий",      "position": "Системный администратор",    "full_name": "Новиков Дмитрий Андреевич", "internal": "2002", "external": "+7 (495) 000-00-06", "office": "212"},
    {"id": 7, "dept_id": 3, "dept": "Бухгалтерия",                          "position": "Главный бухгалтер",          "full_name": "Волкова Елена Викторовна",  "internal": "3000", "external": "+7 (495) 000-00-07", "office": "305"},
    {"id": 8, "dept_id": 3, "dept": "Бухгалтерия",                          "position": "Бухгалтер",                  "full_name": "Зайцев Сергей Михайлович",  "internal": "3001", "external": "+7 (495) 000-00-08", "office": "306"},
    {"id": 9, "dept_id": 4, "dept": "Отдел кадров",                         "position": "Начальник отдела кадров",    "full_name": "Лебедева Татьяна Игоревна", "internal": "4000", "external": "+7 (495) 000-00-09", "office": "401"},
    {"id":10, "dept_id": 4, "dept": "Отдел кадров",                         "position": "Специалист по кадрам",       "full_name": "Кузнецов Павел Романович",  "internal": "4001", "external": "+7 (495) 000-00-10", "office": "402"},
]


def group_by_dept(contacts):
    groups = {}
    order = []
    for c in contacts:
        key = c["dept_id"]
        if key not in groups:
            groups[key] = {"name": c["dept"], "contacts": []}
            order.append(key)
        groups[key]["contacts"].append(c)
    return [groups[k] for k in order]


@app.get("/", response_class=HTMLResponse)
def index(request: Request, search: str = ""):
    contacts = CONTACTS
    if search:
        q = search.lower()
        contacts = [
            c for c in contacts
            if q in c["full_name"].lower()
            or q in c["position"].lower()
            or q in c["internal"].lower()
            or q in c["external"].lower()
            or q in c["office"].lower()
            or q in c["dept"].lower()
        ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dept_groups": group_by_dept(contacts),
        "search": search,
    })


@app.get("/admin/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})

@app.post("/admin/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin123":
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"}, status_code=401)

@app.get("/admin/logout")
def logout():
    return RedirectResponse("/admin/login", status_code=302)


@app.get("/admin", response_class=HTMLResponse)
def admin_contacts(request: Request):
    return templates.TemplateResponse("admin/contacts.html", {
        "request": request,
        "contacts": CONTACTS,
        "departments": DEPARTMENTS,
        "msg": request.query_params.get("msg", ""),
    })

@app.get("/admin/contacts/add", response_class=HTMLResponse)
def contact_add_page(request: Request):
    return templates.TemplateResponse("admin/contacts_form.html", {
        "request": request, "contact": None, "departments": DEPARTMENTS, "error": "",
    })

@app.post("/admin/contacts/add")
def contact_add_post(request: Request,
    department_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(...), internal_phone: str = Form(""),
    external_phone: str = Form(""), office: str = Form("")):
    # В прототипе просто редиректим обратно
    return RedirectResponse("/admin?msg=added", status_code=302)

@app.get("/admin/contacts/{cid}/edit", response_class=HTMLResponse)
def contact_edit_page(cid: int, request: Request):
    contact = next((c for c in CONTACTS if c["id"] == cid), None)
    return templates.TemplateResponse("admin/contacts_form.html", {
        "request": request, "contact": contact, "departments": DEPARTMENTS, "error": "",
    })

@app.post("/admin/contacts/{cid}/edit")
def contact_edit_post(cid: int, request: Request,
    department_id: int = Form(...), position: str = Form(...),
    full_name: str = Form(...), internal_phone: str = Form(""),
    external_phone: str = Form(""), office: str = Form("")):
    return RedirectResponse("/admin?msg=updated", status_code=302)

@app.post("/admin/contacts/{cid}/delete")
def contact_delete(cid: int, request: Request):
    return RedirectResponse("/admin?msg=deleted", status_code=302)


@app.get("/admin/departments", response_class=HTMLResponse)
def admin_depts(request: Request):
    return templates.TemplateResponse("admin/departments.html", {
        "request": request,
        "departments": DEPARTMENTS,
        "counts": {d["id"]: sum(1 for c in CONTACTS if c["dept_id"] == d["id"]) for d in DEPARTMENTS},
        "msg": request.query_params.get("msg", ""),
    })

@app.get("/admin/departments/add", response_class=HTMLResponse)
def dept_add_page(request: Request):
    return templates.TemplateResponse("admin/departments_form.html", {"request": request, "dept": None, "error": ""})

@app.post("/admin/departments/add")
def dept_add_post(name: str = Form(...), sort_order: int = Form(0)):
    return RedirectResponse("/admin/departments?msg=added", status_code=302)

@app.get("/admin/departments/{did}/edit", response_class=HTMLResponse)
def dept_edit_page(did: int, request: Request):
    dept = next((d for d in DEPARTMENTS if d["id"] == did), None)
    return templates.TemplateResponse("admin/departments_form.html", {"request": request, "dept": dept, "error": ""})

@app.post("/admin/departments/{did}/edit")
def dept_edit_post(did: int, name: str = Form(...), sort_order: int = Form(0)):
    return RedirectResponse("/admin/departments?msg=updated", status_code=302)

@app.post("/admin/departments/{did}/delete")
def dept_delete(did: int):
    return RedirectResponse("/admin/departments?msg=deleted", status_code=302)


@app.get("/admin/password", response_class=HTMLResponse)
def password_page(request: Request):
    return templates.TemplateResponse("admin/password.html", {"request": request, "msg": "", "error": ""})

@app.post("/admin/password")
def password_post(request: Request,
    old_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    if new_password != confirm_password:
        return templates.TemplateResponse("admin/password.html", {"request": request, "msg": "", "error": "Новые пароли не совпадают"})
    return templates.TemplateResponse("admin/password.html", {"request": request, "msg": "Пароль изменён (прототип)", "error": ""})


@app.get("/admin/import", response_class=HTMLResponse)
def import_page(request: Request):
    return templates.TemplateResponse("admin/import.html", {"request": request, "msg": "", "error": ""})

@app.post("/admin/import")
async def import_post(request: Request):
    return templates.TemplateResponse("admin/import.html", {"request": request, "msg": "Импорт будет доступен после подключения БД", "error": ""})

@app.get("/admin/export")
def export():
    return RedirectResponse("/admin/import", status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)