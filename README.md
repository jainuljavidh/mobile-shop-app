# Shop Ledger — Mobile Shop Sales Management

A single-page web app for a mobile phone shop to record **sales, expenses,
purchases, customer enquiries, and repairs**, with daily and monthly totals.
Backend: **Python (Flask)**. Database: **MySQL**.

The Repairs section tracks a device through a status workflow:
**Received → In Progress → Completed → Delivered to Customer** — just pick
the new status from the dropdown on that row and it saves immediately.

---

## 1. What you get

```
mobileshop/
├── app.py                 # Flask app + REST API
├── requirements.txt
├── database/
│   └── schema.sql         # MySQL tables
├── templates/
│   └── index.html         # the single page
└── static/
    ├── css/style.css
    └── js/app.js
```

## 2. Prerequisites

- Python 3.9+
- MySQL Server 8.x (or MariaDB 10.5+) running locally or on a server
- `pip`

## 3. Set up the database

Log into MySQL and run the schema file. This creates the `mobile_shop`
database and its four tables (`sales`, `expenses`, `purchases`, `enquiries`).

```bash
mysql -u root -p < database/schema.sql
```

**Already set up the database before?** Just add the new `repairs` table
without touching your existing data:

```bash
mysql -u root -p < database/migration_add_repairs.sql
```

If you'd rather create a dedicated (non-root) MySQL user for the app:

```sql
CREATE USER 'shopapp'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON mobile_shop.* TO 'shopapp'@'localhost';
FLUSH PRIVILEGES;
```

## 4. Configure the app's DB credentials

`app.py` reads these environment variables (falling back to the defaults
shown if not set):

| Variable      | Default       |
|---------------|---------------|
| `DB_HOST`     | `localhost`   |
| `DB_PORT`     | `3306`        |
| `DB_USER`     | `root`        |
| `DB_PASSWORD` | *(empty)*     |
| `DB_NAME`     | `mobile_shop` |

Easiest way to set them for a local run:

```bash
export DB_USER=shopapp
export DB_PASSWORD=choose-a-strong-password
export DB_NAME=mobile_shop
```

(On Windows PowerShell: `$env:DB_USER="shopapp"`, etc.)

## 5. Install dependencies and run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in a browser. It also works fine on a phone's
browser on the same network — use the machine's local IP instead of
`localhost` (e.g. `http://192.168.1.20:5000`).

## 6. Using the app

- **Day view / Month view** toggle at the top switches every section
  (Sales, Expenses, Purchases, Enquiries) between showing a single day's
  records or a whole month's records.
- Pick a date or month with the fields next to the toggle.
- The summary cards at the top always show **today's** sales/expenses/
  purchases plus **this month's** sales, expenses, and enquiry count,
  based on the selected date.
- Each section has an inline form to add a record, a table of existing
  records for the selected day/month, and a running total at the bottom.
- Click **Delete** on any row to remove it (asks for confirmation first).

## 7. Notes on going further

- **Editing rows**: the API supports `PUT` for sales/expenses/purchases if
  you want to add inline editing later (delete-and-re-add works fine for now).
- **Multiple users**: this app has no login system. If your friend wants
  staff accounts or access control, that would need to be added.
- **Backups**: since everything lives in MySQL, a simple `mysqldump` on a
  schedule is enough to back up the shop's data:
  ```bash
  mysqldump -u root -p mobile_shop > backup_$(date +%F).sql
  ```
- **Hosting**: to make this reachable outside the local network, deploy
  Flask behind a proper WSGI server (e.g. gunicorn) and a managed MySQL
  instance, rather than `python app.py`'s built-in dev server.
