#!/usr/bin/env python3
"""
FoodPlan — Meal planning web application.
"""

import os
import sqlite3
import hashlib
import subprocess
import pickle
import base64
import yaml
import requests
from flask import (
    Flask, request, render_template_string, redirect,
    session, send_file, jsonify, make_response
)

# ============================================================
# CONFIG
# ============================================================

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
app.debug = True

DATABASE = "foodplan.db"

# Admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
API_KEY = "sk-foodplan-4f3c2b1a-0000-1111-2222-333344445555"
DB_PASSWORD = "P@ssw0rd!"
SMTP_PASSWORD = "smtp_pass_2024"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


# ============================================================
# DATABASE SETUP
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            email TEXT,
            role TEXT DEFAULT 'user',
            reset_token TEXT
        );
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            ingredients TEXT,
            instructions TEXT,
            author TEXT,
            image_path TEXT,
            rating REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS meal_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            data TEXT,
            shared INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            user TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            ip TEXT,
            user_agent TEXT,
            body TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # seed admin
    existing = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not existing:
        pwd = hashlib.md5("admin123".encode()).hexdigest()
        db.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            ("admin", pwd, "admin@foodplan.local", "admin"),
        )
    db.commit()
    db.close()


init_db()


# ============================================================
# HTML TEMPLATES (inline)
# ============================================================

BASE_HTML = """
<!DOCTYPE html>
<html>
<head><title>FoodPlan - {{ title }}</title>
<style>
body { font-family: Arial; margin: 0; background: #f5f5f5; }
.nav { background: #2e7d32; padding: 10px 20px; color: white; }
.nav a { color: white; margin-right: 15px; text-decoration: none; }
.container { max-width: 900px; margin: 20px auto; padding: 20px; background: white; border-radius: 8px; }
input, textarea, select { width: 100%%; padding: 8px; margin: 5px 0 15px; box-sizing: border-box; }
.btn { background: #2e7d32; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px; }
.comment { background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 3px solid #2e7d32; }
.recipe-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }
.error { color: red; }
.success { color: green; }
</style>
</head>
<body>
<div class="nav">
    <b>FoodPlan</b>
    <a href="/">Home</a>
    <a href="/recipes">Recipes</a>
    <a href="/meal-plans">Meal Plans</a>
    {% if session.get('user') %}
        <a href="/profile">{{ session['user'] }}</a>
        <a href="/logout">Logout</a>
        {% if session.get('role') == 'admin' %}
            <a href="/admin">Admin</a>
        {% endif %}
    {% else %}
        <a href="/login">Login</a>
        <a href="/register">Register</a>
    {% endif %}
</div>
<div class="container">
{{ content }}
</div>
</body>
</html>
"""


# ============================================================
# AUTH ROUTES
# ============================================================

@app.route("/")
def index():
    content = "<h1>Welcome to FoodPlan</h1><p>Plan your meals, share recipes!</p>"
    return render_template_string(BASE_HTML, title="Home", content=content)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        # MD5 hashing
        hashed = hashlib.md5(password.encode()).hexdigest()

        db = get_db()
        # SQL injection in INSERT
        query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{hashed}', '{email}')"
        try:
            db.execute(query)
            db.commit()
        except Exception as e:
            return render_template_string(BASE_HTML, title="Register",
                content=f"<p class='error'>Error: {e}</p>")
        db.close()
        return redirect("/login")

    form = """
    <h2>Register</h2>
    <form method="POST">
        <label>Username:</label><input name="username">
        <label>Email:</label><input name="email">
        <label>Password:</label><input name="password" type="password">
        <button class="btn">Register</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Register", content=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed = hashlib.md5(password.encode()).hexdigest()

        db = get_db()
        # SQL injection in login
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{hashed}'"
        user = db.execute(query).fetchone()
        db.close()

        if user:
            session["user"] = user["username"]
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            return redirect("/")
        else:
            return render_template_string(BASE_HTML, title="Login",
                content="<p class='error'>Invalid credentials</p>")

    form = """
    <h2>Login</h2>
    <form method="POST">
        <label>Username:</label><input name="username">
        <label>Password:</label><input name="password" type="password">
        <button class="btn">Login</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Login", content=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        db = get_db()
        # SQL injection
        user = db.execute(f"SELECT * FROM users WHERE email = '{email}'").fetchone()
        if user:
            token = hashlib.md5(email.encode()).hexdigest()
            db.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
            db.commit()
            # Information disclosure: showing reset token directly
            return render_template_string(BASE_HTML, title="Reset",
                content=f"<p class='success'>Reset link: /reset-password?token={token}</p>")
        db.close()
        return render_template_string(BASE_HTML, title="Reset",
            content="<p class='error'>Email not found</p>")

    form = """
    <h2>Forgot Password</h2>
    <form method="POST">
        <label>Email:</label><input name="email">
        <button class="btn">Reset</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Forgot Password", content=form)


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "")
    if request.method == "POST":
        new_password = request.form["password"]
        hashed = hashlib.md5(new_password.encode()).hexdigest()
        db = get_db()
        db.execute(f"UPDATE users SET password = '{hashed}' WHERE reset_token = '{token}'")
        db.commit()
        db.close()
        return redirect("/login")

    form = f"""
    <h2>Reset Password</h2>
    <form method="POST">
        <input type="hidden" name="token" value="{token}">
        <label>New Password:</label><input name="password" type="password">
        <button class="btn">Reset Password</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Reset Password", content=form)


# ============================================================
# RECIPE ROUTES
# ============================================================

@app.route("/recipes")
def recipes():
    search = request.args.get("q", "")
    db = get_db()
    if search:
        # SQL injection in search
        query = f"SELECT * FROM recipes WHERE title LIKE '%{search}%' OR ingredients LIKE '%{search}%'"
        results = db.execute(query).fetchall()
    else:
        results = db.execute("SELECT * FROM recipes ORDER BY id DESC").fetchall()
    db.close()

    cards = ""
    for r in results:
        # XSS: title and ingredients rendered without escaping
        cards += f"""
        <div class="recipe-card">
            <h3><a href="/recipe/{r['id']}">{r['title']}</a></h3>
            <p><b>Ingredients:</b> {r['ingredients']}</p>
            <p>By: {r['author']} | Rating: {r['rating']}/5</p>
        </div>
        """

    # Reflected XSS: search term rendered back
    content = f"""
    <h2>Recipes</h2>
    <form method="GET">
        <input name="q" placeholder="Search recipes..." value="{search}">
        <button class="btn">Search</button>
    </form>
    <p>Showing results for: {search}</p>
    {cards}
    <a href="/recipes/new" class="btn">Add Recipe</a>
    """
    return render_template_string(BASE_HTML, title="Recipes", content=content)


@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    db = get_db()
    # SQL injection in path parameter
    recipe = db.execute(f"SELECT * FROM recipes WHERE id = {recipe_id}").fetchone()
    if not recipe:
        return "Recipe not found", 404

    comments = db.execute(
        f"SELECT * FROM comments WHERE recipe_id = {recipe_id} ORDER BY created_at DESC"
    ).fetchall()
    db.close()

    comment_html = ""
    for c in comments:
        # Stored XSS: comment content rendered unescaped
        comment_html += f"""
        <div class="comment">
            <b>{c['user']}</b>: {c['content']}
            <small>{c['created_at']}</small>
        </div>
        """

    content = f"""
    <h2>{recipe['title']}</h2>
    <p><b>Ingredients:</b> {recipe['ingredients']}</p>
    <p><b>Instructions:</b> {recipe['instructions']}</p>
    <p>Author: {recipe['author']}</p>
    {f"<img src='/uploads/{recipe['image_path']}' width='300'>" if recipe['image_path'] else ""}

    <h3>Comments</h3>
    {comment_html}
    <form method="POST" action="/recipe/{recipe_id}/comment">
        <textarea name="content" placeholder="Add a comment..."></textarea>
        <button class="btn">Post Comment</button>
    </form>
    """
    return render_template_string(BASE_HTML, title=recipe['title'], content=content)


@app.route("/recipe/<recipe_id>/comment", methods=["POST"])
def add_comment(recipe_id):
    user = session.get("user", "anonymous")
    content = request.form["content"]
    db = get_db()
    # SQL injection + stored XSS
    db.execute(
        f"INSERT INTO comments (recipe_id, user, content) VALUES ({recipe_id}, '{user}', '{content}')"
    )
    db.commit()
    db.close()
    return redirect(f"/recipe/{recipe_id}")


@app.route("/recipes/new", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        title = request.form["title"]
        ingredients = request.form["ingredients"]
        instructions = request.form["instructions"]
        author = session.get("user", "anonymous")
        image_path = ""

        # Insecure file upload — no validation at all
        if "image" in request.files:
            f = request.files["image"]
            if f.filename:
                image_path = f.filename
                f.save(os.path.join("uploads", f.filename))

        db = get_db()
        db.execute(
            f"INSERT INTO recipes (title, ingredients, instructions, author, image_path) "
            f"VALUES ('{title}', '{ingredients}', '{instructions}', '{author}', '{image_path}')"
        )
        db.commit()
        db.close()
        return redirect("/recipes")

    form = """
    <h2>New Recipe</h2>
    <form method="POST" enctype="multipart/form-data">
        <label>Title:</label><input name="title">
        <label>Ingredients:</label><textarea name="ingredients"></textarea>
        <label>Instructions:</label><textarea name="instructions"></textarea>
        <label>Image:</label><input type="file" name="image">
        <button class="btn">Create</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="New Recipe", content=form)


# ============================================================
# MEAL PLAN ROUTES
# ============================================================

@app.route("/meal-plans")
def meal_plans():
    user_id = session.get("user_id")
    db = get_db()
    # Shows all plans (no access control — IDOR)
    plans = db.execute("SELECT * FROM meal_plans ORDER BY id DESC").fetchall()
    db.close()

    items = ""
    for p in plans:
        items += f"<li><a href='/meal-plan/{p['id']}'>{p['name']}</a></li>"

    content = f"""
    <h2>Meal Plans</h2>
    <ul>{items}</ul>
    <a href="/meal-plans/new" class="btn">New Plan</a>
    """
    return render_template_string(BASE_HTML, title="Meal Plans", content=content)


@app.route("/meal-plans/new", methods=["GET", "POST"])
def new_meal_plan():
    if request.method == "POST":
        name = request.form["name"]
        data = request.form["data"]
        user_id = session.get("user_id", 0)
        db = get_db()
        db.execute(
            f"INSERT INTO meal_plans (user_id, name, data) VALUES ({user_id}, '{name}', '{data}')"
        )
        db.commit()
        db.close()
        return redirect("/meal-plans")

    form = """
    <h2>New Meal Plan</h2>
    <form method="POST">
        <label>Plan Name:</label><input name="name">
        <label>Plan Data (JSON):</label><textarea name="data">{"monday": "Pasta", "tuesday": "Salad"}</textarea>
        <button class="btn">Create</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="New Meal Plan", content=form)


@app.route("/meal-plan/<plan_id>")
def view_meal_plan(plan_id):
    db = get_db()
    # IDOR: no user ownership check
    plan = db.execute(f"SELECT * FROM meal_plans WHERE id = {plan_id}").fetchone()
    db.close()
    if not plan:
        return "Not found", 404

    content = f"""
    <h2>{plan['name']}</h2>
    <pre>{plan['data']}</pre>
    """
    return render_template_string(BASE_HTML, title=plan['name'], content=content)


# ============================================================
# PROFILE
# ============================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user"):
        return redirect("/login")

    if request.method == "POST":
        new_email = request.form["email"]
        db = get_db()
        # SQL injection in profile update
        db.execute(f"UPDATE users SET email = '{new_email}' WHERE username = '{session['user']}'")
        db.commit()
        db.close()
        session["email"] = new_email

    content = f"""
    <h2>Profile: {session.get('user')}</h2>
    <p>Email: {session.get('email')}</p>
    <p>Role: {session.get('role')}</p>
    <form method="POST">
        <label>Update email:</label><input name="email" value="{session.get('email', '')}">
        <button class="btn">Update</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Profile", content=content)


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
def admin_panel():
    # Broken access control: check only session, easily spoofable
    if session.get("role") != "admin":
        return "Forbidden", 403

    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    db.close()

    rows = ""
    for u in users:
        # Exposing password hashes in admin panel
        rows += f"<tr><td>{u['id']}</td><td>{u['username']}</td><td>{u['email']}</td><td>{u['password']}</td><td>{u['role']}</td></tr>"

    content = f"""
    <h2>Admin Panel</h2>
    <table border="1" cellpadding="5" width="100%">
        <tr><th>ID</th><th>Username</th><th>Email</th><th>Password Hash</th><th>Role</th></tr>
        {rows}
    </table>
    <br>
    <h3>System Tools</h3>
    <form method="POST" action="/admin/exec">
        <label>Run diagnostics command:</label>
        <input name="cmd" placeholder="e.g. uptime">
        <button class="btn">Execute</button>
    </form>
    """
    return render_template_string(BASE_HTML, title="Admin", content=content)


@app.route("/admin/exec", methods=["POST"])
def admin_exec():
    if session.get("role") != "admin":
        return "Forbidden", 403

    cmd = request.form["cmd"]
    # Command injection
    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    output = result.decode("utf-8", errors="replace")

    content = f"""
    <h2>Command Output</h2>
    <pre>{output}</pre>
    <a href="/admin">Back</a>
    """
    return render_template_string(BASE_HTML, title="Exec", content=content)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.route("/api/recipes", methods=["GET"])
def api_recipes():
    db = get_db()
    search = request.args.get("search", "")
    if search:
        rows = db.execute(f"SELECT * FROM recipes WHERE title LIKE '%{search}%'").fetchall()
    else:
        rows = db.execute("SELECT * FROM recipes").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/import", methods=["POST"])
def api_import():
    """Import meal plan from serialized data."""
    data = request.form.get("data", "")
    if data:
        # Insecure deserialization
        decoded = base64.b64decode(data)
        plan = pickle.loads(decoded)
        return jsonify({"imported": str(plan)})
    return jsonify({"error": "No data"}), 400


@app.route("/api/import-yaml", methods=["POST"])
def api_import_yaml():
    """Import configuration from YAML."""
    raw = request.data.decode("utf-8")
    # Unsafe YAML loading
    config = yaml.load(raw, Loader=yaml.Loader)
    return jsonify({"config": str(config)})


@app.route("/api/fetch-recipe", methods=["GET"])
def api_fetch_recipe():
    """Fetch recipe from external URL."""
    url = request.args.get("url", "")
    if url:
        # SSRF: fetches arbitrary URLs
        response = requests.get(url)
        return response.text
    return "Missing url param", 400


@app.route("/api/export/<filename>")
def api_export(filename):
    # Path traversal
    filepath = os.path.join("uploads", filename)
    return send_file(filepath)


@app.route("/api/log", methods=["POST"])
def api_log():
    """Log API access — stores raw user input."""
    body = request.get_data(as_text=True)
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    db = get_db()
    # SQL injection via headers
    db.execute(
        f"INSERT INTO api_logs (endpoint, ip, user_agent, body) "
        f"VALUES ('/api/log', '{ip}', '{ua}', '{body}')"
    )
    db.commit()
    db.close()
    return jsonify({"status": "logged"})


@app.route("/api/debug")
def api_debug():
    # Information disclosure: dumps environment and config
    return jsonify({
        "debug": True,
        "secret_key": app.secret_key,
        "api_key": API_KEY,
        "db_password": DB_PASSWORD,
        "aws_key": AWS_SECRET_KEY,
        "env": dict(os.environ),
        "database": DATABASE,
    })


@app.route("/api/eval", methods=["POST"])
def api_eval():
    """Evaluate nutrition expression."""
    expr = request.form.get("expr", "")
    # Code injection via eval
    result = eval(expr)
    return jsonify({"result": result})


# ============================================================
# FILE HANDLING
# ============================================================

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    # Path traversal in file serving
    return send_file(os.path.join("uploads", filename))


@app.route("/download")
def download_file():
    path = request.args.get("file", "")
    # Direct path traversal — can read any file on disk
    return send_file(path)


# ============================================================
# ERROR HANDLING
# ============================================================

@app.errorhandler(500)
def internal_error(e):
    # Exposes stack trace and internal details
    import traceback
    tb = traceback.format_exc()
    return f"<h1>Internal Server Error</h1><pre>{tb}</pre>", 500


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
