

import os
from datetime import date, datetime

from flask import Flask, jsonify, request, render_template
import mysql.connector
from mysql.connector import pooling


app = Flask(__name__)


# ===============================================================
# DATABASE CONFIGURATION
# ===============================================================

DB_CONFIG = {
    "host": os.environ.get(
        "DB_HOST",
        "mysql-3f67b36-javidhjainul-1364.d.aivencloud.com"
    ),
    "port": int(os.environ.get("DB_PORT", 20734)),
    "user": os.environ.get("DB_USER", "avnadmin"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME", "defaultdb"),
    "ssl_ca": os.environ.get(
        "DB_SSL_CA",
        r"C:\Users\DELL\Downloads\ca.pem"
    ),
}

pool = pooling.MySQLConnectionPool(
    pool_name="shop_pool",
    pool_size=10,
    **DB_CONFIG
)


def get_conn():
    return pool.get_connection()


def dict_cursor(conn):
    return conn.cursor(dictionary=True)


def to_float(value):
    if value is None:
        return 0.0

    return float(value)


# ===============================================================
# PAGE
# ===============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ===============================================================
# DATE / MONTH FILTER
# ===============================================================

def parse_filters():
    d = request.args.get("date")
    m = request.args.get("month")

    return d, m


# ===============================================================
# SALES
# ===============================================================

@app.route("/api/sales", methods=["GET"])
def get_sales():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM sales
                WHERE sale_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM sales
                WHERE sale_date >= %s
                AND sale_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                ORDER BY sale_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM sales
                ORDER BY sale_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("sale_date"):
                row["sale_date"] = row["sale_date"].isoformat()

            row["amount"] = to_float(row.get("amount"))
            row["split_amount"] = to_float(row.get("split_amount"))
            row["total_amount"] = to_float(row.get("total_amount"))

        return jsonify(rows)

    except Exception as e:

        print("SALES GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/sales", methods=["POST"])
def add_sale():

    try:

        data = request.get_json(force=True)

        sale_date = (
            data.get("sale_date")
            or date.today().isoformat()
        )

        product_name = (
            data.get("product_name")
            or ""
        ).strip()

        amount = to_float(
            data.get("amount")
        )

        split_amount = to_float(
            data.get("split_amount")
        )

        if not product_name:

            return jsonify({
                "error": "product_name is required"
            }), 400

        total_amount = (
            amount + split_amount
        )

        conn = get_conn()
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO sales
                (
                    sale_date,
                    product_name,
                    amount,
                    split_amount,
                    total_amount
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    sale_date,
                    product_name,
                    amount,
                    split_amount,
                    total_amount
                )
            )

            conn.commit()

            return jsonify({
                "id": cur.lastrowid
            }), 201

        finally:

            cur.close()
            conn.close()

    except Exception as e:

        print("SALES POST ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/sales/<int:sale_id>", methods=["PUT"])
def update_sale(sale_id):

    data = request.get_json(force=True)

    amount = to_float(
        data.get("amount")
    )

    split_amount = to_float(
        data.get("split_amount")
    )

    total_amount = (
        amount + split_amount
    )

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    sale_date = data.get("sale_date")

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE sales
            SET
                sale_date=%s,
                product_name=%s,
                amount=%s,
                split_amount=%s,
                total_amount=%s
            WHERE id=%s
            """,
            (
                sale_date,
                product_name,
                amount,
                split_amount,
                total_amount,
                sale_id
            )
        )

        conn.commit()

        return jsonify({
            "updated": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


@app.route("/api/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM sales WHERE id=%s",
            (sale_id,)
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# EXPENSES
# ===============================================================

@app.route("/api/expenses", methods=["GET"])
def get_expenses():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM expenses
                WHERE expense_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM expenses
                WHERE expense_date >= %s
                AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                ORDER BY expense_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM expenses
                ORDER BY expense_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("expense_date"):
                row["expense_date"] = row["expense_date"].isoformat()

            row["amount"] = to_float(
                row.get("amount")
            )

        return jsonify(rows)

    except Exception as e:

        print("EXPENSE GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/expenses", methods=["POST"])
def add_expense():

    data = request.get_json(force=True)

    expense_date = (
        data.get("expense_date")
        or date.today().isoformat()
    )

    expense_name = (
        data.get("expense_name")
        or ""
    ).strip()

    amount = to_float(
        data.get("amount")
    )

    if not expense_name:

        return jsonify({
            "error": "expense_name is required"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO expenses
            (
                expense_date,
                expense_name,
                amount
            )
            VALUES (%s, %s, %s)
            """,
            (
                expense_date,
                expense_name,
                amount
            )
        )

        conn.commit()

        return jsonify({
            "id": cur.lastrowid
        }), 201

    finally:

        cur.close()
        conn.close()


@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):

    data = request.get_json(force=True)

    expense_date = data.get(
        "expense_date"
    )

    expense_name = (
        data.get("expense_name")
        or ""
    ).strip()

    amount = to_float(
        data.get("amount")
    )

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE expenses
            SET
                expense_date=%s,
                expense_name=%s,
                amount=%s
            WHERE id=%s
            """,
            (
                expense_date,
                expense_name,
                amount,
                expense_id
            )
        )

        conn.commit()

        return jsonify({
            "updated": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM expenses WHERE id=%s",
            (expense_id,)
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# PURCHASES
# ===============================================================

@app.route("/api/purchases", methods=["GET"])
def get_purchases():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM purchases
                WHERE purchase_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM purchases
                WHERE purchase_date >= %s
                AND purchase_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                ORDER BY purchase_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM purchases
                ORDER BY purchase_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("purchase_date"):
                row["purchase_date"] = row["purchase_date"].isoformat()

            row["amount"] = to_float(
                row.get("amount")
            )

        return jsonify(rows)

    except Exception as e:

        print("PURCHASE GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/purchases", methods=["POST"])
def add_purchase():

    data = request.get_json(force=True)

    purchase_date = (
        data.get("purchase_date")
        or date.today().isoformat()
    )

    dealer_name = (
        data.get("dealer_name")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    amount = to_float(
        data.get("amount")
    )

    if not dealer_name or not product_name:

        return jsonify({
            "error": "dealer_name and product_name are required"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO purchases
            (
                purchase_date,
                dealer_name,
                product_name,
                amount
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                purchase_date,
                dealer_name,
                product_name,
                amount
            )
        )

        conn.commit()

        return jsonify({
            "id": cur.lastrowid
        }), 201

    finally:

        cur.close()
        conn.close()


@app.route("/api/purchases/<int:purchase_id>", methods=["PUT"])
def update_purchase(purchase_id):

    data = request.get_json(force=True)

    purchase_date = data.get(
        "purchase_date"
    )

    dealer_name = (
        data.get("dealer_name")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    amount = to_float(
        data.get("amount")
    )

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE purchases
            SET
                purchase_date=%s,
                dealer_name=%s,
                product_name=%s,
                amount=%s
            WHERE id=%s
            """,
            (
                purchase_date,
                dealer_name,
                product_name,
                amount,
                purchase_id
            )
        )

        conn.commit()

        return jsonify({
            "updated": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


@app.route("/api/purchases/<int:purchase_id>", methods=["DELETE"])
def delete_purchase(purchase_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM purchases WHERE id=%s",
            (purchase_id,)
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# ENQUIRIES
# ===============================================================

@app.route("/api/enquiries", methods=["GET"])
def get_enquiries():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM enquiries
                WHERE enquiry_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM enquiries
                WHERE enquiry_date >= %s
                AND enquiry_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                ORDER BY enquiry_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM enquiries
                ORDER BY enquiry_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("enquiry_date"):
                row["enquiry_date"] = row["enquiry_date"].isoformat()

        return jsonify(rows)

    except Exception as e:

        print("ENQUIRY GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/enquiries", methods=["POST"])
def add_enquiry():

    data = request.get_json(force=True)

    enquiry_date = (
        data.get("enquiry_date")
        or date.today().isoformat()
    )

    customer_name = (
        data.get("customer_name")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    if not customer_name or not product_name:

        return jsonify({
            "error": "customer_name and product_name are required"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO enquiries
            (
                enquiry_date,
                customer_name,
                product_name
            )
            VALUES (%s, %s, %s)
            """,
            (
                enquiry_date,
                customer_name,
                product_name
            )
        )

        conn.commit()

        return jsonify({
            "id": cur.lastrowid
        }), 201

    finally:

        cur.close()
        conn.close()


@app.route("/api/enquiries/<int:enquiry_id>", methods=["DELETE"])
def delete_enquiry(enquiry_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM enquiries WHERE id=%s",
            (enquiry_id,)
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# REPAIRS
# ===============================================================

REPAIR_STATUSES = [
    "Received",
    "In Progress",
    "Completed",
    "Delivered to Customer"
]


@app.route("/api/repairs", methods=["GET"])
def get_repairs():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM repairs
                WHERE repair_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM repairs
                WHERE repair_date >= %s
                AND repair_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                ORDER BY repair_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM repairs
                ORDER BY repair_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("repair_date"):
                row["repair_date"] = row["repair_date"].isoformat()

        return jsonify(rows)

    except Exception as e:

        print("REPAIR GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


@app.route("/api/repairs", methods=["POST"])
def add_repair():

    data = request.get_json(force=True)

    repair_date = (
        data.get("repair_date")
        or date.today().isoformat()
    )

    customer_name = (
        data.get("customer_name")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    status = (
        data.get("status")
        or "Received"
    )

    if not customer_name or not product_name:

        return jsonify({
            "error": "customer_name and product_name are required"
        }), 400

    if status not in REPAIR_STATUSES:

        return jsonify({
            "error": "Invalid repair status"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO repairs
            (
                repair_date,
                customer_name,
                product_name,
                status
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                repair_date,
                customer_name,
                product_name,
                status
            )
        )

        conn.commit()

        return jsonify({
            "id": cur.lastrowid,
            "message": "Repair added successfully"
        }), 201

    finally:

        cur.close()
        conn.close()


@app.route("/api/repairs/<int:repair_id>", methods=["PUT"])
def update_repair(repair_id):

    data = request.get_json(force=True)

    repair_date = (
        data.get("repair_date")
        or date.today().isoformat()
    )

    customer_name = (
        data.get("customer_name")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    status = (
        data.get("status")
        or "Received"
    )

    if not customer_name or not product_name:

        return jsonify({
            "error": "customer_name and product_name are required"
        }), 400

    if status not in REPAIR_STATUSES:

        return jsonify({
            "error": "Invalid repair status"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE repairs
            SET
                repair_date=%s,
                customer_name=%s,
                product_name=%s,
                status=%s
            WHERE id=%s
            """,
            (
                repair_date,
                customer_name,
                product_name,
                status,
                repair_id
            )
        )

        conn.commit()

        return jsonify({
            "updated": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


@app.route("/api/repairs/<int:repair_id>", methods=["DELETE"])
def delete_repair(repair_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM repairs WHERE id=%s",
            (repair_id,)
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# PAYMENTS
# ===============================================================

PAYMENT_METHODS = [
    "Cash",
    "UPI",
    "Card",
    "Bank Transfer"
]


@app.route("/api/payments", methods=["GET"])
def get_payments():

    d, m = parse_filters()

    conn = get_conn()
    cur = dict_cursor(conn)

    try:

        if d:

            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_date >= %s
                AND payment_date < DATE_ADD(
                    %s,
                    INTERVAL 1 MONTH
                )
                ORDER BY payment_date DESC, id DESC
                """,
                (
                    f"{m}-01",
                    f"{m}-01"
                )
            )

        else:

            cur.execute(
                """
                SELECT *
                FROM payments
                ORDER BY payment_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("payment_date"):

                row["payment_date"] = (
                    row["payment_date"].isoformat()
                )

            row["total_amount"] = to_float(
                row.get("total_amount")
            )

            row["paid_amount"] = to_float(
                row.get("paid_amount")
            )

            row["balance_amount"] = to_float(
                row.get("balance_amount")
            )

        return jsonify(rows)

    except Exception as e:

        print(
            "PAYMENT GET ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


# ===============================================================
# ADD PAYMENT
# ===============================================================

@app.route("/api/payments", methods=["POST"])
def add_payment():

    try:

        data = request.get_json(force=True)

        payment_date = (
            data.get("payment_date")
            or date.today().isoformat()
        )

        customer_name = (
            data.get("customer_name")
            or ""
        ).strip()

        reference_name = (
            data.get("reference_name")
            or ""
        ).strip()

        total_amount = to_float(
            data.get("total_amount")
        )

        paid_amount = to_float(
            data.get("paid_amount")
        )

        payment_method = (
            data.get("payment_method")
            or "Cash"
        )

        notes = (
            data.get("notes")
            or ""
        ).strip()

        # -------------------------------------------------------
        # VALIDATION
        # -------------------------------------------------------

        if not customer_name:

            return jsonify({
                "error": "customer_name is required"
            }), 400

        if not reference_name:

            return jsonify({
                "error": "reference_name is required"
            }), 400

        if total_amount <= 0:

            return jsonify({
                "error": "total_amount must be greater than 0"
            }), 400

        if paid_amount < 0:

            return jsonify({
                "error": "paid_amount cannot be negative"
            }), 400

        if paid_amount > total_amount:

            return jsonify({
                "error": "paid_amount cannot be greater than total_amount"
            }), 400

        if payment_method not in PAYMENT_METHODS:

            return jsonify({
                "error": "Invalid payment method"
            }), 400

        # -------------------------------------------------------
        # CALCULATE BALANCE
        # -------------------------------------------------------

        balance_amount = (
            total_amount -
            paid_amount
        )

        # -------------------------------------------------------
        # DETERMINE STATUS
        # -------------------------------------------------------

        if paid_amount == 0:

            status = "Pending"

        elif paid_amount < total_amount:

            status = "Partial"

        else:

            status = "Paid"

        # -------------------------------------------------------
        # DATABASE
        # -------------------------------------------------------

        conn = get_conn()
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO payments
                (
                    payment_date,
                    customer_name,
                    reference_name,
                    total_amount,
                    paid_amount,
                    balance_amount,
                    payment_method,
                    status,
                    notes
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    payment_date,
                    customer_name,
                    reference_name,
                    total_amount,
                    paid_amount,
                    balance_amount,
                    payment_method,
                    status,
                    notes
                )
            )

            conn.commit()

            return jsonify({

                "id":
                    cur.lastrowid,

                "message":
                    "Payment added successfully"

            }), 201

        finally:

            cur.close()
            conn.close()

    except Exception as e:

        print(
            "PAYMENT POST ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500


# ===============================================================
# UPDATE PAYMENT
# ===============================================================

@app.route(
    "/api/payments/<int:payment_id>",
    methods=["PUT"]
)
def update_payment(payment_id):

    data = request.get_json(force=True)

    payment_date = (
        data.get("payment_date")
        or date.today().isoformat()
    )

    customer_name = (
        data.get("customer_name")
        or ""
    ).strip()

    reference_name = (
        data.get("reference_name")
        or ""
    ).strip()

    total_amount = to_float(
        data.get("total_amount")
    )

    paid_amount = to_float(
        data.get("paid_amount")
    )

    payment_method = (
        data.get("payment_method")
        or "Cash"
    )

    notes = (
        data.get("notes")
        or ""
    ).strip()

    if not customer_name:

        return jsonify({
            "error": "customer_name is required"
        }), 400

    if not reference_name:

        return jsonify({
            "error": "reference_name is required"
        }), 400

    if total_amount <= 0:

        return jsonify({
            "error": "total_amount must be greater than 0"
        }), 400

    if paid_amount < 0:

        return jsonify({
            "error": "paid_amount cannot be negative"
        }), 400

    if paid_amount > total_amount:

        return jsonify({
            "error": "paid_amount cannot be greater than total_amount"
        }), 400

    if payment_method not in PAYMENT_METHODS:

        return jsonify({
            "error": "Invalid payment method"
        }), 400

    balance_amount = (
        total_amount -
        paid_amount
    )

    if paid_amount == 0:

        status = "Pending"

    elif paid_amount < total_amount:

        status = "Partial"

    else:

        status = "Paid"

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE payments
            SET
                payment_date=%s,
                customer_name=%s,
                reference_name=%s,
                total_amount=%s,
                paid_amount=%s,
                balance_amount=%s,
                payment_method=%s,
                status=%s,
                notes=%s
            WHERE id=%s
            """,
            (
                payment_date,
                customer_name,
                reference_name,
                total_amount,
                paid_amount,
                balance_amount,
                payment_method,
                status,
                notes,
                payment_id
            )
        )

        conn.commit()

        return jsonify({
            "updated":
                cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# DELETE PAYMENT
# ===============================================================

@app.route(
    "/api/payments/<int:payment_id>",
    methods=["DELETE"]
)
def delete_payment(payment_id):

    conn = get_conn()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            DELETE FROM payments
            WHERE id=%s
            """,
            (payment_id,)
        )

        conn.commit()

        return jsonify({
            "deleted":
                cur.rowcount
        })

    finally:

        cur.close()
        conn.close()


# ===============================================================
# SUMMARY
# ===============================================================

@app.route("/api/summary", methods=["GET"])
def summary():

    conn = None
    cur = None

    try:

        requested_date = request.args.get("date")
        requested_month = request.args.get("month")

        # =======================================================
        # DETERMINE DATE AND MONTH
        # =======================================================

        if requested_date:

            d = requested_date
            m = requested_date[:7]

        elif requested_month:

            m = requested_month
            d = f"{requested_month}-01"

        else:

            d = date.today().isoformat()
            m = d[:7]

        print(
            "SUMMARY REQUEST:",
            "date =", d,
            "month =", m
        )

        # =======================================================
        # VALIDATE DATE / MONTH
        # =======================================================

        try:

            datetime.strptime(
                d,
                "%Y-%m-%d"
            )

            datetime.strptime(
                m,
                "%Y-%m"
            )

        except ValueError:

            return jsonify({
                "error":
                    "Invalid date or month format"
            }), 400

        # =======================================================
        # DATABASE
        # =======================================================

        conn = get_conn()

        cur = conn.cursor(
            dictionary=True
        )

        # =======================================================
        # HELPER FOR SUM VALUES
        # =======================================================

        def scalar(query, params=()):

            cur.execute(
                query,
                params
            )

            row = cur.fetchone()

            if not row:

                return 0.0

            value = next(
                iter(row.values())
            )

            return to_float(value)

        # =======================================================
        # SELECTED DAY SALES
        # =======================================================

        today_sales = scalar(
            """
            SELECT COALESCE(
                SUM(total_amount),
                0
            ) AS total
            FROM sales
            WHERE sale_date = %s
            """,
            (d,)
        )

        # =======================================================
        # SELECTED DAY EXPENSES
        # =======================================================

        today_expenses = scalar(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS total
            FROM expenses
            WHERE expense_date = %s
            """,
            (d,)
        )

        # =======================================================
        # SELECTED DAY PURCHASES
        # =======================================================

        today_purchases = scalar(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS total
            FROM purchases
            WHERE purchase_date = %s
            """,
            (d,)
        )

        # =======================================================
        # TODAY PAYMENTS RECEIVED
        # =======================================================
        #
        # This is the actual money received on the selected date.
        #
        # Example:
        #
        # Total Bill = ₹10,000
        # Paid       = ₹4,000
        # Balance    = ₹6,000
        #
        # Today's Payment Received = ₹4,000
        # =======================================================

        today_payments_received = scalar(
            """
            SELECT COALESCE(
                SUM(paid_amount),
                0
            ) AS total
            FROM payments
            WHERE payment_date = %s
            """,
            (d,)
        )

        # =======================================================
        # TODAY PAYMENT BALANCE
        # =======================================================
        #
        # This is the pending amount for payment records
        # on the selected date.
        # =======================================================

        today_payment_balance = scalar(
            """
            SELECT COALESCE(
                SUM(balance_amount),
                0
            ) AS total
            FROM payments
            WHERE payment_date = %s
            """,
            (d,)
        )

        # =======================================================
        # MONTH ENQUIRIES
        # =======================================================

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM enquiries
            WHERE enquiry_date >= %s
            AND enquiry_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        row = cur.fetchone()

        month_enquiries = int(
            row["total"] or 0
        )

        # =======================================================
        # MONTH SALES
        # =======================================================

        month_sales = scalar(
            """
            SELECT COALESCE(
                SUM(total_amount),
                0
            ) AS total
            FROM sales
            WHERE sale_date >= %s
            AND sale_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        # =======================================================
        # MONTH EXPENSES
        # =======================================================

        month_expenses = scalar(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS total
            FROM expenses
            WHERE expense_date >= %s
            AND expense_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        # =======================================================
        # MONTH PURCHASES
        # =======================================================

        month_purchases = scalar(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS total
            FROM purchases
            WHERE purchase_date >= %s
            AND purchase_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        # =======================================================
        # MONTH PAYMENTS RECEIVED
        # =======================================================

        month_payments_received = scalar(
            """
            SELECT COALESCE(
                SUM(paid_amount),
                0
            ) AS total
            FROM payments
            WHERE payment_date >= %s
            AND payment_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        # =======================================================
        # MONTH PAYMENT BALANCE
        # =======================================================

        month_payment_balance = scalar(
            """
            SELECT COALESCE(
                SUM(balance_amount),
                0
            ) AS total
            FROM payments
            WHERE payment_date >= %s
            AND payment_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
            """,
            (
                f"{m}-01",
                f"{m}-01"
            )
        )

        # =======================================================
        # ACTIVE REPAIRS
        # =======================================================

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM repairs
            WHERE status != 'Delivered to Customer'
            """
        )

        row = cur.fetchone()

        active_repairs = int(
            row["total"] or 0
        )

        # =======================================================
        # RESPONSE
        # =======================================================

        result = {

            "date":
                d,

            "month":
                m,

            # -------------------------
            # DAY
            # -------------------------

            "today_sales":
                today_sales,

            "today_expenses":
                today_expenses,

            "today_purchases":
                today_purchases,

            "today_payments_received":
                today_payments_received,

            "today_payment_balance":
                today_payment_balance,

            # -------------------------
            # MONTH
            # -------------------------

            "month_sales":
                month_sales,

            "month_expenses":
                month_expenses,

            "month_purchases":
                month_purchases,

            "month_enquiries":
                month_enquiries,

            "month_payments_received":
                month_payments_received,

            "month_payment_balance":
                month_payment_balance,

            # -------------------------
            # REPAIRS
            # -------------------------

            "active_repairs":
                active_repairs
        }

        print(
            "SUMMARY RESULT:",
            result
        )

        return jsonify(result)

    except Exception as e:

        print(
            "SUMMARY ERROR:",
            repr(e)
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# START APPLICATION
# ===============================================================

if __name__ == "__main__":

    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )

