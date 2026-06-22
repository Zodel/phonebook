from database import get_db

# Получает список всех контактов из базы (с поддержкой поиска и сортировки)
def get_all_contacts(search=""):
    with get_db() as conn:
        if search:
            q = f"%{search}%"
            rows = conn.execute(
                """
                SELECT c.*, d.name AS dept_name, d.sort_order AS dept_sort
                FROM contacts c
                JOIN departments d ON d.id = c.department_id
                WHERE c.full_name LIKE ? OR c.position LIKE ?
                   OR c.internal_phone LIKE ? OR c.external_phone LIKE ?
                   OR c.office LIKE ? OR d.name LIKE ?
                ORDER BY d.sort_order, d.id, c.id
                """,
                (q, q, q, q, q, q),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT c.*, d.name AS dept_name, d.sort_order AS dept_sort
                FROM contacts c
                JOIN departments d ON d.id = c.department_id
                ORDER BY d.sort_order, d.id, c.id
                """
            ).fetchall()
        return [dict(r) for r in rows]

# Получает один контакт по его ID
def get_contact(contact_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        return dict(row) if row else None

# Создает новую запись контакта в базе данных
def create_contact(data):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO contacts
               (department_id, position, full_name, internal_phone, external_phone, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data["department_id"], data["position"], data["full_name"],
                data["internal_phone"], data["external_phone"], data["office"],
            ),
        )

# Обновляет данные существующего контакта
def update_contact(contact_id, data):
    with get_db() as conn:
        conn.execute(
            """UPDATE contacts SET
               department_id = ?, position = ?, full_name = ?,
               internal_phone = ?, external_phone = ?, office = ?
               WHERE id = ?""",
            (
                data["department_id"], data["position"], data["full_name"],
                data["internal_phone"], data["external_phone"], data["office"],
                contact_id,
            ),
        )

# Удаляет контакт из базы по ID
def delete_contact(contact_id):
    with get_db() as conn:
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))

# Возвращает список всех отделов, отсортированных по порядку
def get_all_departments():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM departments ORDER BY sort_order, id"
        ).fetchall()
        return [dict(r) for r in rows]

# Получает данные одного отдела по его ID
def get_department(dept_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM departments WHERE id = ?", (dept_id,)
        ).fetchone()
        return dict(row) if row else None

# Считает количество контактов в каждом отделе
def get_department_counts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT department_id, COUNT(*) AS cnt FROM contacts GROUP BY department_id"
        ).fetchall()
        return {r["department_id"]: r["cnt"] for r in rows}

# Добавляет новый отдел в базу
def create_department(name, sort_order):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO departments (name, sort_order) VALUES (?, ?)",
            (name, sort_order),
        )

# Обновляет название и порядок сортировки отдела
def update_department(dept_id, name, sort_order):
    with get_db() as conn:
        conn.execute(
            "UPDATE departments SET name = ?, sort_order = ? WHERE id = ?",
            (name, sort_order, dept_id),
        )

# Удаляет отдел из базы
def delete_department(dept_id):
    with get_db() as conn:
        conn.execute("DELETE FROM departments WHERE id = ?", (dept_id,))

# Получает данные администратора по имени пользователя
def get_admin(username):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None

# Обновляет пароль администратора
def update_admin_password(username, new_password):
    with get_db() as conn:
        conn.execute(
            "UPDATE admins SET password = ? WHERE username = ?",
            (new_password, username),
        )

# Группирует плоский список контактов в структуру по отделам
def group_contacts_by_department(contacts):
    groups = {}
    order = []
    for c in contacts:
        key = c["department_id"]
        if key not in groups:
            groups[key] = {"name": c["dept_name"], "contacts": []}
            order.append(key)
        groups[key]["contacts"].append(c)
    return [groups[k] for k in order]