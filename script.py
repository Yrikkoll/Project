import sqlite3

DB_NAME = "phone_book.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Створюємо базову таблицю (без нових колонок)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL
    )
    """)

    # Перевіряємо, які колонки вже існують
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [column[1] for column in cursor.fetchall()]

    # Додаємо нові колонки якщо їх нема
    if "telegram" not in columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN telegram TEXT")

    if "viber" not in columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN viber TEXT")

    conn.commit()
    return conn, cursor


def add_contact(cursor, conn):
    name = input("Ім'я: ")
    phone = input("Телефон: ")
    telegram = input("Telegram (можна залишити пустим): ")
    viber = input("Viber (можна залишити пустим): ")

    cursor.execute("""
        INSERT INTO contacts (name, phone, telegram, viber)
        VALUES (?, ?, ?, ?)
    """, (name, phone, telegram, viber))

    conn.commit()
    print("Контакт додано.")


def show_contacts(cursor):
    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()

    if not contacts:
        print("База порожня.")
        return

    for contact in contacts:
        print("ID:", contact[0])
        print("Ім'я:", contact[1])
        print("Телефон:", contact[2])
        print("Telegram:", contact[3])
        print("Viber:", contact[4])
        print("------------------------")


def edit_contact(cursor, conn):
    show_contacts(cursor)
    contact_id = input("Введіть ID контакту для редагування: ")

    name = input("Нове ім'я: ")
    phone = input("Новий телефон: ")
    telegram = input("Новий Telegram: ")
    viber = input("Новий Viber: ")

    cursor.execute("""
        UPDATE contacts
        SET name=?, phone=?, telegram=?, viber=?
        WHERE id=?
    """, (name, phone, telegram, viber, contact_id))

    conn.commit()

    if cursor.rowcount == 0:
        print("Контакт не знайдено.")
    else:
        print("Контакт оновлено.")


def delete_contact(cursor, conn):
    show_contacts(cursor)
    contact_id = input("Введіть ID контакту для видалення: ")

    cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
    conn.commit()

    if cursor.rowcount == 0:
        print("Контакт не знайдено.")
    else:
        print("Контакт видалено.")


def search_contact(cursor):
    keyword = input("Введіть дані для пошуку: ")

    cursor.execute("""
        SELECT * FROM contacts
        WHERE name LIKE ?
        OR phone LIKE ?
        OR telegram LIKE ?
        OR viber LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

    results = cursor.fetchall()

    if not results:
        print("Нічого не знайдено.")
        return

    for contact in results:
        print("ID:", contact[0])
        print("Ім'я:", contact[1])
        print("Телефон:", contact[2])
        print("Telegram:", contact[3])
        print("Viber:", contact[4])
        print("------------------------")


def main():
    conn, cursor = init_db()

    while True:
        print("\nТелефонна книга (SQLite)")
        print("1. Додати контакт")
        print("2. Показати всі контакти")
        print("3. Редагувати контакт")
        print("4. Видалити контакт")
        print("5. Пошук")
        print("0. Вихід")

        choice = input("Ваш вибір: ")

        if choice == "1":
            add_contact(cursor, conn)
        elif choice == "2":
            show_contacts(cursor)
        elif choice == "3":
            edit_contact(cursor, conn)
        elif choice == "4":
            delete_contact(cursor, conn)
        elif choice == "5":
            search_contact(cursor)
        elif choice == "0":
            break
        else:
            print("Невірний вибір.")

    conn.close()


if __name__ == "__main__":
    main()