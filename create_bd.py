import sqlite3
from datetime import datetime

DB_FILE = "goods.db"

SQL_SCRIPT = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS user_roles;

CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE suppliers (
    supplier_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    phone         TEXT,
    email         TEXT
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name  TEXT NOT NULL,
    category_id   INTEGER NOT NULL,
    supplier_id   INTEGER NOT NULL,
    price         REAL NOT NULL,
    stock_qty     INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
);

CREATE TABLE deliveries (
    delivery_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    INTEGER NOT NULL,
    delivery_date TEXT NOT NULL,
    quantity      INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_name ON products(product_name);
CREATE INDEX idx_deliveries_product ON deliveries(product_id);
CREATE INDEX idx_deliveries_date ON deliveries(delivery_date);

CREATE VIEW v_products_full AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    s.supplier_name,
    p.price,
    p.stock_qty
FROM products p
JOIN categories c ON p.category_id = c.category_id
JOIN suppliers s  ON p.supplier_id = s.supplier_id;

CREATE VIEW v_product_stock_calc AS
SELECT
    p.product_id,
    p.product_name,
    IFNULL(SUM(d.quantity), 0) AS delivered_qty
FROM products p
LEFT JOIN deliveries d ON d.product_id = p.product_id
GROUP BY p.product_id, p.product_name;

CREATE TRIGGER trg_deliveries_after_insert
AFTER INSERT ON deliveries
FOR EACH ROW
BEGIN
    UPDATE products
    SET stock_qty = stock_qty + NEW.quantity
    WHERE product_id = NEW.product_id;
END;

CREATE TRIGGER trg_deliveries_after_delete
AFTER DELETE ON deliveries
FOR EACH ROW
BEGIN
    UPDATE products
    SET stock_qty = stock_qty - OLD.quantity
    WHERE product_id = OLD.product_id;
END;

CREATE TABLE roles (
    role_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL UNIQUE
);

CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
);

-- Роли: поставщик и менеджер
INSERT INTO roles (role_name) VALUES ('supplier');
INSERT INTO roles (role_name) VALUES ('manager');

-- Пользователи
INSERT INTO users (user_name) VALUES ('user_supplier');
INSERT INTO users (user_name) VALUES ('user_manager');

-- Связи пользователь-роль
INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u, roles r
WHERE u.user_name = 'user_supplier' AND r.role_name = 'supplier';

INSERT INTO user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM users u, roles r
WHERE u.user_name = 'user_manager' AND r.role_name = 'manager';

-- Данные для теста
INSERT INTO categories (category_name) VALUES ('Бытовая техника');
INSERT INTO categories (category_name) VALUES ('Компьютеры');
INSERT INTO categories (category_name) VALUES ('Офисные товары');

INSERT INTO suppliers (supplier_name, phone, email)
VALUES ('ООО "ТехноМир"', '+7-900-000-00-01', 'info@technomir.ru');

INSERT INTO suppliers (supplier_name, phone, email)
VALUES ('ООО "КомПро"', '+7-900-000-00-02', 'sales@kompro.ru');

INSERT INTO products (product_name, category_id, supplier_id, price, stock_qty)
VALUES ('Ноутбук X', 2, 2, 55000, 0);

INSERT INTO products (product_name, category_id, supplier_id, price, stock_qty)
VALUES ('Принтер Y', 3, 1, 12000, 0);

INSERT INTO products (product_name, category_id, supplier_id, price, stock_qty)
VALUES ('Пылесос Z', 1, 1, 8000, 0);

INSERT INTO deliveries (product_id, delivery_date, quantity)
VALUES (1, '2026-02-20', 10);

INSERT INTO deliveries (product_id, delivery_date, quantity)
VALUES (2, '2026-02-21', 5);

INSERT INTO deliveries (product_id, delivery_date, quantity)
VALUES (3, '2026-02-22', 7);
"""

def init_and_backup(db_file: str = DB_FILE):
    conn = sqlite3.connect(db_file)
    try:
        conn.executescript(SQL_SCRIPT)
        conn.commit()
        print("База создана и заполнена.")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"goods_backup_{ts}.db"
        dst = sqlite3.connect(backup_name)
        with dst:
            conn.backup(dst)
        dst.close()
        print(f"Резервная копия создана: {backup_name}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_and_backup()
