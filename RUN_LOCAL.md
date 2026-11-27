# Run the solar demo locally (Windows 10/11, PowerShell 5.1, MySQL 8)

This is the `demo/solar-epc` branch: the product plus a **fictional** solar EPC
company, "Helios Grid Energy Pvt Ltd" (demo data — every name, number and
document is invented). Every command below is one line, typed in PowerShell 5.1
from the folder named in step 2. Nothing asks a question.

## 1. What you need first

- Python 3.10 or newer: `python --version`
- Git: `git --version`
- MySQL 8 server running locally (the Windows service is usually `MySQL80`): `Get-Service MySQL80`
- A MySQL login that may create a database (often `root`). You need its password for step 4.

If `Get-Service MySQL80` says *Stopped*, start it from an **Administrator** PowerShell: `Start-Service MySQL80`

## 2. Get the code

```powershell
git clone https://github.com/Manas236/Sample.git
```
```powershell
cd Sample
```
```powershell
git checkout demo/solar-epc
```

## 3. Python environment

The commands call the venv's own Python, so no activation (and no execution-policy change) is needed.

```powershell
python -m venv .venv
```
```powershell
.\.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt
```
```powershell
.\.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check pytest==9.1.1
```

## 4. Settings (`.env`)

```powershell
Copy-Item .env.example .env
```

Set the five values below. Replace `YOUR_MYSQL_PASSWORD` first; the other four can be pasted as they are. Each line rewrites one setting in place (ASCII, so the file gets no byte-order mark).

```powershell
(Get-Content .env) -replace '^DB_PASSWORD=.*', 'DB_PASSWORD=YOUR_MYSQL_PASSWORD' | Set-Content -Encoding ascii .env
```
```powershell
(Get-Content .env) -replace '^DB_USER=.*', 'DB_USER=root' | Set-Content -Encoding ascii .env
```
```powershell
(Get-Content .env) -replace '^DB_NAME=.*', 'DB_NAME=qms_demo' | Set-Content -Encoding ascii .env
```
```powershell
(Get-Content .env) -replace '^QMS_DEMO_DATA=.*', 'QMS_DEMO_DATA=true' | Set-Content -Encoding ascii .env
```
```powershell
(Get-Content .env) -replace '^QMS_SECRET_KEY=.*', ('QMS_SECRET_KEY=' + [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')) | Set-Content -Encoding ascii .env
```

Check them (the password line is left out on purpose):

```powershell
Select-String -Path .env -Pattern '^(DB_USER|DB_NAME|QMS_DEMO_DATA|QMS_PORT)='
```

`DB_NAME` **must** be `qms_demo`. The seed tool refuses any other database name, so it can never drop or fill a real one.

## 5. Build the demo company

```powershell
.\.venv\Scripts\python.exe tools\seed_demo.py --reset
```

`--reset` takes a dated backup of `qms_demo` into `backups\` (when the database already exists), drops it, creates it empty, and seeds the demo through the app's own pages. It needs `mysqldump`, which ships with MySQL 8 (`C:\Program Files\MySQL\MySQL Server 8.0\bin`); the tool finds it there. On a brand-new machine with no `qms_demo` yet, there is nothing to back up and it goes straight to creating it.

Running it again **without** `--reset` changes nothing and prints the same record counts:

```powershell
.\.venv\Scripts\python.exe tools\seed_demo.py
```

Expected counts: quotations 2, purchases 5, purchase_orders 2, specs 16, boqs 3, ra_bills 4, receipts 2, delivery_challans 4, measurements 1, projects 2, charges 5, employees 6, attendance 270, attachments 5, addresses 11, settings 8, users 7, roles 7.

## 6. Start the app

```powershell
.\.venv\Scripts\python.exe app.py
```

Open the address it prints (default **http://127.0.0.1:5000**; `QMS_PORT` in `.env` changes it). Stop it with `Ctrl+C`.

`app.py` is the development server and listens on this computer only. Do not expose it to a network.

## 7. Demo logins (one per role)

| Username | Password | Role | Use it to show |
|---|---|---|---|
| `owner` | `Helios-Owner-26` | Owner | everything — use this for the demo |
| `director` | `Helios-Director-26` | Director | admin without role editing |
| `operations` | `Helios-Ops-26` | Operation Head | BOQ, dispatch, RA bills, site |
| `hr` | `Helios-HR-26` | HR | employees and attendance only |
| `sales` | `Helios-Sales-26` | Sales Manager | quotations and customers |
| `purchase` | `Helios-Purchase-26` | Purchase Manager | inquiries, POs, vendors |
| `accounts` | `Helios-Accounts-26` | Accountant | invoices and receipts |

⚠ **These passwords are public** (they are in this file in a public repository). They are for a local demo database only. Never put this database where anyone else can reach it.

## 8. Run the tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite does **not** read your `.env` and never touches MySQL; it runs on an in-memory store. Expected on this branch: **0 failed** (REPORT.md has the exact counts).

## 9. Before the demo, and after

- Fresh data just before you present: `.\.venv\Scripts\python.exe tools\seed_demo.py --reset`
- Rebrand to the prospect: DEMO_SCRIPT.md, "Rebrand before the demo".
- The backups the reset takes are in `backups\` (ignored by git). Delete old ones when you no longer need them.

## 10. If something goes wrong

- `REFUSED: DB_NAME is 'qms'` — step 4: set `DB_NAME=qms_demo`.
- `REFUSED: QMS_DEMO_DATA is not true` — step 4: set `QMS_DEMO_DATA=true`.
- `REFUSED: persistence is not live` — MySQL is not running or the password is wrong: `Get-Service MySQL80`, then check `DB_USER` / `DB_PASSWORD`.
- `mysqldump not found` — add `C:\Program Files\MySQL\MySQL Server 8.0\bin` to PATH for this window: `$env:Path += ';C:\Program Files\MySQL\MySQL Server 8.0\bin'`
- Port already in use — pick another for this window: `$env:QMS_PORT = '5050'`, then start the app again.
