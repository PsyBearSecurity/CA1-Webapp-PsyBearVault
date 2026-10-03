import sqlite3
import re
import os

from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# Temporary during development.
# We will secure this properly before submission.
app.secret_key = os.environ.get("SECRET_KEY")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# -------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------

def create_database():

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)


# -------------------------------------------------
# CREATE DEFAULT ADMIN
# -------------------------------------------------

def create_admin():

    admin_username = "admin"
    admin_password = os.environ.get("ADMIN_PASSWORD")

    password_hash = generate_password_hash(admin_password)

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        existing_admin = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (admin_username,)
        ).fetchone()

        if not existing_admin:

            connection.execute(
                """
                INSERT INTO users
                (username, password_hash, role, is_active)
                VALUES (?, ?, ?, ?)
                """,
                (
                    admin_username,
                    password_hash,
                    "admin",
                    1
                )
            )


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -------------------------------------------------
# REGISTER
# -------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Basic input validation
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username):
            return "Username must be 3-30 characters and contain only letters, numbers or underscores."

        if len(password) < 12:
            return "Password must be at least 12 characters long."

        password_hash = generate_password_hash(password)

        try:

            with sqlite3.connect("securevault.db", timeout=10) as connection:

                connection.execute(
                    """
                    INSERT INTO users
                    (username, password_hash, role, is_active)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        username,
                        password_hash,
                        "user",
                        1
                    )
                )

        except sqlite3.IntegrityError:

            return "Unable to create account. Please choose another username."

        return render_template("registration-successful.html")

    return render_template("register.html")


# -------------------------------------------------
# LOGIN
# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("securevault.db", timeout=10) as connection:

            user = connection.execute(
                """
                SELECT id, username, password_hash, role, is_active
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

        # Generic login failure
        if not user:
            return "Invalid username or password."

        if not check_password_hash(user[2], password):
            return "Invalid username or password."

        # Check if administrator has disabled the account
        if user[4] == 0:
            return "This account is disabled."

        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[3]

        # Send administrators to the admin dashboard
        if user[3] == "admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# -------------------------------------------------
# USER DASHBOARD
# -------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Admin should use the admin dashboard
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        notes = connection.execute(
            """
            SELECT id, title, content
            FROM notes
            WHERE user_id = ?
            """,
            (session["user_id"],)
        ).fetchall()

    return render_template(
        "dashboard.html",
        username=session["username"],
        notes=notes
    )


# -------------------------------------------------
# CREATE NOTE
# -------------------------------------------------

@app.route("/create-note", methods=["GET", "POST"])
def create_note():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "user":
        return "Access denied.", 403

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        # Validate note title
        if len(title) < 1 or len(title) > 100:
            return "Invalid note title."

        # Validate note content
        if len(content) < 1 or len(content) > 2000:
            return "Invalid note content."

        with sqlite3.connect("securevault.db", timeout=10) as connection:

            connection.execute(
                """
                INSERT INTO notes
                (user_id, title, content)
                VALUES (?, ?, ?)
                """,
                (
                    session["user_id"],
                    title,
                    content
                )
            )

        return redirect(url_for("dashboard"))

    return render_template("create_note.html")


# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied.", 403

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        users = connection.execute(
            """
            SELECT
                users.id,
                users.username,
                users.role,
                users.is_active,
                COUNT(notes.id)
            FROM users

            LEFT JOIN notes
            ON users.id = notes.user_id

            GROUP BY users.id
            """
        ).fetchall()

    return render_template(
        "admin_dashboard.html",
        users=users
    )


# -------------------------------------------------
# DISABLE USER
# -------------------------------------------------

@app.route("/disable-user/<int:user_id>")
def disable_user(user_id):

    if session.get("role") != "admin":
        return "Access denied.", 403

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        connection.execute(
            """
            UPDATE users
            SET is_active = 0
            WHERE id = ?
            AND role != 'admin'
            """,
            (user_id,)
        )

    return redirect(url_for("admin_dashboard"))


# -------------------------------------------------
# NOTE DELETION
# -------------------------------------------------

@app.route("/delete-note/<int:note_id>", methods=["POST"])
def delete_note(note_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "user":
        return "Access denied.", 403

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        connection.execute(
            """
            DELETE FROM notes
            WHERE id = ?
            AND user_id = ?
            """,
            (
                note_id,
                session["user_id"]
            )
        )

    return redirect(url_for("dashboard"))


# -------------------------------------------------
# ENABLE USER
# -------------------------------------------------

@app.route("/enable-user/<int:user_id>")
def enable_user(user_id):

    if session.get("role") != "admin":
        return "Access denied.", 403

    with sqlite3.connect("securevault.db", timeout=10) as connection:

        connection.execute(
            """
            UPDATE users
            SET is_active = 1
            WHERE id = ?
            AND role != 'admin'
            """,
            (user_id,)
        )

    return redirect(url_for("admin_dashboard"))


# -------------------------------------------------
# LOGOUT
# -------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.errorhandler(403)
def forbidden(error):

    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(error):

    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):

    return render_template("500.html"), 500

# -------------------------------------------------
# START APPLICATION
# -------------------------------------------------

if __name__ == "__main__":

    create_database()
    create_admin()

app.run(debug=False)