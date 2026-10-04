

import os
import io
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
import traceback

from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    redirect,
    url_for,
    session,
    send_file
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

IST = timezone(timedelta(hours=5, minutes=30))


# ===============================================================
# DATABASE CONFIGURATION
# ===============================================================

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "root123"),
    "database": os.environ.get("DB_NAME", "mobile_shop"),
}

pool = pooling.MySQLConnectionPool(
    pool_name="shop_pool",
    pool_size=20,
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
# AUTHENTICATION
# ===============================================================


@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "GET":

        if session.get("logged_in"):
            return redirect(url_for("index"))

        return render_template("signin.html")


    username = (
        request.form.get("username")
        or ""
    ).strip()

    password = (
        request.form.get("password")
        or ""
    )


    if not username or not password:

        return render_template(
            "signin.html",
            error="Username and password are required."
        )


    conn = None
    cur = None

    try:

        conn = get_conn()

        cur = conn.cursor(
            dictionary=True
        )

        cur.execute(
            """
            SELECT
                id,
                username,
                password_hash
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        user = cur.fetchone()


        if not user:

            return render_template(
                "signin.html",
                error="Invalid username or password."
            )


        if not check_password_hash(
            user["password_hash"],
            password
        ):

            return render_template(
                "signin.html",
                error="Invalid username or password."
            )


        session.clear()

        session["logged_in"] = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]


        return redirect(
            url_for("index")
        )


    except Exception as e:

        print(
            "SIGNIN ERROR:",
            e
        )

        return render_template(
            "signin.html",
            error="Unable to sign in right now."
        ), 500


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# SIGN UP
# ===============================================================


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "GET":

        if session.get("logged_in"):
            return redirect(url_for("index"))

        return render_template("signup.html")


    username = (
        request.form.get("username")
        or ""
    ).strip()

    password = (
        request.form.get("password")
        or ""
    )

    confirm_password = (
        request.form.get("confirm_password")
        or ""
    )


    if not username:

        return render_template(
            "signup.html",
            error="Username is required."
        )


    if len(username) < 3:

        return render_template(
            "signup.html",
            error="Username must contain at least 3 characters."
        )


    if len(password) < 6:

        return render_template(
            "signup.html",
            error="Password must contain at least 6 characters."
        )


    if password != confirm_password:

        return render_template(
            "signup.html",
            error="Passwords do not match."
        )


    conn = None
    cur = None

    try:

        conn = get_conn()

        cur = conn.cursor(
            dictionary=True
        )


        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        existing_user = cur.fetchone()


        if existing_user:

            return render_template(
                "signup.html",
                error="Username already exists."
            )


        password_hash = generate_password_hash(
            password
        )


        cur.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                username,
                password_hash
            )
        )


        conn.commit()


        return redirect(
            url_for(
                "signin",
                registered="1"
            )
        )


    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "SIGNUP ERROR:",
            e
        )

        return render_template(
            "signup.html",
            error="Unable to create account."
        ), 500


    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# SIGN OUT
# ===============================================================


@app.route(
    "/signout",
    methods=["POST"]
)
def signout():

    session.clear()

    return redirect(
        url_for("signin")
    )


# ===============================================================
# AUTHENTICATION PROTECTION
# ===============================================================


@app.before_request
def require_login():

    

    public_paths = (
        "/signin",
        "/signup",
        "/static/"
    )


    if (
        request.path == "/signin"
        or request.path == "/signup"
        or request.path.startswith("/static/")
    ):

        return None


    if session.get("logged_in"):

        return None


    if request.path.startswith("/api/"):

        return jsonify({
            "error": "Authentication required"
        }), 401


    return redirect(
        url_for("signin")
    )



# ===============================================================
# DATABASE BACKUP
# ===============================================================


def _sql_identifier(value):
    """Safely quote a MySQL identifier such as a table name."""
    return "`" + str(value).replace("`", "``") + "`"


def _sql_value(value):
    """Convert a MySQL value into a SQL literal."""

    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float, Decimal)):
        return str(value)

    if isinstance(value, datetime):
        return "'" + value.isoformat(sep=" ") + "'"

    if isinstance(value, date):
        return "'" + value.isoformat() + "'"

    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"

    text = str(value)
    text = (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\x00", "\\0")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\x1a", "\\Z")
    )
    return "'" + text + "'"


def create_database_backup():
    """
    Create a complete SQL backup of the configured MySQL database.

    This uses the MySQL connection already used by Shop Ledger instead
    of relying on the external mysqldump command. That makes the same
    backup endpoint usable for local MySQL and, later, Aiven MySQL.
    """

    database_name = DB_CONFIG["database"]
    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SHOW TABLES")
        table_rows = cur.fetchall()
        tables = [row[0] for row in table_rows]

        lines = [
            "-- Shop Ledger Database Backup",
            "-- Database: " + str(database_name),
            "-- Created: " + datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "",
            "SET FOREIGN_KEY_CHECKS=0;",
            "SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';",
            "",
            "CREATE DATABASE IF NOT EXISTS " + _sql_identifier(database_name) + ";",
            "USE " + _sql_identifier(database_name) + ";",
            "",
        ]

        for table_name in tables:
            quoted_table = _sql_identifier(table_name)

            cur.execute("SHOW CREATE TABLE " + quoted_table)
            create_row = cur.fetchone()
            create_sql = create_row[1]

            lines.append("-- --------------------------------------------------")
            lines.append("-- Table: " + table_name)
            lines.append("-- --------------------------------------------------")
            lines.append("DROP TABLE IF EXISTS " + quoted_table + ";")
            lines.append(create_sql + ";")
            lines.append("")

            cur.execute("SELECT * FROM " + quoted_table)
            rows = cur.fetchall()

            if rows:
                column_count = len(rows[0])
                columns = [
                    _sql_identifier(desc[0])
                    for desc in cur.description
                ]
                column_sql = ", ".join(columns)

                for start in range(0, len(rows), 500):
                    batch = rows[start:start + 500]
                    values_sql = []

                    for row in batch:
                        values_sql.append(
                            "(" + ", ".join(
                                _sql_value(value) for value in row
                            ) + ")"
                        )

                    lines.append(
                        "INSERT INTO " + quoted_table +
                        " (" + column_sql + ") VALUES\n" +
                        ",\n".join(values_sql) + ";"
                    )

                    lines.append("")

        lines.extend([
            "SET FOREIGN_KEY_CHECKS=1;",
            "",
            "-- End of Shop Ledger backup",
        ])

        return "\n".join(lines)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/database-backup", methods=["GET"])
def database_backup():
    """Create and download a Shop Ledger SQL backup."""

    try:
        sql_text = create_database_backup()

        backup_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "backup"
        )
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now(IST).strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"shop_ledger_backup_{timestamp}.sql"
        backup_path = os.path.join(backup_dir, filename)

        with open(backup_path, "w", encoding="utf-8", newline="\n") as backup_file:
            backup_file.write(sql_text)

        return send_file(
            io.BytesIO(sql_text.encode("utf-8")),
            mimetype="application/sql",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print("DATABASE BACKUP ERROR:", e)
        traceback.print_exc()

        return jsonify({
            "error": "Unable to create database backup.",
            "details": str(e)
        }), 500



# ===============================================================
# USER MANAGEMENT
# ===============================================================

@app.route("/api/users", methods=["GET"])
def get_users():

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT
                id,
                username,
                created_at
            FROM users
            ORDER BY id DESC
            """
        )

        rows = cur.fetchall()

        for row in rows:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()

        return jsonify(rows)

    except Exception as e:
        print("GET USERS ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# CREATE USER
# ---------------------------------------------------------------

@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json(force=True)

    username = (
        data.get("username")
        or ""
    ).strip()

    password = (
        data.get("password")
        or ""
    )

    confirm_password = (
        data.get("confirm_password")
        or ""
    )

    if not username:
        return jsonify({
            "error": "Username is required."
        }), 400

    if len(username) < 3:
        return jsonify({
            "error": "Username must contain at least 3 characters."
        }), 400

    if not password:
        return jsonify({
            "error": "Password is required."
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must contain at least 6 characters."
        }), 400

    if password != confirm_password:
        return jsonify({
            "error": "Passwords do not match."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        existing_user = cur.fetchone()

        if existing_user:
            return jsonify({
                "error": "Username already exists."
            }), 409

        password_hash = generate_password_hash(password)

        cur.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                username,
                password_hash
            )
        )

        user_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "id": user_id,
            "username": username,
            "message": "User created successfully."
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("CREATE USER ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# UPDATE USER
# ---------------------------------------------------------------

@app.route(
    "/api/users/<int:user_id>",
    methods=["PUT"]
)
def update_user(user_id):

    data = request.get_json(force=True)

    username = (
        data.get("username")
        or ""
    ).strip()

    password = (
        data.get("password")
        or ""
    )

    confirm_password = (
        data.get("confirm_password")
        or ""
    )

    if not username:
        return jsonify({
            "error": "Username is required."
        }), 400

    if len(username) < 3:
        return jsonify({
            "error": "Username must contain at least 3 characters."
        }), 400

    if password and len(password) < 6:
        return jsonify({
            "error": "Password must contain at least 6 characters."
        }), 400

    if password != confirm_password:
        return jsonify({
            "error": "Passwords do not match."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cur.fetchone()

        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            AND id <> %s
            LIMIT 1
            """,
            (
                username,
                user_id
            )
        )

        duplicate = cur.fetchone()

        if duplicate:
            return jsonify({
                "error": "Username already exists."
            }), 409

        if password:
            password_hash = generate_password_hash(password)

            cur.execute(
                """
                UPDATE users
                SET
                    username = %s,
                    password_hash = %s
                WHERE id = %s
                """,
                (
                    username,
                    password_hash,
                    user_id
                )
            )
        else:
            cur.execute(
                """
                UPDATE users
                SET username = %s
                WHERE id = %s
                """,
                (
                    username,
                    user_id
                )
            )

        conn.commit()

        if session.get("user_id") == user_id:
            session["username"] = username

        return jsonify({
            "message": "User updated successfully."
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("UPDATE USER ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# DELETE USER
# ---------------------------------------------------------------

@app.route(
    "/api/users/<int:user_id>",
    methods=["DELETE"]
)
def delete_user(user_id):

    if session.get("user_id") == user_id:
        return jsonify({
            "error": "You cannot delete the currently logged-in user."
        }), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            DELETE FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        deleted = cur.rowcount

        conn.commit()

        if deleted == 0:
            return jsonify({
                "error": "User not found."
            }), 404

        return jsonify({
            "deleted": deleted,
            "message": "User deleted successfully."
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("DELETE USER ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()



# ===============================================================
# CUSTOMER LEDGER
# ===============================================================

@app.route("/api/customer-ledger", methods=["GET"])
def get_customer_ledger():
    """
    Return one customer's complete ledger.

    IMPORTANT:
    - Product sales come from sales table.
    - Credit sales come from payments table when there is no
      corresponding sales row.
    - Repair charge comes from repairs.amount only after the repair
      is Delivered to Customer.
    - repairs.advance is the cumulative total amount received for
      that repair.
    - Repair rows in sales are excluded from this ledger so the
      repair is not counted twice.
    - Before delivery, a repair advance is NOT shown in the ledger.
    """

    search = str(request.args.get("q") or "").strip()

    if not search:
        return jsonify({
            "error": "Enter customer name or mobile number"
        }), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        like = f"%{search}%"

        cur.execute("""
            SELECT *
            FROM (
                
                /* =====================================================
                   1. SALES
                   ===================================================== */

                SELECT
                    s.sale_date AS transaction_date,

                    CASE
                        WHEN s.sale_type = 'Repair'
                        THEN 'Repair'
                        ELSE 'Sale'
                    END AS transaction_type,

                    s.product_name AS description,

                    CASE
                        /* A payment-linked sale already has its charge
                           represented by the Payment record. */
                        WHEN s.payment_id IS NOT NULL
                        THEN COALESCE(
                            p.total_amount,
                            s.total_amount,
                            0
                        )
                        ELSE COALESCE(
                            s.total_amount,
                            0
                        )
                    END AS debit_amount,

                    /* Full payment = money received immediately.
                       For a payment-linked sale, use the Payment record's
                       paid amount as the credit so the outstanding becomes 0.
                       For a normal direct/full sale without payment_id,
                       the sale itself is fully paid. */
                    CASE
                        WHEN s.payment_id IS NOT NULL
                        THEN COALESCE(p.paid_amount, 0)
                        ELSE COALESCE(s.total_amount, 0)
                    END AS credit_amount,

                    COALESCE(
                        s.customer_name,
                        p.customer_name,
                        ''
                    ) AS customer_name,

                    COALESCE(
                        s.customer_number,
                        p.customer_number,
                        ''
                    ) AS customer_number,

                    s.id AS sort_id

                FROM sales s

                LEFT JOIN payments p
                    ON p.id = s.payment_id

                WHERE s.sale_type <> 'Credit Payment'
                  AND s.sale_type <> 'Repair'

                  AND (
                      COALESCE(
                          s.customer_name,
                          p.customer_name,
                          ''
                      ) LIKE %s

                      OR

                      COALESCE(
                          s.customer_number,
                          p.customer_number,
                          ''
                      ) LIKE %s
                  )


                UNION ALL


                /* =====================================================
                   2. PAYMENTS / CREDIT SALES
                   ===================================================== */

                SELECT

                    p.payment_date AS transaction_date,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM sales ps
                            WHERE ps.payment_id = p.id
                              AND ps.sale_type <> 'Credit Payment'
                        )
                        THEN 'Payment'

                        ELSE 'Credit Sale'
                    END AS transaction_type,

                    COALESCE(
                        NULLIF(
                            p.reference_name,
                            ''
                        ),
                        'Payment received'
                    ) AS description,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM sales ps
                            WHERE ps.payment_id = p.id
                              AND ps.sale_type <> 'Credit Payment'
                        )
                        THEN 0

                        ELSE COALESCE(
                            p.total_amount,
                            0
                        )
                    END AS debit_amount,

                    /* If the payment is already linked to a Sales row,
                       its paid amount was already used as the credit in
                       the Sales part above. Do not count it twice. */
                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM sales ps
                            WHERE ps.payment_id = p.id
                              AND ps.sale_type <> 'Credit Payment'
                        )
                        THEN 0
                        ELSE COALESCE(
                            p.paid_amount,
                            0
                        )
                    END AS credit_amount,

                    p.customer_name,

                    COALESCE(
                        p.customer_number,
                        ''
                    ) AS customer_number,

                    p.id AS sort_id

                FROM payments p

                WHERE
                    p.customer_name LIKE %s

                    OR

                    COALESCE(
                        p.customer_number,
                        ''
                    ) LIKE %s


                UNION ALL


                /* =====================================================
                   3. DELIVERED REPAIR
                   ===================================================== */

                SELECT

                    /* One repair = one customer charge.
                       The advance entered when the phone is received
                       is NOT shown before delivery.

                       Example:
                       Repair amount = ₹2,000
                       Advance      = ₹1,000
                       Balance paid at delivery = ₹1,000

                       After delivery:
                       Debit  = ₹2,000
                       Credit = ₹2,000
                       Outstanding = ₹0

                       The Repair row in SALES is excluded above, so
                       this repair is not counted twice.
                    */

                    COALESCE(
                        r.delivery_date,
                        DATE(r.delivered_at),
                        r.repair_date
                    ) AS transaction_date,

                    'Repair' AS transaction_type,

                    CONCAT(
                        'Repair - ',
                        r.product_name,

                        CASE
                            WHEN COALESCE(
                                r.model,
                                ''
                            ) <> ''

                            THEN CONCAT(
                                ' ',
                                r.model
                            )

                            ELSE ''
                        END
                    ) AS description,

                    COALESCE(
                        r.amount,
                        0
                    ) AS debit_amount,

                    COALESCE(
                        r.advance,
                        0
                    ) AS credit_amount,

                    r.customer_name,

                    COALESCE(
                        r.customer_number,
                        ''
                    ) AS customer_number,

                    r.id AS sort_id

                FROM repairs r

                WHERE r.status = 'Delivered to Customer'

                  AND (
                      r.customer_name LIKE %s

                      OR

                      COALESCE(
                          r.customer_number,
                          ''
                      ) LIKE %s
                  )

            ) ledger

            ORDER BY
                transaction_date ASC,
                sort_id ASC

        """, (
            like,
            like,

            like,
            like,

            like,
            like
        ))

        rows = cur.fetchall()

        balance = 0.0
        total_debit = 0.0
        total_credit = 0.0

        for row in rows:

            # ---------------------------------------------------------
            # DATE
            # ---------------------------------------------------------

            if row.get("transaction_date"):
                row["transaction_date"] = (
                    row["transaction_date"].isoformat()
                )

            # ---------------------------------------------------------
            # AMOUNTS
            # ---------------------------------------------------------

            row["debit_amount"] = to_float(
                row.get("debit_amount")
            )

            row["credit_amount"] = to_float(
                row.get("credit_amount")
            )

            # ---------------------------------------------------------
            # TOTALS
            # ---------------------------------------------------------

            total_debit += row["debit_amount"]

            total_credit += row["credit_amount"]

            # ---------------------------------------------------------
            # RUNNING BALANCE
            # ---------------------------------------------------------

            balance += (
                row["debit_amount"]
                -
                row["credit_amount"]
            )

            row["running_balance"] = round(
                balance,
                2
            )

        # -------------------------------------------------------------
        # CUSTOMER DETAILS
        # -------------------------------------------------------------

        customer_name = ""
        customer_number = ""

        for row in rows:

            if row.get("customer_name"):
                customer_name = row["customer_name"]

            if row.get("customer_number"):
                customer_number = row["customer_number"]

            if customer_name and customer_number:
                break

        # -------------------------------------------------------------
        # RESPONSE
        # -------------------------------------------------------------

        return jsonify({

            "customer_name":
                customer_name or search,

            "customer_number":
                customer_number,

            "total_debit":
                round(
                    total_debit,
                    2
                ),

            "total_credit":
                round(
                    total_credit,
                    2
                ),

            "outstanding":
                round(
                    balance,
                    2
                ),

            "transactions":
                rows
        })

    except Exception as e:

        print(
            "CUSTOMER LEDGER ERROR:",
            e
        )

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

# ===============================================================
# CUSTOMER NUMBER LOOKUP
# ===============================================================

@app.route("/api/customer-by-number", methods=["GET"])
def customer_by_number():
    """Find an existing customer name using the mobile number."""
    customer_number = str(
        request.args.get("number") or ""
    ).strip()

    if not customer_number:
        return jsonify({
            "exists": False,
            "customer_name": "",
            "customer_number": ""
        })

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        # Prefer the most recent known customer name for this number.
        cur.execute("""
            SELECT customer_name, customer_number
            FROM (
                SELECT
                    customer_name,
                    customer_number,
                    sale_date AS transaction_date,
                    id AS sort_id
                FROM sales
                WHERE customer_number = %s
                  AND customer_name IS NOT NULL
                  AND TRIM(customer_name) <> ''

                UNION ALL

                SELECT
                    customer_name,
                    customer_number,
                    payment_date AS transaction_date,
                    id AS sort_id
                FROM payments
                WHERE customer_number = %s
                  AND customer_name IS NOT NULL
                  AND TRIM(customer_name) <> ''

                UNION ALL

                SELECT
                    customer_name,
                    customer_number,
                    repair_date AS transaction_date,
                    id AS sort_id
                FROM repairs
                WHERE customer_number = %s
                  AND customer_name IS NOT NULL
                  AND TRIM(customer_name) <> ''
            ) customer_history
            ORDER BY transaction_date DESC, sort_id DESC
            LIMIT 1
        """, (
            customer_number,
            customer_number,
            customer_number
        ))

        row = cur.fetchone()

        if not row:
            return jsonify({
                "exists": False,
                "customer_name": "",
                "customer_number": customer_number
            })

        return jsonify({
            "exists": True,
            "customer_name": row.get("customer_name") or "",
            "customer_number": row.get("customer_number") or customer_number
        })

    except Exception as e:
        print("CUSTOMER NUMBER LOOKUP ERROR:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ===============================================================
# PAGE
# ===============================================================

@app.route("/")
def index():

    if not session.get("logged_in"):

        return redirect(
            url_for("signin")
        )

    return render_template(
        "index.html"
    )


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

# ===============================================================
# SALES
# ===============================================================

@app.route("/api/sales", methods=["GET"])
def get_sales():

    conn = None
    cur = None

    try:
        sale_date, month = parse_filters()

        conn = get_conn()
        cur = dict_cursor(conn)

        query = """
            SELECT
                s.id,
                s.sale_date,
                s.customer_name,
                s.customer_number,
                s.product_name,
                s.quantity,
                s.amount,
                s.split_amount,
                s.total_amount,
                s.sale_type,
                s.operator,
                s.recharge_mobile,
                s.recharge_id,
                s.repair_id,
                s.payment_id,
                CASE
                    WHEN s.sale_type = 'Repair'
                         AND s.repair_id IS NOT NULL
                    THEN GREATEST(
                        COALESCE(r.amount, 0)
                        - COALESCE(r.advance, 0),
                        0
                    )
                    ELSE 0
                END AS repair_balance
            FROM sales s
            LEFT JOIN repairs r
                ON r.id = s.repair_id
        """

        params = []
        conditions = []

        if sale_date:
            conditions.append("sale_date = %s")
            params.append(sale_date)

        elif month:
            conditions.append("DATE_FORMAT(sale_date, '%Y-%m') = %s")
            params.append(month)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC"

        cur.execute(query, params)

        rows = cur.fetchall()

        for row in rows:
            if row.get("sale_date"):
                row["sale_date"] = row["sale_date"].isoformat()

            row["quantity"] = int(row["quantity"] or 0)
            row["amount"] = to_float(row["amount"])
            row["split_amount"] = to_float(row["split_amount"])
            row["total_amount"] = to_float(row["total_amount"])

            row["sale_type"] = row.get("sale_type") or "Product"
            row["operator"] = row.get("operator") or ""
            row["recharge_mobile"] = row.get("recharge_mobile") or ""
            row["recharge_id"] = row.get("recharge_id")
            row["repair_id"] = row.get("repair_id")
            row["payment_id"] = row.get("payment_id")
            row["repair_balance"] = to_float(
                row.get("repair_balance")
            )

        return jsonify(rows)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# ADD SALE
# ---------------------------------------------------------------

@app.route("/api/sales", methods=["POST"])
def add_sale():

    data = request.get_json() or {}

    sale_date = data.get("sale_date") or date.today().isoformat()
    product_name = str(data.get("product_name") or "").strip()
    customer_name = str(data.get("customer_name") or "").strip()
    customer_number = str(data.get("customer_number") or "").strip()
    payment_type = str(data.get("payment_type") or "Full Payment").strip()

    try:
        quantity = int(data.get("quantity") or 0)
        amount = to_float(data.get("amount"))
        split_amount = to_float(data.get("split_amount"))
        paid_amount = to_float(data.get("paid_amount"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid quantity or amount"}), 400

    total_amount = round(amount + split_amount, 2)
    allow_negative_stock = data.get("allow_negative_stock") is True

    if payment_type not in ("Full Payment", "Partial Payment", "Credit"):
        return jsonify({"error": "Invalid payment type"}), 400

    payment_method = data.get("payment_method") or "Cash"
    if payment_type in ("Credit", "Partial Payment") and payment_method not in PAYMENT_METHODS:
        return jsonify({"error": "Invalid payment method"}), 400

    if not product_name:
        return jsonify({"error": "Product name is required"}), 400
    if quantity <= 0:
        return jsonify({"error": "Quantity must be greater than 0"}), 400
    if total_amount <= 0:
        return jsonify({"error": "Total amount must be greater than 0"}), 400
    if paid_amount < 0 or paid_amount > total_amount:
        return jsonify({"error": "Paid amount must be between 0 and total amount"}), 400

    if payment_type == "Full Payment":
        paid_amount = total_amount
    elif payment_type == "Credit":
        paid_amount = 0
    elif payment_type == "Partial Payment":
        if paid_amount <= 0 or paid_amount >= total_amount:
            return jsonify({"error": "For Partial Payment, paid amount must be less than the total amount"}), 400

    if payment_type in ("Credit", "Partial Payment") and not customer_name:
        return jsonify({"error": "Customer name is required for credit or partial payment"}), 400

    balance_amount = round(total_amount - paid_amount, 2)
    status = "Paid" if balance_amount == 0 else ("Partial" if paid_amount > 0 else "Pending")

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # Lock inventory. The item leaves stock even when payment is credit/partial.
        cur.execute("""
            SELECT id, product_name, quantity
            FROM inventory
            WHERE product_name = %s
            ORDER BY id
            LIMIT 1
            FOR UPDATE
        """, (product_name,))
        inventory = cur.fetchone()

        if inventory:
            current_stock = int(inventory["quantity"] or 0)
            if current_stock < quantity and not allow_negative_stock:
                conn.rollback()
                return jsonify({
                    "error": (
                        f"Insufficient stock for '{product_name}'. "
                        f"Available: {current_stock}, Required: {quantity}. "
                        "Enable 'Allow Negative Stock' to continue."
                    )
                }), 400

        payment_id = None
        sale_id = None

        # Credit/partial creates one Payment Tracking record automatically.
        if payment_type in ("Credit", "Partial Payment"):
            cur.execute("""
                INSERT INTO payments
                (
                    payment_date,
                    customer_name,
                    customer_number,
                    reference_name,
                    total_amount,
                    paid_amount,
                    balance_amount,
                    payment_method,
                    status,
                    notes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                sale_date,
                customer_name,
                customer_number,
                product_name,
                total_amount,
                paid_amount,
                balance_amount,
                data.get("payment_method") or "Cash",
                status,
                "Created automatically from Sales"
            ))
            payment_id = cur.lastrowid

        # Only the money actually received today is recorded in Sales.
        if paid_amount > 0:
            cur.execute("""
    INSERT INTO sales
    (
        sale_date,
        customer_name,
        customer_number,
        product_name,
        quantity,
        amount,
        split_amount,
        total_amount,
        sale_type,
        payment_id
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    sale_date,
    customer_name,
    customer_number,
    product_name,
    quantity if payment_type == "Full Payment" else 0,
    paid_amount,
    0,
    paid_amount,
    "Product",
    payment_id
))
            sale_id = cur.lastrowid

        # Stock is reduced once, when the item is sold, regardless of payment status.
        if inventory:
            cur.execute("""
                UPDATE inventory
                SET quantity = quantity - %s
                WHERE id = %s
            """, (quantity, inventory["id"]))

        conn.commit()

        if payment_type == "Credit":
            message = "Credit sale saved. It was added to Payment Tracking, not Sales."
        elif payment_type == "Partial Payment":
            message = "Partial sale saved. Received amount added to Sales and balance added to Payment Tracking."
        else:
            message = "Sale added successfully."

        return jsonify({
            "message": message,
            "id": sale_id,
            "payment_id": payment_id,
            "inventory_updated": bool(inventory),
            "sale_amount": paid_amount,
            "balance_amount": balance_amount
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
            traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# UPDATE SALE
# ---------------------------------------------------------------

@app.route("/api/sales/<int:sale_id>", methods=["PUT"])
def update_sale(sale_id):

    data = request.get_json() or {}

    sale_date = data.get("sale_date") or date.today().isoformat()
    new_product_name = str(data.get("product_name") or "").strip()

    try:
        new_quantity = int(data.get("quantity") or 0)
        amount = to_float(data.get("amount"))
        split_amount = to_float(data.get("split_amount"))
    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid quantity or amount"
        }), 400

    total_amount = amount + split_amount

    # Only a real JSON true can allow negative stock.
    allow_negative_stock = (
        data.get("allow_negative_stock") is True
    )

    if not new_product_name:
        return jsonify({
            "error": "Product name is required"
        }), 400

    if new_quantity <= 0:
        return jsonify({
            "error": "Quantity must be greater than 0"
        }), 400

    if amount < 0 or split_amount < 0:
        return jsonify({
            "error": "Amount cannot be negative"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Get old sale and lock it
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                product_name,
                quantity,
                sale_type
            FROM sales
            WHERE id = %s
            FOR UPDATE
        """, (
            sale_id,
        ))

        old_sale = cur.fetchone()

        if not old_sale:

            return jsonify({
                "error": "Sale not found"
            }), 404

        old_product_name = old_sale["product_name"]
        old_quantity = int(
            old_sale["quantity"] or 0
        )

        if old_sale.get("sale_type") == "Recharge":

            return jsonify({
                "error":
                    "Use the recharge section to edit recharge sales"
            }), 400

        if old_sale.get("sale_type") == "Repair":

            return jsonify({
                "error":
                    "Repair sales cannot be edited from Product Sales"
            }), 400

        if old_sale.get("payment_id") is not None:

            return jsonify({
                "error":
                    "Payment-linked sales cannot be edited from Product Sales. Edit the Payment Tracking record instead."
            }), 400

        # -------------------------------------------------------
        # Lock OLD inventory when it exists.
        # If the old product is not in inventory, continue without
        # restoring stock because there is no stock row to restore.
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                product_name,
                quantity
            FROM inventory
            WHERE product_name = %s
            ORDER BY id
            LIMIT 1
            FOR UPDATE
        """, (
            old_product_name,
        ))

        old_inventory = cur.fetchone()

        if old_inventory:

            # Return old sale quantity to stock before recalculating
            # the new sale.
            cur.execute("""
                UPDATE inventory
                SET quantity = quantity + %s
                WHERE id = %s
            """, (
                old_quantity,
                old_inventory["id"]
            ))

        # -------------------------------------------------------
        # Lock NEW inventory row when it exists.
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                product_name,
                quantity
            FROM inventory
            WHERE product_name = %s
            ORDER BY id
            LIMIT 1
            FOR UPDATE
        """, (
            new_product_name,
        ))

        new_inventory = cur.fetchone()

        # -------------------------------------------------------
        # NEW PRODUCT NOT IN INVENTORY
        # -------------------------------------------------------
        # The sale can still be updated. No stock movement is made.
        # -------------------------------------------------------

        if new_inventory:

            current_stock = int(
                new_inventory["quantity"] or 0
            )

            # ---------------------------------------------------
            # Check stock only for an existing inventory product.
            # ---------------------------------------------------

            if (
                current_stock < new_quantity
                and not allow_negative_stock
            ):

                conn.rollback()

                return jsonify({
                    "error": (
                        f"Insufficient stock for '{new_product_name}'. "
                        f"Available: {current_stock}, "
                        f"Required: {new_quantity}. "
                        f"Enable 'Allow Negative Stock' to continue."
                    )
                }), 400

            # Deduct the new quantity.
            cur.execute("""
                UPDATE inventory
                SET quantity = quantity - %s
                WHERE id = %s
            """, (
                new_quantity,
                new_inventory["id"]
            ))

        # -------------------------------------------------------
        # Update sale record
        # -------------------------------------------------------

        cur.execute("""
            UPDATE sales
            SET
                sale_date = %s,
                product_name = %s,
                quantity = %s,
                amount = %s,
                split_amount = %s,
                total_amount = %s
            WHERE id = %s
        """, (
            sale_date,
            new_product_name,
            new_quantity,
            amount,
            split_amount,
            total_amount,
            sale_id
        ))

        conn.commit()

        return jsonify({
            "message": "Sale updated successfully",
            "inventory_updated": bool(new_inventory)
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# DELETE SALE
# ---------------------------------------------------------------

@app.route("/api/sales/<int:sale_id>", methods=["DELETE"])
def delete_sale(sale_id):

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Get sale and lock it
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                product_name,
                quantity,
                sale_type,
                recharge_id
            FROM sales
            WHERE id = %s
            FOR UPDATE
        """, (sale_id,))

        sale = cur.fetchone()

        if not sale:

            return jsonify({
                "error": "Sale not found"
            }), 404

        if sale.get("sale_type") == "Recharge":
            conn.rollback()
            return jsonify({
                "error": "Use the recharge delete action for recharge sales"
            }), 400

        if sale.get("sale_type") == "Repair":
            conn.rollback()
            return jsonify({
                "error": "Processed repair sales cannot be deleted here"
            }), 400

        if sale.get("payment_id") is not None:
            conn.rollback()
            return jsonify({
                "error": "Payment-linked sales cannot be deleted. Edit the Payment Tracking record instead."
            }), 400

        product_name = sale["product_name"]
        quantity = int(sale["quantity"] or 0)

        # -------------------------------------------------------
        # Find inventory.
        # -------------------------------------------------------
        # If the product is not in inventory, simply delete the sale
        # without attempting to restore stock.
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                quantity
            FROM inventory
            WHERE product_name = %s
            ORDER BY id
            LIMIT 1
            FOR UPDATE
        """, (product_name,))

        inventory = cur.fetchone()

        if inventory:

            # Return sold quantity to stock.
            cur.execute("""
                UPDATE inventory
                SET quantity = quantity + %s
                WHERE id = %s
            """, (
                quantity,
                inventory["id"]
            ))

        # -------------------------------------------------------
        # Delete sale in both cases.
        # -------------------------------------------------------

        cur.execute("""
            DELETE FROM sales
            WHERE id = %s
        """, (sale_id,))

        conn.commit()

        return jsonify({
            "message": (
                "Sale deleted and stock restored successfully"
                if inventory
                else "Sale deleted successfully. Product was not in inventory, so stock was not changed."
            ),
            "inventory_updated": bool(inventory)
        })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
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
                row["purchase_date"] = (
                    row["purchase_date"].isoformat()
                )

            row["amount"] = to_float(
                row.get("amount")
            )

            row["quantity"] = int(
                row.get("quantity") or 1
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


# ===============================================================
# ADD PURCHASE
# ===============================================================

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

    quantity = int(
        data.get("quantity") or 1
    )

    if not dealer_name or not product_name:

        return jsonify({
            "error":
                "dealer_name and product_name are required"
        }), 400

    if quantity <= 0:

        return jsonify({
            "error":
                "Quantity must be greater than 0"
        }), 400

    conn = get_conn()
    cur = conn.cursor()

    try:

        # =====================================================
        # 1. SAVE PURCHASE
        # =====================================================

        cur.execute(
            """
            INSERT INTO purchases
            (
                purchase_date,
                dealer_name,
                product_name,
                amount,
                quantity
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                purchase_date,
                dealer_name,
                product_name,
                amount,
                quantity
            )
        )

        purchase_id = cur.lastrowid

        # =====================================================
        # 2. CHECK INVENTORY
        # =====================================================

        cur.execute(
            """
            SELECT id
            FROM inventory
            WHERE product_name = %s
            LIMIT 1
            """,
            (product_name,)
        )

        inventory_item = cur.fetchone()

        # =====================================================
        # 3. UPDATE EXISTING INVENTORY
        # =====================================================

        if inventory_item:

            cur.execute(
                """
                UPDATE inventory
                SET quantity = quantity + %s
                WHERE id = %s
                """,
                (
                    quantity,
                    inventory_item[0]
                )
            )

        # =====================================================
        # 4. CREATE NEW INVENTORY ITEM
        # =====================================================

        else:

            cur.execute(
                """
                INSERT INTO inventory
                (
                    product_name,
                    quantity,
                    purchase_date
                )
                VALUES (%s, %s, %s)
                """,
                (
                    product_name,
                    quantity,
                    purchase_date
                )
            )

        conn.commit()

        return jsonify({
            "id": purchase_id,
            "message":
                "Purchase added and inventory updated"
        }), 201

    except Exception as e:

        conn.rollback()

        print(
            "PURCHASE POST ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cur.close()
        conn.close()


# ===============================================================
# UPDATE PURCHASE
# ===============================================================

@app.route(
    "/api/purchases/<int:purchase_id>",
    methods=["PUT"]
)
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

    quantity = int(
        data.get("quantity") or 1
    )

    if not dealer_name or not product_name:

        return jsonify({
            "error":
                "dealer_name and product_name are required"
        }), 400

    if quantity <= 0:

        return jsonify({
            "error":
                "Quantity must be greater than 0"
        }), 400

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
                amount=%s,
                quantity=%s
            WHERE id=%s
            """,
            (
                purchase_date,
                dealer_name,
                product_name,
                amount,
                quantity,
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


# ===============================================================
# DELETE PURCHASE
# ===============================================================

@app.route(
    "/api/purchases/<int:purchase_id>",
    methods=["DELETE"]
)
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

# ===============================================================
# ENQUIRIES
# ===============================================================

# ---------------------------------------------------------------
# GET ENQUIRIES
# ---------------------------------------------------------------

@app.route("/api/enquiries", methods=["GET"])
def get_enquiries():

    d, m = parse_filters()

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = dict_cursor(conn)

        if d:

            cur.execute(
                """
                SELECT
                    id,
                    enquiry_date,
                    customer_name,
                    customer_number,
                    customer_enquiry
                FROM enquiries
                WHERE enquiry_date = %s
                ORDER BY id DESC
                """,
                (d,)
            )

        elif m:

            cur.execute(
                """
                SELECT
                    id,
                    enquiry_date,
                    customer_name,
                    customer_number,
                    customer_enquiry
                FROM enquiries
                WHERE enquiry_date >= %s
                AND enquiry_date < DATE_ADD(
                    %s,
                    INTERVAL 1 MONTH
                )
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
                SELECT
                    id,
                    enquiry_date,
                    customer_name,
                    customer_number,
                    customer_enquiry
                FROM enquiries
                ORDER BY enquiry_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("enquiry_date"):
                row["enquiry_date"] = (
                    row["enquiry_date"].isoformat()
                )

            row["customer_number"] = (
                row.get("customer_number") or ""
            )

            row["customer_enquiry"] = (
                row.get("customer_enquiry") or ""
            )

        return jsonify(rows)

    except Exception as e:

        print("ENQUIRY GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# ADD ENQUIRY
# ---------------------------------------------------------------

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

    customer_number = (
        data.get("customer_number")
        or ""
    ).strip()

    customer_enquiry = (
        data.get("customer_enquiry")
        or ""
    ).strip()

    if not customer_name:

        return jsonify({
            "error": "Customer name is required"
        }), 400

    if not customer_enquiry:

        return jsonify({
            "error": "Customer enquiry is required"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO enquiries
            (
                enquiry_date,
                customer_name,
                customer_number,
                customer_enquiry
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                enquiry_date,
                customer_name,
                customer_number,
                customer_enquiry
            )
        )

        enquiry_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "id": enquiry_id,
            "message": "Enquiry added successfully"
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        print("ENQUIRY POST ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ---------------------------------------------------------------
# DELETE ENQUIRY
# ---------------------------------------------------------------

@app.route(
    "/api/enquiries/<int:enquiry_id>",
    methods=["DELETE"]
)
def delete_enquiry(enquiry_id):

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM enquiries
            WHERE id = %s
            """,
            (enquiry_id,)
        )

        deleted = cur.rowcount

        conn.commit()

        return jsonify({
            "deleted": deleted,
            "message": "Enquiry deleted successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print("ENQUIRY DELETE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()





# ===============================================================
# REPAIRS
# ===============================================================

REPAIR_STATUSES = [
    "Received",
    "In Progress",
    "Item Returned",
    "Completed",
    "Delivered to Customer"
]


# ===============================================================
# GET REPAIRS
# ===============================================================

@app.route("/api/repairs", methods=["GET"])
def get_repairs():

    d, m = parse_filters()

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = dict_cursor(conn)

        if d:

            cur.execute(
                """
                SELECT
                    id,
                    repair_date,
                    delivery_date,
                    customer_name,
                    customer_number,
                    product_name,
                    model,
                    issue,
                    part_request,
                    amount,
                    advance,
                    status,
                    stock_reduced,
                    sales_recorded,
                    received_at,
                    delivered_at,
                    created_at
                FROM repairs
                WHERE
                (
                    -- Repairs received on the selected date.
                    repair_date = %s

                    OR

                    -- Older repairs stay visible only while they
                    -- have not yet been delivered.
                    (
                        repair_date < %s
                        AND delivered_at IS NULL
                    )

                    OR

                    -- A delivered repair is visible on its
                    -- actual physical delivery date only.
                    delivery_date = %s

                    OR

                    -- An item returned repair is visible on the
                    -- date it was actually returned/closed.
                    (
                        status = 'Item Returned'
                        AND DATE(delivered_at) = %s
                    )
                )
                ORDER BY id DESC
                """,
                (
                    d,
                    d,
                    d,
                    d
                )
            )

        elif m:

            cur.execute(
                """
                SELECT
                    id,
                    repair_date,
                    delivery_date,
                    customer_name,
                    customer_number,
                    product_name,
                    model,
                    issue,
                    part_request,
                    amount,
                    advance,
                    status,
                    stock_reduced,
                    sales_recorded,
                    received_at,
                    delivered_at,
                    created_at
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
                SELECT
                    id,
                    repair_date,
                    delivery_date,
                    customer_name,
                    customer_number,
                    product_name,
                    model,
                    issue,
                    part_request,
                    amount,
                    advance,
                    status,
                    stock_reduced,
                    sales_recorded,
                    received_at,
                    delivered_at,
                    created_at
                FROM repairs
                ORDER BY repair_date DESC, id DESC
                LIMIT 200
                """
            )

        rows = cur.fetchall()

        for row in rows:

            if row.get("repair_date"):
                row["repair_date"] = row["repair_date"].isoformat()

            if row.get("delivery_date"):
                row["delivery_date"] = row["delivery_date"].isoformat()

            if row.get("received_at"):
                row["received_at"] = row["received_at"].isoformat()

            if row.get("delivered_at"):
                row["delivered_at"] = row["delivered_at"].isoformat()

            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()

            row["amount"] = to_float(row.get("amount"))
            row["advance"] = to_float(row.get("advance"))

            row["stock_reduced"] = int(
                row.get("stock_reduced") or 0
            )

            row["sales_recorded"] = int(
                row.get("sales_recorded") or 0
            )

        return jsonify(rows)

    except Exception as e:

        print("REPAIR GET ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# ADD REPAIR
# ===============================================================

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

    customer_number = (
        data.get("customer_number")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    model = (
        data.get("model")
        or ""
    ).strip()

    issue = (
        data.get("issue")
        or ""
    ).strip()

    part_request = (
        data.get("part_request")
        or ""
    ).strip()

    status = (
        data.get("status")
        or "Received"
    )

    try:

        amount = to_float(
            data.get("amount")
        )

        advance = to_float(
            data.get("advance")
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid amount or advance"
        }), 400

    # -----------------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------------

    if not customer_name:

        return jsonify({
            "error": "Customer name is required"
        }), 400

    if not product_name:

        return jsonify({
            "error": "Product name is required"
        }), 400

    if status not in REPAIR_STATUSES:

        return jsonify({
            "error": "Invalid repair status"
        }), 400

    if amount < 0:

        return jsonify({
            "error": "Amount cannot be negative"
        }), 400

    if advance < 0:

        return jsonify({
            "error": "Advance cannot be negative"
        }), 400

    if advance > amount:

        return jsonify({
            "error": "Advance cannot be greater than amount"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO repairs
            (
                repair_date,
                delivery_date,
                customer_name,
                customer_number,
                product_name,
                model,
                issue,
                part_request,
                amount,
                advance,
                status,
                stock_reduced,
                sales_recorded,
                received_at,
                delivered_at
            )
            VALUES
            (
                %s,
                NULL,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                0,
                0,
                %s,
                NULL
            )
            """,
            (
                repair_date,
                customer_name,
                customer_number,
                product_name,
                model,
                issue,
                part_request,
                amount,
                advance,
                status,
                datetime.now(IST).replace(tzinfo=None)
            )
        )

        repair_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "id": repair_id,
            "message": "Repair added successfully"
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        print("REPAIR POST ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# UPDATE REPAIR
# ===============================================================

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

    customer_number = (
        data.get("customer_number")
        or ""
    ).strip()

    product_name = (
        data.get("product_name")
        or ""
    ).strip()

    model = (
        data.get("model")
        or ""
    ).strip()

    issue = (
        data.get("issue")
        or ""
    ).strip()

    part_request = (
        data.get("part_request")
        or ""
    ).strip()

    status = (
        data.get("status")
        or "Received"
    )

    try:

        amount = to_float(
            data.get("amount")
        )

        advance = to_float(
            data.get("advance")
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid amount or advance"
        }), 400

    if not customer_name:

        return jsonify({
            "error": "Customer name is required"
        }), 400

    if not product_name:

        return jsonify({
            "error": "Product name is required"
        }), 400

    if status not in REPAIR_STATUSES:

        return jsonify({
            "error": "Invalid repair status"
        }), 400

    if amount < 0 or advance < 0:

        return jsonify({
            "error": "Amount and advance cannot be negative"
        }), 400

    if advance > amount:

        return jsonify({
            "error": "Advance cannot be greater than amount"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Get existing repair
        # -------------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                status,
                stock_reduced,
                sales_recorded
            FROM repairs
            WHERE id = %s
            FOR UPDATE
            """,
            (repair_id,)
        )

        existing = cur.fetchone()

        if not existing:

            return jsonify({
                "error": "Repair not found"
            }), 404

        # -------------------------------------------------------
        # Do not allow editing delivered repair back to another
        # status if stock/sale processing has already happened.
        # -------------------------------------------------------

        if (
            int(existing["sales_recorded"] or 0) == 1
            and status != "Delivered to Customer"
        ):

            return jsonify({
                "error": (
                    "Delivered repair cannot be moved back "
                    "to another status after sales recording"
                )
            }), 400

        cur.execute(
            """
            UPDATE repairs
            SET
                repair_date = %s,
                customer_name = %s,
                customer_number = %s,
                product_name = %s,
                model = %s,
                issue = %s,
                part_request = %s,
                amount = %s,
                advance = %s,
                status = %s,
                delivered_at = CASE
                    WHEN %s = 'Delivered to Customer'
                    THEN COALESCE(
                        delivered_at,
                        %s
                    )
                    ELSE delivered_at
                END
            WHERE id = %s
            """,
            (
                repair_date,
                customer_name,
                customer_number,
                product_name,
                model,
                issue,
                part_request,
                amount,
                advance,
                status,
                status,
                datetime.now(IST).replace(tzinfo=None),
                repair_id
            )
        )

        conn.commit()

        return jsonify({
            "updated": cur.rowcount,
            "message": "Repair updated successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print("REPAIR UPDATE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# ===============================================================
# CHANGE REPAIR STATUS
# ===============================================================

@app.route(
    "/api/repairs/<int:repair_id>/status",
    methods=["PATCH"]
)
def update_repair_status(repair_id):

    data = request.get_json(force=True)

    new_status = (
        data.get("status")
        or ""
    ).strip()

    delivery_date = data.get("delivery_date")

    if new_status not in REPAIR_STATUSES:

        return jsonify({
            "error": "Invalid repair status"
        }), 400

    # -------------------------------------------------------
    # ACTUAL DELIVERY DATE
    # -------------------------------------------------------
    # This is the date the customer physically received the phone.
    # It is intentionally separate from delivered_at, which stores
    # when the application was updated.
    # -------------------------------------------------------

    if new_status == "Delivered to Customer":

        if not delivery_date:

            return jsonify({
                "error": "Actual delivery date is required"
            }), 400

        try:

            delivery_date_obj = datetime.strptime(
                str(delivery_date),
                "%Y-%m-%d"
            ).date()

        except (ValueError, TypeError):

            return jsonify({
                "error": "Invalid delivery date. Use YYYY-MM-DD."
            }), 400

        if delivery_date_obj > date.today():

            return jsonify({
                "error": "Delivery date cannot be a future date"
            }), 400

        delivery_date = delivery_date_obj.isoformat()

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Lock repair
        # -------------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                customer_name,
                customer_number,
                product_name,
                model,
                issue,
                part_request,
                amount,
                advance,
                status,
                stock_reduced,
                sales_recorded,
                delivery_date
            FROM repairs
            WHERE id = %s
            FOR UPDATE
            """,
            (repair_id,)
        )

        repair = cur.fetchone()

        if not repair:

            return jsonify({
                "error": "Repair not found"
            }), 404

        # -------------------------------------------------------
        # ITEM RETURNED IS A FINAL STATUS
        # -------------------------------------------------------

        if (
            repair["status"] == "Item Returned"
            and new_status != "Item Returned"
        ):

            return jsonify({
                "error": (
                    "Item Returned is a final status and "
                    "cannot be changed back"
                )
            }), 400

        # -------------------------------------------------------
        # PREVENT DUPLICATE DELIVERY PROCESSING
        # -------------------------------------------------------

        if (
            int(repair["sales_recorded"] or 0) == 1
            and new_status != "Delivered to Customer"
        ):

            return jsonify({
                "error": (
                    "This repair has already been delivered "
                    "and recorded"
                )
            }), 400

        # -------------------------------------------------------
        # ITEM RETURNED PROCESS
        # -------------------------------------------------------

        if new_status == "Item Returned":

            cur.execute(
                """
                UPDATE repairs
                SET
                    status = %s,
                    delivered_at = COALESCE(
                        delivered_at,
                        %s
                    )
                WHERE id = %s
                """,
                (
                    new_status,
                    datetime.now(IST).replace(tzinfo=None),
                    repair_id
                )
            )

            conn.commit()

            return jsonify({
                "message": (
                    "Item returned successfully. "
                    "No sale or stock change was made."
                ),
                "repair_id": repair_id,
                "status": new_status,
                "stock_reduced": int(
                    repair["stock_reduced"] or 0
                ),
                "sales_recorded": int(
                    repair["sales_recorded"] or 0
                ),
                "balance": max(
                    0,
                    to_float(repair["amount"])
                    - to_float(repair["advance"])
                )
            })

        # -------------------------------------------------------
        # DELIVERY PROCESS
        # -------------------------------------------------------

        if new_status == "Delivered to Customer":

            quoted_amount = to_float(
                repair["amount"]
            )

            advance = to_float(
                repair["advance"]
            )

            raw_final_amount = data.get("final_amount")

            try:

                final_amount = to_float(
                    raw_final_amount
                )

            except (ValueError, TypeError):

                return jsonify({
                    "error": "Enter a valid final repair amount"
                }), 400

            if final_amount < 0:

                return jsonify({
                    "error": "Final repair amount cannot be negative"
                }), 400

            if final_amount > quoted_amount:

                return jsonify({
                    "error": (
                        f"Final repair amount cannot be greater than "
                        f"the quoted amount of ₹{quoted_amount:.2f}"
                    )
                }), 400

            if final_amount < advance:

                return jsonify({
                    "error": (
                        f"Final repair amount cannot be less than the "
                        f"advance already received of ₹{advance:.2f}"
                    )
                }), 400

            remaining = 0
            total_received = final_amount

            # ===================================================
            # 1. REDUCE PART STOCK
            # ===================================================

            if (
                repair["part_request"]
                and int(repair["stock_reduced"] or 0) == 0
            ):

                part_name = (
                    repair["part_request"]
                    or ""
                ).strip()

                cur.execute(
                    """
                    SELECT
                        id,
                        product_name,
                        quantity
                    FROM inventory
                    WHERE product_name = %s
                    ORDER BY id
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (part_name,)
                )

                inventory = cur.fetchone()

                if not inventory:

                    conn.rollback()

                    return jsonify({
                        "error": (
                            f"Part '{part_name}' "
                            "was not found in inventory"
                        )
                    }), 400

                current_stock = int(
                    inventory["quantity"] or 0
                )

                if current_stock < 1:

                    conn.rollback()

                    return jsonify({
                        "error": (
                            f"Insufficient stock for part "
                            f"'{part_name}'. "
                            f"Available: {current_stock}"
                        )
                    }), 400

                cur.execute(
                    """
                    UPDATE inventory
                    SET quantity = quantity - 1
                    WHERE id = %s
                    """,
                    (inventory["id"],)
                )

                cur.execute(
                    """
                    UPDATE repairs
                    SET stock_reduced = 1
                    WHERE id = %s
                    """,
                    (repair_id,)
                )

            # ===================================================
            # 2. RECORD REPAIR IN SALES
            # ===================================================

            if int(repair["sales_recorded"] or 0) == 0:

                received_amount = final_amount

                cur.execute(
                    """
                    INSERT INTO sales
                    (
                        sale_date,
                        customer_name,
                        customer_number,
                        product_name,
                        quantity,
                        amount,
                        split_amount,
                        total_amount,
                        sale_type,
                        repair_id
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        1,
                        %s,
                        0,
                        %s,
                        'Repair',
                        %s
                    )
                    """,
                    (
                        delivery_date,
                        repair["customer_name"],
                        repair["customer_number"],
                        repair["product_name"],
                        received_amount,
                        received_amount,
                        repair_id
                    )
                )

                cur.execute(
                    """
                    UPDATE repairs
                    SET sales_recorded = 1
                    WHERE id = %s
                    """,
                    (repair_id,)
                )

            # ===================================================
            # 3. UPDATE REPAIR STATUS + ACTUAL DELIVERY DATE
            # ===================================================

            cur.execute(
                """
                UPDATE repairs
                SET
                    status = %s,
                    delivery_date = %s,
                    delivered_at = COALESCE(
                        delivered_at,
                        %s
                    )
                WHERE id = %s
                """,
                (
                    new_status,
                    delivery_date,
                    datetime.now(IST).replace(tzinfo=None),
                    repair_id
                )
            )

            conn.commit()

            return jsonify({
                "message": "Repair delivered successfully",
                "repair_id": repair_id,
                "quoted_amount": quoted_amount,
                "discount": round(
                    quoted_amount - final_amount,
                    2
                ),
                "amount": final_amount,
                "advance": total_received,
                "received_amount": final_amount,
                "balance": remaining,
                "delivery_date": delivery_date,
                "stock_reduced": True,
                "sales_recorded": True
            })

        # =======================================================
        # NORMAL STATUS CHANGE
        # =======================================================

        cur.execute(
            """
            UPDATE repairs
            SET status = %s
            WHERE id = %s
            """,
            (
                new_status,
                repair_id
            )
        )

        conn.commit()

        return jsonify({
            "message": "Repair status updated successfully",
            "repair_id": repair_id,
            "status": new_status
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print("REPAIR STATUS ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


@app.route(
    "/api/repairs/<int:repair_id>/balance-payment",
    methods=["POST"]
)
def add_repair_balance_payment(repair_id):

    data = request.get_json(force=True) or {}

    try:
        payment_amount = to_float(
            data.get("payment_amount")
        )
    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid payment amount"
        }), 400

    if payment_amount <= 0:
        return jsonify({
            "error": "Payment amount must be greater than 0"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Lock repair so two balance payments cannot overlap.
        # -------------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                amount,
                advance,
                status,
                sales_recorded
            FROM repairs
            WHERE id = %s
            FOR UPDATE
            """,
            (repair_id,)
        )

        repair = cur.fetchone()

        if not repair:
            return jsonify({
                "error": "Repair not found"
            }), 404

        if repair["status"] != "Delivered to Customer":
            return jsonify({
                "error": (
                    "Balance payment can be recorded only after "
                    "the repair is delivered to the customer"
                )
            }), 400

        if int(repair["sales_recorded"] or 0) != 1:
            return jsonify({
                "error": "Repair sale record was not found"
            }), 400

        full_amount = to_float(repair["amount"])
        paid_so_far = to_float(repair["advance"])
        current_balance = round(
            full_amount - paid_so_far,
            2
        )

        if current_balance <= 0:
            return jsonify({
                "error": "This repair is already fully paid"
            }), 400

        if payment_amount > current_balance:
            return jsonify({
                "error": (
                    f"Payment cannot be greater than the "
                    f"remaining balance of ₹{current_balance:.2f}"
                )
            }), 400

        # -------------------------------------------------------
        # Repair sales logic
        # -------------------------------------------------------
        # The repair sale was already created at DELIVERY using
        # the FULL repair amount and the delivery date.
        #
        # Therefore, a later balance payment must update only the
        # repair's advance/balance. It must NOT change sales.total_amount.
        # Otherwise the same repair would be counted again in the
        # dashboard and sales totals.
        # -------------------------------------------------------

        cur.execute(
            """
            SELECT id
            FROM sales
            WHERE repair_id = %s
              AND sale_type = 'Repair'
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """,
            (repair_id,)
        )

        sale = cur.fetchone()

        if not sale:
            return jsonify({
                "error": "Repair sale record was not found"
            }), 400

        new_paid = round(
            paid_so_far + payment_amount,
            2
        )

        new_balance = round(
            full_amount - new_paid,
            2
        )

        cur.execute(
            """
            UPDATE repairs
            SET advance = %s
            WHERE id = %s
            """,
            (
                new_paid,
                repair_id
            )
        )

        conn.commit()

        return jsonify({
            "message": "Repair balance payment recorded successfully",
            "repair_id": repair_id,
            "payment_received": payment_amount,
            "total_received": new_paid,
            "balance": new_balance
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REPAIR BALANCE PAYMENT ERROR:",
            e
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
# DELETE REPAIR
# ===============================================================

@app.route(
    "/api/repairs/<int:repair_id>",
    methods=["DELETE"]
)
def delete_repair(repair_id):

    conn = None
    cur = None

    try:

        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # -------------------------------------------------------
        # Check repair
        # -------------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                stock_reduced,
                sales_recorded
            FROM repairs
            WHERE id = %s
            FOR UPDATE
            """,
            (repair_id,)
        )

        repair = cur.fetchone()

        if not repair:

            return jsonify({
                "error": "Repair not found"
            }), 404

        # -------------------------------------------------------
        # Prevent deletion after stock/sales processing
        # -------------------------------------------------------

        if (
            int(repair["stock_reduced"] or 0) == 1
            or
            int(repair["sales_recorded"] or 0) == 1
        ):

            return jsonify({
                "error": (
                    "This repair cannot be deleted because "
                    "stock or sales has already been processed"
                )
            }), 400

        cur.execute(
            """
            DELETE FROM repairs
            WHERE id = %s
            """,
            (
                repair_id,
            )
        )

        conn.commit()

        return jsonify({
            "deleted": cur.rowcount,
            "message": "Repair deleted successfully"
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "REPAIR DELETE ERROR:",
            e
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
                WHERE (
                    payment_date = %s
                    OR (
                        payment_date < %s
                        AND balance_amount > 0
                    )
                )
                ORDER BY
                    (balance_amount > 0) DESC,
                    payment_date DESC,
                    id DESC
                """,
                (d, d)
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

        customer_number = (
            data.get("customer_number")
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
                    customer_number,
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
                    %s,
                    %s
                )
                """,
                (
                    payment_date,
                    customer_name,
                    customer_number,
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

    data = request.get_json(force=True) or {}

    payment_date = data.get("payment_date") or date.today().isoformat()
    customer_name = str(data.get("customer_name") or "").strip()
    customer_number = str(data.get("customer_number") or "").strip()
    reference_name = str(data.get("reference_name") or "").strip()
    payment_method = data.get("payment_method") or "Cash"
    notes = str(data.get("notes") or "").strip()

    try:
        additional_payment = to_float(data.get("additional_payment", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid additional payment amount"}), 400

    if not customer_name:
        return jsonify({"error": "customer_name is required"}), 400
    if not reference_name:
        return jsonify({"error": "reference_name is required"}), 400
    if additional_payment < 0:
        return jsonify({"error": "Additional payment cannot be negative"}), 400
    if payment_method not in PAYMENT_METHODS:
        return jsonify({"error": "Invalid payment method"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # Lock the outstanding record so two users cannot collect the same balance.
        cur.execute("""
            SELECT
                id,
                payment_date,
                customer_name,
                reference_name,
                total_amount,
                paid_amount,
                balance_amount,
                payment_method,
                status,
                notes
            FROM payments
            WHERE id = %s
            FOR UPDATE
        """, (payment_id,))

        payment = cur.fetchone()
        if not payment:
            return jsonify({"error": "Payment record not found"}), 404

        old_paid = to_float(payment["paid_amount"])
        old_balance = to_float(payment["balance_amount"])
        total_amount = to_float(payment["total_amount"])

        if additional_payment > old_balance:
            return jsonify({
                "error": f"Payment cannot be greater than the pending balance of ₹{old_balance:.2f}"
            }), 400

        new_paid = round(old_paid + additional_payment, 2)
        new_balance = round(total_amount - new_paid, 2)
        status = "Paid" if new_balance == 0 else ("Partial" if new_paid > 0 else "Pending")

        # Every new amount actually received becomes a new Sales entry on THIS date.
        sale_id = None
        if additional_payment > 0:
            cur.execute("""
                INSERT INTO sales
                (
                    sale_date,
                    customer_name,
                    customer_number,
                    product_name,
                    quantity,
                    amount,
                    split_amount,
                    total_amount,
                    sale_type,
                    payment_id
                )
                VALUES (%s,%s,%s,%s,0,%s,0,%s,'Credit Payment',%s)
            """, (
                payment_date,
                customer_name,
                payment.get("customer_number") or "",
                reference_name,
                additional_payment,
                additional_payment,
                payment_id
            ))
            sale_id = cur.lastrowid

        cur.execute("""
            UPDATE payments
            SET
                payment_date=%s,
                customer_name=%s,
                customer_number=%s,
                reference_name=%s,
                paid_amount=%s,
                balance_amount=%s,
                payment_method=%s,
                status=%s,
                notes=%s
            WHERE id=%s
        """, (
            payment_date,
            customer_name,
            customer_number,
            reference_name,
            new_paid,
            new_balance,
            payment_method,
            status,
            notes,
            payment_id
        ))

        conn.commit()

        return jsonify({
            "updated": cur.rowcount,
            "payment_received_now": additional_payment,
            "paid_amount": new_paid,
            "balance_amount": new_balance,
            "status": status,
            "sale_id": sale_id
        })

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
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
            SELECT COUNT(*) AS total
            FROM sales
            WHERE payment_id = %s
            """,
            (payment_id,)
        )

        linked = cur.fetchone()
        if linked and int(linked[0] or 0) > 0:
            return jsonify({
                "error": "This payment has Sales entries linked to it and cannot be deleted."
            }), 400

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
        # Show ALL outstanding customer balances up to the
        # selected date. An unpaid balance therefore carries
        # forward and remains visible every day until it is paid.
        #
        # Example:
        #   23-Sep: Total ₹2,000, Paid ₹1,000, Balance ₹1,000
        #   24-Sep: Balance still ₹1,000
        #   Customer pays the remaining ₹1,000
        #   24-Sep dashboard pending becomes ₹0
        # =======================================================

        today_payment_balance = scalar(
            """
            SELECT COALESCE(
                SUM(balance_amount),
                0
            ) AS total
            FROM payments
            WHERE payment_date <= %s
              AND balance_amount > 0
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
            WHERE payment_date < DATE_ADD(
                %s,
                INTERVAL 1 MONTH
            )
              AND balance_amount > 0
            """,
            (f"{m}-01",)
        )

        # =======================================================
        # ACTIVE REPAIRS
        # =======================================================

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM repairs
            WHERE status NOT IN (
                'Delivered to Customer',
                'Item Returned'
            )
            """
        )

        row = cur.fetchone()

        active_repairs = int(
            row["total"] or 0
        )

        # =======================================================
        # SIM RECHARGE SALES
        # =======================================================

        today_recharge_sales = scalar(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM sales
            WHERE sale_date = %s
              AND sale_type = 'Recharge'
            """,
            (d,)
        )

        month_recharge_sales = scalar(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM sales
            WHERE sale_date >= %s
              AND sale_date < DATE_ADD(%s, INTERVAL 1 MONTH)
              AND sale_type = 'Recharge'
            """,
            (f"{m}-01", f"{m}-01")
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

            "today_recharge_sales":
                today_recharge_sales,

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

            "month_recharge_sales":
                month_recharge_sales,

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

 # ============================================================
# ===============================================================
# MASTER DATA API
# ===============================================================

@app.route("/api/master", methods=["GET"])
def get_master_data():

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        cur.execute("""
            SELECT id, name, created_at
            FROM master_categories
            ORDER BY name ASC
        """)
        categories = cur.fetchall()

        cur.execute("""
            SELECT
                m.id,
                m.category_id,
                m.name,
                c.name AS category_name,
                m.created_at
            FROM master_models m
            INNER JOIN master_categories c
                ON c.id = m.category_id
            ORDER BY c.name ASC, m.name ASC
        """)
        models = cur.fetchall()

        cur.execute("""
            SELECT
                p.id,
                p.model_id,
                p.name,
                m.name AS model_name,
                c.id AS category_id,
                c.name AS category_name,
                p.created_at
            FROM master_parts p
            INNER JOIN master_models m
                ON m.id = p.model_id
            INNER JOIN master_categories c
                ON c.id = m.category_id
            ORDER BY c.name ASC, m.name ASC, p.name ASC
        """)
        parts = cur.fetchall()

        return jsonify({
            "categories": categories,
            "models": models,
            "parts": parts
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/categories", methods=["POST"])
def add_master_category():

    data = request.get_json() or {}
    name = str(data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO master_categories (name) VALUES (%s)",
            (name,)
        )
        conn.commit()

        return jsonify({
            "id": cur.lastrowid,
            "message": "Category added successfully"
        }), 201

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()

        if getattr(e, "errno", None) == 1062:
            return jsonify({
                "error": f"Category '{name}' already exists"
            }), 409

        return jsonify({"error": str(e)}), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/categories/<int:category_id>", methods=["DELETE"])
def delete_master_category(category_id):

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        cur.execute(
            "SELECT id, name FROM master_categories WHERE id = %s",
            (category_id,)
        )
        category = cur.fetchone()

        if not category:
            return jsonify({"error": "Category not found"}), 404

        cur.execute(
            "SELECT COUNT(*) AS total FROM master_models WHERE category_id = %s",
            (category_id,)
        )
        if int(cur.fetchone()["total"] or 0) > 0:
            return jsonify({
                "error": "Delete this category's models first"
            }), 400

        cur.execute(
            "SELECT COUNT(*) AS total FROM inventory WHERE category = %s",
            (category["name"],)
        )
        if int(cur.fetchone()["total"] or 0) > 0:
            return jsonify({
                "error": "This category is already used in Inventory and cannot be deleted"
            }), 400

        cur.execute(
            "DELETE FROM master_categories WHERE id = %s",
            (category_id,)
        )
        conn.commit()

        return jsonify({"message": "Category deleted successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/models", methods=["POST"])
def add_master_model():

    data = request.get_json() or {}

    try:
        category_id = int(data.get("category_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid category is required"}), 400

    name = str(data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Model name is required"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM master_categories WHERE id = %s",
            (category_id,)
        )
        if not cur.fetchone():
            return jsonify({"error": "Category not found"}), 404

        cur.execute(
            """
            INSERT INTO master_models (category_id, name)
            VALUES (%s, %s)
            """,
            (category_id, name)
        )
        conn.commit()

        return jsonify({
            "id": cur.lastrowid,
            "message": "Model added successfully"
        }), 201

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()

        if getattr(e, "errno", None) == 1062:
            return jsonify({
                "error": f"Model '{name}' already exists in this category"
            }), 409

        return jsonify({"error": str(e)}), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/models/<int:model_id>", methods=["DELETE"])
def delete_master_model(model_id):

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        cur.execute(
            """
            SELECT m.id, m.category_id, m.name, c.name AS category_name
            FROM master_models m
            INNER JOIN master_categories c
                ON c.id = m.category_id
            WHERE m.id = %s
            """,
            (model_id,)
        )
        model = cur.fetchone()

        if not model:
            return jsonify({"error": "Model not found"}), 404

        cur.execute(
            "SELECT COUNT(*) AS total FROM master_parts WHERE model_id = %s",
            (model_id,)
        )
        if int(cur.fetchone()["total"] or 0) > 0:
            return jsonify({
                "error": "Delete this model's part / items first"
            }), 400

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM inventory
            WHERE category = %s
              AND model = %s
            """,
            (model["category_name"], model["name"])
        )
        if int(cur.fetchone()["total"] or 0) > 0:
            return jsonify({
                "error": "This model is already used in Inventory and cannot be deleted"
            }), 400

        cur.execute(
            "DELETE FROM master_models WHERE id = %s",
            (model_id,)
        )
        conn.commit()

        return jsonify({"message": "Model deleted successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/parts", methods=["POST"])
def add_master_part():

    data = request.get_json() or {}

    try:
        model_id = int(data.get("model_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid model is required"}), 400

    name = str(data.get("name") or "").strip()

    if not name:
        return jsonify({"error": "Part / Item name is required"}), 400

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM master_models WHERE id = %s",
            (model_id,)
        )
        if not cur.fetchone():
            return jsonify({"error": "Model not found"}), 404

        cur.execute(
            """
            INSERT INTO master_parts (model_id, name)
            VALUES (%s, %s)
            """,
            (model_id, name)
        )
        conn.commit()

        return jsonify({
            "id": cur.lastrowid,
            "message": "Part / Item added successfully"
        }), 201

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()

        if getattr(e, "errno", None) == 1062:
            return jsonify({
                "error": f"Part / Item '{name}' already exists for this model"
            }), 409

        return jsonify({"error": str(e)}), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route("/api/master/parts/<int:part_id>", methods=["DELETE"])
def delete_master_part(part_id):

    conn = None
    cur = None

    try:
        conn = get_conn()
        cur = dict_cursor(conn)

        cur.execute(
            """
            SELECT
                p.id,
                p.model_id,
                p.name,
                m.name AS model_name,
                c.name AS category_name
            FROM master_parts p
            INNER JOIN master_models m
                ON m.id = p.model_id
            INNER JOIN master_categories c
                ON c.id = m.category_id
            WHERE p.id = %s
            """,
            (part_id,)
        )
        part = cur.fetchone()

        if not part:
            return jsonify({"error": "Part / Item not found"}), 404

        cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM inventory
            WHERE category = %s
              AND model = %s
              AND part_item = %s
            """,
            (
                part["category_name"],
                part["model_name"],
                part["name"]
            )
        )
        if int(cur.fetchone()["total"] or 0) > 0:
            return jsonify({
                "error": "This part / item is already used in Inventory and cannot be deleted"
            }), 400

        cur.execute(
            "DELETE FROM master_parts WHERE id = %s",
            (part_id,)
        )
        conn.commit()

        return jsonify({"message": "Part / Item deleted successfully"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# INVENTORY API
# ============================================================

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    conn = None
    cursor = None

    try:
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                product_name,
                category,
                model,
                part_item,
                purchase_price,
                selling_price,
                quantity,
                minimum_stock,
                created_at
            FROM inventory
            ORDER BY id DESC
        """)

        inventory = cursor.fetchall()

        return jsonify(inventory)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/inventory", methods=["POST"])
def add_inventory():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        product_name = str(data.get("product_name") or "").strip()
        category = str(data.get("category") or "").strip()
        model = str(data.get("model") or "").strip()
        part_item = str(data.get("part_item") or "").strip()
        purchase_price = data.get("purchase_price", 0)
        selling_price = data.get("selling_price", 0)
        quantity = data.get("quantity", 0)
        minimum_stock = data.get("minimum_stock", 2)

        if not product_name:
            return jsonify({
                "error": "Product name is required"
            }), 400

        if not category:
            return jsonify({
                "error": "Category is required"
            }), 400

        if not model:
            return jsonify({
                "error": "Model is required"
            }), 400

        if not part_item:
            return jsonify({
                "error": "Part / Item is required"
            }), 400

        try:
            quantity = int(quantity)
            minimum_stock = int(minimum_stock)
            purchase_price = float(purchase_price or 0)
            selling_price = float(selling_price or 0)
        except (TypeError, ValueError):
            return jsonify({
                "error": "Invalid quantity or amount"
            }), 400

        if quantity < 0:
            return jsonify({
                "error": "Quantity cannot be negative"
            }), 400

        if minimum_stock < 0:
            return jsonify({
                "error": "Low stock limit cannot be negative"
            }), 400

        if purchase_price < 0 or selling_price < 0:
            return jsonify({
                "error": "Amount cannot be negative"
            }), 400

        conn = pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO inventory
            (
                product_name,
                category,
                model,
                part_item,
                purchase_price,
                selling_price,
                quantity,
                minimum_stock
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product_name,
            category,
            model,
            part_item,
            purchase_price,
            selling_price,
            quantity,
            minimum_stock
        ))

        conn.commit()

        return jsonify({
            "message": "Inventory item added successfully",
            "id": cursor.lastrowid
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/inventory/<int:item_id>", methods=["PUT"])
def update_inventory(item_id):
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        product_name = str(data.get("product_name") or "").strip()
        category = str(data.get("category") or "").strip()
        model = str(data.get("model") or "").strip()
        part_item = str(data.get("part_item") or "").strip()
        purchase_price = data.get("purchase_price", 0)
        selling_price = data.get("selling_price", 0)
        quantity = data.get("quantity", 0)
        minimum_stock = data.get("minimum_stock", 2)

        if not product_name or not category or not model or not part_item:
            return jsonify({
                "error": "Product name, category, model and part / item are required"
            }), 400

        try:
            quantity = int(quantity)
            minimum_stock = int(minimum_stock)
            purchase_price = float(purchase_price or 0)
            selling_price = float(selling_price or 0)
        except (TypeError, ValueError):
            return jsonify({
                "error": "Invalid quantity or amount"
            }), 400

        if quantity < 0:
            return jsonify({
                "error": "Quantity cannot be negative"
            }), 400

        if minimum_stock < 0:
            return jsonify({
                "error": "Low stock limit cannot be negative"
            }), 400

        if purchase_price < 0 or selling_price < 0:
            return jsonify({
                "error": "Amount cannot be negative"
            }), 400

        conn = pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE inventory
            SET
                product_name = %s,
                category = %s,
                model = %s,
                part_item = %s,
                purchase_price = %s,
                selling_price = %s,
                quantity = %s,
                minimum_stock = %s
            WHERE id = %s
        """, (
            product_name,
            category,
            model,
            part_item,
            purchase_price,
            selling_price,
            quantity,
            minimum_stock,
            item_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Inventory item not found"
            }), 404

        return jsonify({
            "message": "Inventory item updated successfully"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/inventory/<int:item_id>", methods=["DELETE"])
def delete_inventory(item_id):
    conn = None
    cursor = None

    try:
        conn = pool.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM inventory WHERE id = %s",
            (item_id,)
        )

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Inventory item not found"
            }), 404

        return jsonify({
            "message": "Inventory item deleted successfully"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ===============================================================
# SIM RECHARGE
# ===============================================================

RECHARGE_OPERATORS = [
    "Jio",
    "Airtel",
    "Vi",
    "BSNL"
]


@app.route("/api/recharge", methods=["GET"])
def get_recharges():
    """Return recharge transactions for the selected date/month."""
    conn = None
    cur = None

    try:
        d, m = parse_filters()
        operator = (request.args.get("operator") or "").strip()

        conn = get_conn()
        cur = dict_cursor(conn)

        query = """
            SELECT
                rb.id,
                rb.transaction_date,
                rb.operator,
                rb.transaction_type,
                rb.amount,
                rb.customer_name,
                rb.mobile_number,
                rb.notes,
                rb.created_at,
                s.id AS sale_id
            FROM recharge_balance rb
            LEFT JOIN sales s
                ON s.recharge_id = rb.id
        """

        conditions = []
        params = []

        if d:
            conditions.append("rb.transaction_date = %s")
            params.append(d)
        elif m:
            conditions.append("""
                rb.transaction_date >= %s
                AND rb.transaction_date < DATE_ADD(
                    %s,
                    INTERVAL 1 MONTH
                )
            """)
            params.extend((f"{m}-01", f"{m}-01"))

        if operator:
            conditions.append("rb.operator = %s")
            params.append(operator)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            ORDER BY rb.transaction_date DESC, rb.id DESC
        """

        cur.execute(query, params)
        rows = cur.fetchall()

        for row in rows:
            if row.get("transaction_date"):
                row["transaction_date"] = row["transaction_date"].isoformat()

            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()

            row["amount"] = to_float(row.get("amount"))

        return jsonify(rows)

    except Exception as e:
        print("RECHARGE GET ERROR:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ===============================================================
# RECHARGE SUMMARY
# ===============================================================

@app.route("/api/recharge/summary", methods=["GET"])
def recharge_summary():
    """
    Recharge balance calculation.

    Opening Balance:
        All ADD transactions before selected date
        minus all RECHARGE transactions before selected date.

    Added:
        Total recharge balance added on selected date.

    Recharge Sales:
        Total recharge amount used on selected date.

    Closing Balance:
        Opening + Added - Recharge Sales

    Therefore:

        Today's Closing
            =
        Tomorrow's Opening
    """

    conn = None
    cur = None

    try:

        selected_date = (
            request.args.get("date")
            or date.today().isoformat()
        )

        operator = (
            request.args.get("operator")
            or ""
        ).strip()

        # Validate date
        datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        )

        conn = get_conn()
        cur = dict_cursor(conn)

        # -------------------------------------------------------
        # Operators
        # -------------------------------------------------------

        operators = (
            [operator]
            if operator
            else RECHARGE_OPERATORS
        )

        result = []

        # -------------------------------------------------------
        # Calculate each operator
        # -------------------------------------------------------

        for op in operators:

            # ===================================================
            # 1. OPENING BALANCE
            # ===================================================
            #
            # Everything BEFORE selected date:
            #
            # ADD       -> +
            # RECHARGE  -> -
            #
            # This automatically carries yesterday's closing
            # balance into today's opening balance.
            #
            cur.execute("""
                SELECT
                    COALESCE(
                        SUM(
                            CASE
                                WHEN transaction_type = 'ADD'
                                    THEN amount

                                WHEN transaction_type = 'RECHARGE'
                                    THEN -amount

                                ELSE 0
                            END
                        ),
                        0
                    ) AS opening_balance

                FROM recharge_balance

                WHERE operator = %s
                  AND transaction_date < %s
            """, (
                op,
                selected_date
            ))

            row = cur.fetchone()

            opening_balance = to_float(
                row["opening_balance"]
            )

            # ===================================================
            # 2. TODAY'S ADDED BALANCE
            # ===================================================

            cur.execute("""
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    ) AS total

                FROM recharge_balance

                WHERE operator = %s
                  AND transaction_type = 'ADD'
                  AND transaction_date = %s
            """, (
                op,
                selected_date
            ))

            row = cur.fetchone()

            added = to_float(
                row["total"]
            )

            # ===================================================
            # 3. TODAY'S RECHARGE SALES
            # ===================================================

            cur.execute("""
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    ) AS total

                FROM recharge_balance

                WHERE operator = %s
                  AND transaction_type = 'RECHARGE'
                  AND transaction_date = %s
            """, (
                op,
                selected_date
            ))

            row = cur.fetchone()

            recharge_sales = to_float(
                row["total"]
            )

            # ===================================================
            # 4. CLOSING BALANCE
            # ===================================================

            closing_balance = (
                opening_balance
                + added
                - recharge_sales
            )

            # ===================================================
            # 5. RESULT
            # ===================================================

            result.append({
                "operator": op,
                "opening_balance": opening_balance,
                "added": added,
                "recharge_sales": recharge_sales,
                "closing_balance": closing_balance
            })

        return jsonify(result)

    except Exception as e:

        print(
            "RECHARGE SUMMARY ERROR:",
            e
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
# ADD OPERATOR RECHARGE BALANCE
# ===============================================================

@app.route("/api/recharge/add", methods=["POST"])
def add_recharge_balance():

    data = request.get_json(
        force=True
    ) or {}

    # -----------------------------------------------------------
    # Selected transaction date
    # -----------------------------------------------------------

    transaction_date = (
        data.get("transaction_date")
        or date.today().isoformat()
    )

    operator = str(
        data.get("operator")
        or ""
    ).strip()

    # -----------------------------------------------------------
    # Validate amount and date
    # -----------------------------------------------------------

    try:

        amount = to_float(
            data.get("amount")
        )

        datetime.strptime(
            transaction_date,
            "%Y-%m-%d"
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid date or amount"
        }), 400

    # -----------------------------------------------------------
    # Validate operator
    # -----------------------------------------------------------

    if operator not in RECHARGE_OPERATORS:

        return jsonify({
            "error": "Invalid operator"
        }), 400

    # -----------------------------------------------------------
    # Validate amount
    # -----------------------------------------------------------

    if amount <= 0:

        return jsonify({
            "error": "Amount must be greater than 0"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()

        cur = conn.cursor()

        # -------------------------------------------------------
        # ADD BALANCE TRANSACTION
        # -------------------------------------------------------

        cur.execute("""
            INSERT INTO recharge_balance
            (
                transaction_date,
                operator,
                transaction_type,
                amount,
                notes
            )
            VALUES
            (
                %s,
                %s,
                'ADD',
                %s,
                %s
            )
        """, (
            transaction_date,
            operator,
            amount,
            data.get("notes")
        ))

        transaction_id = cur.lastrowid

        conn.commit()

        return jsonify({
            "id": transaction_id,
            "message": (
                f"{operator} recharge balance "
                "added successfully"
            )
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "RECHARGE ADD ERROR:",
            e
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
# ADD RECHARGE SALE
# ===============================================================

@app.route("/api/recharge", methods=["POST"])
def add_recharge():

    data = request.get_json(
        force=True
    ) or {}

    # -----------------------------------------------------------
    # Input values
    # -----------------------------------------------------------

    sale_date = (
        data.get("sale_date")
        or date.today().isoformat()
    )

    customer_name = str(
        data.get("customer_name")
        or ""
    ).strip()

    mobile_number = str(
        data.get("mobile_number")
        or ""
    ).strip()

    operator = str(
        data.get("operator")
        or ""
    ).strip()

    # -----------------------------------------------------------
    # Validate amount and date
    # -----------------------------------------------------------

    try:

        amount = to_float(
            data.get("amount")
        )

        datetime.strptime(
            sale_date,
            "%Y-%m-%d"
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid date or amount"
        }), 400

    # -----------------------------------------------------------
    # Validate operator
    # -----------------------------------------------------------

    if operator not in RECHARGE_OPERATORS:

        return jsonify({
            "error": "Invalid operator"
        }), 400

    # -----------------------------------------------------------
    # Validate mobile number
    # -----------------------------------------------------------

    if not mobile_number:

        return jsonify({
            "error": "Mobile number is required"
        }), 400

    # -----------------------------------------------------------
    # Validate amount
    # -----------------------------------------------------------

    if amount <= 0:

        return jsonify({
            "error": "Recharge amount must be greater than 0"
        }), 400

    conn = None
    cur = None

    try:

        conn = get_conn()

        cur = conn.cursor(
            dictionary=True
        )

        # =======================================================
        # CHECK AVAILABLE OPERATOR BALANCE
        # =======================================================
        #
        # Calculate balance up to the selected date BEFORE
        # adding this recharge.
        #
        # ADD       -> +
        # RECHARGE  -> -
        #
        cur.execute("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'ADD'
                                THEN amount

                            WHEN transaction_type = 'RECHARGE'
                                THEN -amount

                            ELSE 0
                        END
                    ),
                    0
                ) AS balance

            FROM recharge_balance

            WHERE operator = %s
              AND transaction_date <= %s
        """, (
            operator,
            sale_date
        ))

        row = cur.fetchone()

        available_balance = to_float(
            row["balance"]
        )

        # -------------------------------------------------------
        # Prevent negative balance
        # -------------------------------------------------------

        if amount > available_balance:

            conn.rollback()

            return jsonify({
                "error": (
                    f"Insufficient {operator} "
                    f"recharge balance. "
                    f"Available balance: "
                    f"₹{available_balance:.2f}"
                )
            }), 400

        # =======================================================
        # SAVE RECHARGE IN RECHARGE BALANCE
        # =======================================================

        cur.execute("""
            INSERT INTO recharge_balance
            (
                transaction_date,
                operator,
                transaction_type,
                amount,
                customer_name,
                mobile_number
            )
            VALUES
            (
                %s,
                %s,
                'RECHARGE',
                %s,
                %s,
                %s
            )
        """, (
            sale_date,
            operator,
            amount,
            customer_name,
            mobile_number
        ))

        recharge_id = cur.lastrowid

        # =======================================================
        # ALSO SAVE IN SALES TABLE
        # =======================================================
        #
        # This makes recharge appear in:
        #
        # Daily Sales
        # Monthly Sales
        #
        cur.execute("""
            INSERT INTO sales
            (
                sale_date,
                customer_name,
                customer_number,
                product_name,
                quantity,
                amount,
                split_amount,
                total_amount,
                sale_type,
                operator,
                recharge_mobile,
                recharge_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                1,
                %s,
                0,
                %s,
                'Recharge',
                %s,
                %s,
                %s
            )
        """, (
            sale_date,
            customer_name,
            mobile_number,
            f"{operator} Recharge",
            amount,
            amount,
            operator,
            mobile_number,
            recharge_id
        ))

        sale_id = cur.lastrowid

        # -------------------------------------------------------
        # Commit both transactions together
        # -------------------------------------------------------

        conn.commit()

        return jsonify({
            "id": sale_id,
            "recharge_id": recharge_id,
            "message": "Recharge sale added successfully"
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "RECHARGE POST ERROR:",
            e
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
# DELETE RECHARGE
# ===============================================================

@app.route(
    "/api/recharge/<int:sale_id>",
    methods=["DELETE"]
)
def delete_recharge(sale_id):

    conn = None
    cur = None

    try:

        conn = get_conn()

        cur = conn.cursor(
            dictionary=True
        )

        # -------------------------------------------------------
        # Find recharge sale
        # -------------------------------------------------------

        cur.execute("""
            SELECT
                id,
                sale_type,
                recharge_id

            FROM sales

            WHERE id = %s

            FOR UPDATE
        """, (
            sale_id,
        ))

        sale = cur.fetchone()

        if not sale:

            return jsonify({
                "error": "Sale not found"
            }), 404

        # -------------------------------------------------------
        # Make sure this is a recharge
        # -------------------------------------------------------

        if sale.get("sale_type") != "Recharge":

            return jsonify({
                "error": (
                    "This sale is not a recharge sale"
                )
            }), 400

        recharge_id = sale.get(
            "recharge_id"
        )

        # -------------------------------------------------------
        # Delete recharge balance transaction
        # -------------------------------------------------------

        if recharge_id:

            cur.execute("""
                DELETE FROM recharge_balance

                WHERE id = %s
                  AND transaction_type = 'RECHARGE'
            """, (
                recharge_id,
            ))

        # -------------------------------------------------------
        # Delete recharge from sales
        # -------------------------------------------------------

        cur.execute("""
            DELETE FROM sales

            WHERE id = %s
              AND sale_type = 'Recharge'
        """, (
            sale_id,
        ))

        conn.commit()

        return jsonify({
            "message": (
                "Recharge deleted and "
                "operator balance restored"
            )
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "RECHARGE DELETE ERROR:",
            e
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
        debug=True,
        host="0.0.0.0",
        port=5000
    )
