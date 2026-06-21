import sqlite3
from contextlib import contextmanager

DB_PATH = "phonebook.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            full_name TEXT NOT NULL,
            internal_phone TEXT,
            external_phone TEXT,
            office TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
        )
    """)

    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", "admin123"),
        )

    cur.execute("SELECT COUNT(*) FROM departments")
    if cur.fetchone()[0] == 0:
        #Фиктивные данные
        departments = [
            ("Руководство", 1),
            ("Отдел информационных технологий", 2),
            ("Бухгалтерия", 3),
            ("Отдел кадров", 4),
        ]
        cur.executemany(
            "INSERT INTO departments (name, sort_order) VALUES (?, ?)",
            departments,
        )

        contacts = [
            (1, "Генеральный директор", "Иванов Иван Иванович", "1000", "+7 (495) 000-00-01", "101"),
            (1, "Заместитель директора", "Петрова Мария Сергеевна", "1001", "+7 (495) 000-00-02", "102"),
            (1, "Помощник руководителя", "Соколова Анна Дмитриевна", "1002", "+7 (495) 000-00-03", "103"),
            (2, "Начальник отдела", "Сидоров Алексей Петрович", "2000", "+7 (495) 000-00-04", "210"),
            (2, "Программист", "Козлова Ольга Николаевна", "2001", "+7 (495) 000-00-05", "211"),
            (2, "Системный администратор", "Новиков Дмитрий Андреевич", "2002", "+7 (495) 000-00-06", "212"),
            (3, "Главный бухгалтер", "Волкова Елена Викторовна", "3000", "+7 (495) 000-00-07", "305"),
            (3, "Бухгалтер", "Зайцев Сергей Михайлович", "3001", "+7 (495) 000-00-08", "306"),
            (4, "Начальник отдела кадров", "Лебедева Татьяна Игоревна", "4000", "+7 (495) 000-00-09", "401"),
            (4, "Специалист по кадрам", "Кузнецов Павел Романович", "4001", "+7 (495) 000-00-10", "402"),
        ]
        cur.executemany(
            """INSERT INTO contacts
               (department_id, position, full_name, internal_phone, external_phone, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            contacts,
        )

    conn.commit()
    conn.close()
