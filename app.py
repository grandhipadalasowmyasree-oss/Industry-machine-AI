from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime


app = Flask(__name__)

app.secret_key = "industrial_assistant_secret_key"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect("conversations.db")

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Check existing columns
    cursor.execute("PRAGMA table_info(users)")

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]

    # Add email column if old database doesn't have it
    if "email" not in columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN email TEXT
        """)

    # =====================================================
    # CONVERSATIONS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print("Database initialized successfully.")


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_database()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        ).strip()

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not email:

            error = "Please enter your email."

            return render_template(
                "login.html",
                error=error
            )

        if not password:

            error = "Please enter your password."

            return render_template(
                "login.html",
                error=error
            )

        # ---------------------------------------------
        # FIND USER
        # ---------------------------------------------

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                username,
                email,
                password,
                role
            FROM users
            WHERE LOWER(email) = ?
        """, (email,))

        user = cursor.fetchone()

        conn.close()

        # ---------------------------------------------
        # CHECK PASSWORD
        # ---------------------------------------------

        if user and user["password"] == password:

            session.clear()

            session["username"] = user["username"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            print(
                "LOGIN SUCCESS:",
                user["username"],
                user["email"],
                user["role"]
            )

            return redirect(
                url_for("chatbot")
            )

        error = "Invalid email or password."

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# CREATE ACCOUNT
# =========================================================

@app.route(
    "/create-account",
    methods=["GET", "POST"]
)
def create_account():

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        # =================================================
        # VALIDATION
        # =================================================

        if not username:

            error = "Please enter your username."

        elif not email:

            error = "Please enter your email."

        elif not password:

            error = "Please create a password."

        elif not confirm_password:

            error = "Please confirm your password."

        elif password != confirm_password:

            error = "Passwords do not match."

        elif len(password) < 6:

            error = (
                "Password must contain at least 6 characters."
            )

        else:

            conn = get_db_connection()
            cursor = conn.cursor()

            # ---------------------------------------------
            # CHECK USERNAME
            # ---------------------------------------------

            cursor.execute("""
                SELECT id
                FROM users
                WHERE LOWER(username) = ?
            """, (
                username.lower(),
            ))

            existing_username = cursor.fetchone()

            if existing_username:

                error = (
                    "Username already exists. "
                    "Please choose another username."
                )

                conn.close()

            else:

                # -----------------------------------------
                # CHECK EMAIL
                # -----------------------------------------

                cursor.execute("""
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = ?
                """, (
                    email,
                ))

                existing_email = cursor.fetchone()

                if existing_email:

                    error = (
                        "An account with this email "
                        "already exists."
                    )

                    conn.close()

                else:

                    # -------------------------------------
                    # CREATE ACCOUNT
                    # -------------------------------------

                    try:

                        cursor.execute("""
                            INSERT INTO users
                            (
                                username,
                                email,
                                password,
                                role
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            username,
                            email,
                            password,
                            "User"
                        ))

                        conn.commit()
                        conn.close()

                        print(
                            "ACCOUNT CREATED:",
                            username,
                            email
                        )

                        return redirect(
                            url_for("login")
                        )

                    except sqlite3.IntegrityError as e:

                        conn.close()

                        print(
                            "REGISTRATION ERROR:",
                            e
                        )

                        error = (
                            "Username or email already exists."
                        )

    return render_template(
        "register.html",
        error=error
    )


# =========================================================
# CHATBOT PAGE
# =========================================================

@app.route("/chatbot")
def chatbot():

    # Login protection
    if "username" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",

        username=session.get(
            "username",
            ""
        ),

        email=session.get(
            "email",
            ""
        ),

        role=session.get(
            "role",
            ""
        )
    )


# =========================================================
# CHATBOT API
# =========================================================

@app.route("/chat", methods=["POST"])
@app.route("/ask", methods=["POST"])
def ask():

    # =====================================================
    # LOGIN PROTECTION
    # =====================================================

    if "username" not in session:

        return jsonify({
            "error": "Please login first."
        }), 401

    # =====================================================
    # GET JSON
    # =====================================================

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "answer": "Please enter a question."
        })

    question = data.get(
        "message",
        ""
    ).strip()

    if not question:

        return jsonify({
            "answer": "Please enter a question."
        })

    try:

        print("\n=================================")
        print("USER:", session["username"])
        print("QUESTION:", question)
        print("=================================")

        # =================================================
        # LOAD RAG ONLY WHEN NEEDED
        # =================================================

        from rag.chat import (
            retrieve_documents,
            generate_answer
        )

        # =================================================
        # RETRIEVE MACHINE DATA / RAG DATA
        # =================================================

        documents, sources = retrieve_documents(
            question
        )

        print(
            "DOCUMENTS RETRIEVED:",
            len(documents)
        )

        # =================================================
        # GENERATE AI ANSWER
        # =================================================

        answer = generate_answer(
            question,
            documents,
            sources
        )

        print(
            "ANSWER GENERATED SUCCESSFULLY"
        )

        # =================================================
        # SAVE CONVERSATION
        # =================================================

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO conversations
            (
                username,
                user_message,
                bot_response,
                timestamp
            )
            VALUES (?, ?, ?, ?)
        """, (
            session["username"],
            question,
            answer,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conversation_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # =================================================
        # SEND RESPONSE
        # =================================================

        return jsonify({
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id
        })

    except Exception as e:

        print("\n=================================")
        print("CHATBOT ERROR:", e)
        print("=================================\n")

        return jsonify({
            "answer":
                "Sorry, I couldn't process your question."
        }), 500


# =========================================================
# RECENT CONVERSATIONS
# =========================================================

@app.route("/conversations")
def conversations():

    # Login protection
    if "username" not in session:

        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            user_message,
            bot_response,
            timestamp
        FROM conversations
        WHERE username = ?
        ORDER BY id DESC
    """, (
        session["username"],
    ))

    rows = cursor.fetchall()

    conn.close()

    conversation_list = []

    for row in rows:

        conversation_list.append({

            "id": row["id"],

            "user_message":
                row["user_message"],

            "bot_response":
                row["bot_response"],

            "timestamp":
                row["timestamp"]

        })

    return jsonify(
        conversation_list
    )


# =========================================================
# DELETE CONVERSATION
# =========================================================

@app.route(
    "/conversations/<int:conversation_id>",
    methods=["DELETE"]
)
def delete_conversation(conversation_id):

    # =====================================================
    # LOGIN PROTECTION
    # =====================================================

    if "username" not in session:

        return jsonify({
            "message": "Please login first."
        }), 401

    username = session["username"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================================
    # CHECK CONVERSATION
    # =====================================================

    cursor.execute("""
        SELECT
            id,
            username
        FROM conversations
        WHERE id = ?
    """, (
        conversation_id,
    ))

    conversation = cursor.fetchone()

    # Conversation doesn't exist
    if not conversation:

        conn.close()

        print(
            "DELETE FAILED: Conversation does not exist:",
            conversation_id
        )

        return jsonify({
            "message":
                "Conversation does not exist."
        }), 404

    # =====================================================
    # SECURITY CHECK
    # =====================================================

    if conversation["username"] != username:

        conn.close()

        print(
            "DELETE BLOCKED:",
            username,
            "tried to delete conversation",
            conversation_id
        )

        return jsonify({
            "message":
                "You cannot delete this conversation."
        }), 403

    # =====================================================
    # DELETE
    # =====================================================

    cursor.execute("""
        DELETE FROM conversations
        WHERE id = ?
        AND username = ?
    """, (
        conversation_id,
        username
    ))

    conn.commit()

    deleted_rows = cursor.rowcount

    conn.close()

    # =====================================================
    # RESULT
    # =====================================================

    if deleted_rows == 0:

        return jsonify({
            "message":
                "Conversation could not be deleted."
        }), 404

    print(
        "CONVERSATION DELETED:",
        conversation_id,
        "BY:",
        username
    )

    return jsonify({
        "message":
            "Conversation deleted successfully."
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )