from __future__ import annotations

import os
import sqlite3
import secrets
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


DB_NAME = "banco.db"


def _db_path() -> str:
    # banco.db dentro de instance/
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "instance", DB_NAME)


def init_db(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                produto TEXT NOT NULL,
                valor REAL NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
            """
        )

        cur.execute("SELECT COUNT(*) FROM admin_users")
        count = cur.fetchone()[0]
        if count == 0:
            initial_username = os.environ.get("ADMIN_INITIAL_USERNAME", "admin")
            initial_password = os.environ.get("ADMIN_INITIAL_PASSWORD") or "admin123"
            password_hash = generate_password_hash(initial_password)
            cur.execute(
                "INSERT INTO admin_users (username, senha_hash, criado_em) VALUES (?, ?, ?)",
                (initial_username, password_hash, datetime.utcnow().isoformat() + "Z"),
            )

        con.commit()


def criar_app() -> Flask:
    base_dir = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
        static_url_path="/static",
    )

    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False  # dev local (http)

    CORS(app, supports_credentials=True)

    db_path = _db_path()
    init_db(db_path)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_cliente_id_or_none() -> int | None:
        cid = session.get("cliente_id")
        try:
            return int(cid) if cid is not None else None
        except Exception:
            return None

    def _get_admin_username_or_none() -> str | None:
        u = session.get("admin_user")
        return u if u else None

    def _require_admin():
        if not _get_admin_username_or_none():
            return jsonify({"erro": "Acesso negado"}), 401
        return None

    # ── páginas GET ───────────────────────────────────────────────────────────

    @app.route("/", methods=["GET"])
    def root():
        return render_template("index.html")

    @app.route("/sobre", methods=["GET"])
    def sobre():
        return render_template("sobre.html")

    @app.route("/projeto", methods=["GET"])
    def projeto():
        return render_template("projeto.html")

    @app.route("/cadastro", methods=["GET"])
    def cadastro():
        return render_template("cadastro.html")

    @app.route("/loja", methods=["GET"])
    def loja():
        return render_template("loja.html")

    # ── ações POST ────────────────────────────────────────────────────────────

    @app.route("/cadastrar", methods=["POST"])
    def cadastrar():
        nome = (request.form.get("nome") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""

        if not nome:
            flash("Nome é obrigatório", "error")
            return redirect(url_for("cadastro"))

        if not email or "@" not in email:
            flash("E-mail inválido", "error")
            return redirect(url_for("cadastro"))

        if not senha or len(senha) < 6:
            flash("Senha deve ter no mínimo 6 caracteres", "error")
            return redirect(url_for("cadastro"))

        senha_hash = generate_password_hash(senha)

        try:
            with sqlite3.connect(db_path) as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO clientes (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                    (nome, email, senha_hash, datetime.utcnow().isoformat() + "Z"),
                )
                cliente_id = cur.lastrowid
        except sqlite3.IntegrityError:
            flash("E-mail já cadastrado", "error")
            return redirect(url_for("cadastro"))

        session["cliente_id"] = cliente_id
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("loja"))

    @app.route("/comprar", methods=["POST"])
    def comprar():
        produto = (request.form.get("produto") or "").strip()
        valor_raw = (request.form.get("valor") or "").strip()

        if not produto:
            flash("Produto inválido", "error")
            return redirect(url_for("loja"))

        try:
            valor = float(valor_raw.replace("R$", "").strip().replace(".", "").replace(",", "."))
        except Exception:
            flash("Valor inválido", "error")
            return redirect(url_for("loja"))

        cliente_id = _get_cliente_id_or_none()

        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO compras (cliente_id, produto, valor, data) VALUES (?, ?, ?, ?)",
                (cliente_id, produto, valor, datetime.utcnow().isoformat() + "Z"),
            )

        flash("Compra efetuada com sucesso!", "success")
        return redirect(url_for("loja"))

    @app.route("/login-cliente", methods=["POST"])
    def login_cliente():
        dados = request.get_json(silent=True) or {}
        email = (dados.get("email") or "").strip().lower()
        password = dados.get("password") or ""

        if not email or not password:
            return jsonify({"erro": "Informe email e senha"}), 400

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                "SELECT id, senha_hash FROM clientes WHERE email = ? LIMIT 1",
                (email,),
            )
            row = cur.fetchone()

        if not row or not check_password_hash(row["senha_hash"], password):
            return jsonify({"erro": "Credenciais inválidas"}), 401

        session["cliente_id"] = int(row["id"])
        return jsonify({"ok": True}), 200

    @app.route("/logout-cliente", methods=["GET"])
    def logout_cliente():
        session.pop("cliente_id", None)
        flash("Sessão encerrada.", "success")
        return redirect(url_for("loja"))

    @app.route("/registrar-email", methods=["POST"])
    def registrar_email():
        dados = request.get_json(silent=True) or {}
        email = (dados.get("email") or "").strip().lower()
        if not email or "@" not in email:
            return jsonify({"erro": "E-mail inválido"}), 400

        try:
            with sqlite3.connect(db_path) as con:
                cur = con.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO emails (email, criado_em) VALUES (?, ?)",
                    (email, datetime.utcnow().isoformat() + "Z"),
                )
        except Exception:
            return jsonify({"erro": "Falha ao salvar e-mail"}), 500

        return jsonify({"ok": True}), 201

    # ── admin ─────────────────────────────────────────────────────────────────

    @app.route("/admin", methods=["GET"])
    def admin():
        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT id, nome, email FROM clientes ORDER BY id DESC")
            clientes_rows = cur.fetchall()
            cur.execute(
                "SELECT id, produto, valor, data, cliente_id FROM compras ORDER BY datetime(data) DESC, id DESC"
            )
            compras_rows = cur.fetchall()

        class _O:
            def __init__(self, **kw):
                self.__dict__.update(kw)

        clientes = [_O(**dict(r)) for r in clientes_rows]
        compras = [_O(**dict(r)) for r in compras_rows]
        return render_template("admin.html", compras=compras, clientes=clientes)

    @app.post("/admin/login")
    def admin_login():
        dados = request.get_json(silent=True) or {}
        username = (dados.get("username") or "").strip()
        password = dados.get("password") or ""

        if not username or not password:
            return jsonify({"erro": "Informe username e password"}), 400

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                "SELECT id, username, senha_hash FROM admin_users WHERE username = ? LIMIT 1",
                (username,),
            )
            row = cur.fetchone()

        if not row or not check_password_hash(row["senha_hash"], password):
            return jsonify({"erro": "Credenciais inválidas"}), 401

        session["admin_user"] = row["username"]
        session["admin_logged_at"] = datetime.utcnow().isoformat() + "Z"
        return jsonify({"ok": True}), 200

    @app.post("/admin/logout")
    def admin_logout():
        session.pop("admin_user", None)
        session.pop("admin_logged_at", None)
        return jsonify({"ok": True}), 200

    @app.get("/api/admin/clientes")
    def api_admin_clientes():
        deny = _require_admin()
        if deny:
            return deny

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                """
                SELECT c.id, c.nome, c.email, COUNT(cmp.id) AS total_compras
                FROM clientes c
                LEFT JOIN compras cmp ON cmp.cliente_id = c.id
                GROUP BY c.id
                ORDER BY c.id DESC
                """
            )
            rows = cur.fetchall()

        return jsonify([
            {
                "id": int(r["id"]),
                "nome": r["nome"],
                "email": r["email"],
                "total_compras": int(r["total_compras"] or 0),
            }
            for r in rows
        ])

    @app.get("/api/admin/metrics")
    def api_admin_metrics():
        deny = _require_admin()
        if deny:
            return deny

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM clientes")
            total_clientes = cur.fetchone()["total"]
            cur.execute("SELECT COUNT(*) AS total FROM compras")
            total_compras = cur.fetchone()["total"]
            cur.execute("SELECT COALESCE(SUM(valor), 0) AS receita FROM compras")
            receita_total = cur.fetchone()["receita"]

        return jsonify({
            "total_clientes": int(total_clientes),
            "total_compras": int(total_compras),
            "receita_total": float(receita_total),
        })

    return app


if __name__ == "__main__":
    app = criar_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
