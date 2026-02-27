from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

DB_FILE = "goods.db"

app = Flask(__name__)

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_role(username: str | None):
    if not username:
        return None
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        """SELECT r.role_name
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.user_id
            JOIN roles r ON r.role_id = ur.role_id
            WHERE u.user_name = ?""",
        (username,),
    ).fetchone()
    conn.close()
    return row["role_name"] if row else None

def load_common_data():
    conn = get_conn()
    cur = conn.cursor()

    products = cur.execute(
        "SELECT * FROM v_products_full ORDER BY product_id"
    ).fetchall()

    deliveries = cur.execute(
        """SELECT d.delivery_id, p.product_name, d.delivery_date, d.quantity
            FROM deliveries d
            JOIN products p ON p.product_id = d.product_id
            ORDER BY d.delivery_date DESC, d.delivery_id DESC"""
    ).fetchall()

    all_products = cur.execute(
        "SELECT product_id, product_name FROM products ORDER BY product_name"
    ).fetchall()

    plan = cur.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM v_products_full"
    ).fetchall()

    conn.close()
    return products, deliveries, all_products, plan

@app.route("/")
def index():
    return redirect(url_for("manager_page"))

@app.route("/manager")
def manager_page():
    if not Path(DB_FILE).exists():
        return "База данных не найдена. Сначала запусти init_all.py"

    current_user = "user_manager"
    role = get_user_role(current_user)

    products, deliveries, all_products, plan = load_common_data()

    return render_template(
        "manager.html",
        products=products,
        deliveries=deliveries,
        plan=plan,
        current_user=current_user,
        role=role,
    )

@app.route("/supplier")
def supplier_page():
    if not Path(DB_FILE).exists():
        return "База данных не найдена. Сначала запусти init_all.py"

    current_user = "user_supplier"
    role = get_user_role(current_user)

    products, deliveries, all_products, plan = load_common_data()

    return render_template(
        "supplier.html",
        products=products,
        deliveries=deliveries,
        all_products=all_products,
        plan=plan,
        current_user=current_user,
        role=role,
    )

@app.route("/add_delivery", methods=["POST"])
def add_delivery():
    current_user = "user_supplier"
    role = get_user_role(current_user)

    if role != "supplier":
        return "Доступ запрещен: только поставщик может добавлять поставки", 403

    product_id = request.form.get("product_id")
    delivery_date = request.form.get("delivery_date")
    quantity = request.form.get("quantity")

    if not (product_id and delivery_date and quantity):
        return redirect(url_for("supplier_page"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO deliveries (product_id, delivery_date, quantity) VALUES (?, ?, ?)",
        (product_id, delivery_date, quantity),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("supplier_page"))

if __name__ == "__main__":
    app.run(debug=True)
