import sqlite3
from flask import Flask, request, redirect, url_for, render_template_string, jsonify

app = Flask(__name__)
DB_NAME = "phone_book.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL
    )
    """)
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [column[1] for column in cursor.fetchall()]

    if "telegram" not in columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN telegram TEXT")
    if "viber" not in columns:
        cursor.execute("ALTER TABLE contacts ADD COLUMN viber TEXT")

    conn.commit()
    conn.close()


init_db()


@app.route("/api/contacts", methods=["GET"])
def api_get_contacts():
    search_query = request.args.get("q", "").strip()
    conn = get_db_connection()

    if search_query:
        contacts = conn.execute("""
            SELECT * FROM contacts
            WHERE name LIKE ? OR phone LIKE ? OR telegram LIKE ? OR viber LIKE ?
            ORDER BY id DESC
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")).fetchall()
    else:
        contacts = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()

    conn.close()
    return jsonify([dict(contact) for contact in contacts])


@app.route("/api/contacts/<int:id>", methods=["GET"])
def api_get_contact(id):
    conn = get_db_connection()
    contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (id,)).fetchone()
    conn.close()

    if contact is None:
        return jsonify({"error": "Контакт не знайдено"}), 404

    return jsonify(dict(contact))


@app.route("/api/contacts", methods=["POST"])
def api_create_contact():
    data = request.get_json()

    if not data or not data.get("name") or not data.get("phone"):
        return jsonify({"error": "Поля 'name' та 'phone' є обов'язковими"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contacts (name, phone, telegram, viber)
        VALUES (?, ?, ?, ?)
    """, (data.get("name"), data.get("phone"), data.get("telegram", ""), data.get("viber", "")))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Контакт створено", "id": new_id}), 201


@app.route("/api/contacts/<int:id>", methods=["DELETE"])
def api_delete_contact(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = ?", (id,))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Контакт не знайдено"}), 404

    conn.close()
    return jsonify({"message": "Контакт успішно видалено"}), 200


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сучасна Телефонна Книга</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100 min-h-screen font-sans text-gray-800">
    <div class="container mx-auto px-4 py-8 max-w-5xl">
        <header class="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
            <h1 class="text-3xl font-bold text-indigo-600 flex items-center gap-3">
                <i class="fas fa-address-book"></i> Телефонна книга
            </h1>
            <form action="/" method="GET" class="w-full md:w-1/3 relative">
                <input type="text" name="q" value="{{ search_query }}" placeholder="Пошук контактів..." 
                       class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm">
                <i class="fas fa-search absolute left-3 top-3 text-gray-400"></i>
                {% if search_query %}
                    <a href="/" class="absolute right-3 top-3 text-gray-400 hover:text-red-500"><i class="fas fa-times"></i></a>
                {% endif %}
            </form>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="bg-white p-6 rounded-xl shadow-md h-fit">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">Додати контакт</h2>
                <form action="/add" method="POST" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-600">Ім'я</label>
                        <input type="text" name="name" required class="mt-1 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-600">Телефон</label>
                        <input type="text" name="phone" required class="mt-1 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-600">Telegram</label>
                        <input type="text" name="telegram" class="mt-1 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-600">Viber</label>
                        <input type="text" name="viber" class="mt-1 w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none">
                    </div>
                    <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200">
                        <i class="fas fa-plus mr-2"></i>Додати
                    </button>
                </form>
            </div>

            <div class="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {% if not contacts %}
                    <div class="col-span-full bg-yellow-50 text-yellow-600 p-4 rounded-lg text-center border border-yellow-200">
                        <i class="fas fa-inbox text-3xl mb-2"></i>
                        <p>Контактів не знайдено.</p>
                    </div>
                {% endif %}

                {% for contact in contacts %}
                <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition duration-200 relative group">
                    <h3 class="text-lg font-bold text-gray-800">{{ contact.name }}</h3>
                    <p class="text-gray-500 mt-1"><i class="fas fa-phone-alt text-sm mr-2"></i>{{ contact.phone }}</p>

                    <div class="mt-4 flex gap-2">
                        {% if contact.telegram %}
                        <span class="bg-blue-100 text-blue-600 text-xs px-2 py-1 rounded-full flex items-center">
                            <i class="fab fa-telegram-plane mr-1"></i> {{ contact.telegram }}
                        </span>
                        {% endif %}
                        {% if contact.viber %}
                        <span class="bg-purple-100 text-purple-600 text-xs px-2 py-1 rounded-full flex items-center">
                            <i class="fab fa-viber mr-1"></i> {{ contact.viber }}
                        </span>
                        {% endif %}
                    </div>

                    <form action="/delete/{{ contact.id }}" method="POST" class="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition">
                        <button type="submit" class="text-red-400 hover:text-red-600 bg-red-50 hover:bg-red-100 p-2 rounded-full" title="Видалити">
                            <i class="fas fa-trash"></i>
                        </button>
                    </form>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    conn = get_db_connection()
    if search_query:
        contacts = conn.execute("""
            SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ? OR telegram LIKE ? OR viber LIKE ? ORDER BY id DESC
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")).fetchall()
    else:
        contacts = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, contacts=contacts, search_query=search_query)


@app.route("/add", methods=["POST"])
def add_contact():
    name = request.form["name"]
    phone = request.form["phone"]
    telegram = request.form.get("telegram", "")
    viber = request.form.get("viber", "")
    conn = get_db_connection()
    conn.execute("INSERT INTO contacts (name, phone, telegram, viber) VALUES (?, ?, ?, ?)",
                 (name, phone, telegram, viber))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:id>", methods=["POST"])
def delete_contact(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM contacts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("Сервер запущено! UI доступний за адресою: http://127.0.0.1:5000")
    print("API доступно за адресою: http://127.0.0.1:5000/api/contacts")
    app.run(debug=True, host='0.0.0.0')