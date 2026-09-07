# Global UPI

Global UPI is a Django-based digital wallet application for managing UPI users, wallets, transfers, and support requests across currencies.

## Features

- User registration, login, profile completion, and password changes
- Optional Google authentication through `django-allauth`
- UPI IDs and QR code generation
- Multi-currency wallets and balance management
- Money transfers, conversion previews, deposits, withdrawals, and payment requests
- Bank account management
- Admin dashboard with payment approval, user blocking, and support ticket management

## Project Structure

The Django project is located in the `global_upi/` directory.

```text
global_upi/
|-- manage.py
|-- global_upi/       # Django project configuration
|-- upi/              # Application models, views, URLs, and migrations
|-- media/            # Uploaded QR codes and media files
`-- db.sqlite3        # Local development database
```

## Requirements

- Python 3.10+
- Django
- django-allauth
- Pillow

## Local Setup

From the repository root:

```bash
cd global_upi
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install django django-allauth Pillow
```

Apply migrations and create an administrator:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. The Django admin is available at `http://127.0.0.1:8000/admin/`.

## Configuration Notes

Before deploying, move `SECRET_KEY` and other credentials to environment variables, set `DEBUG = False`, configure `ALLOWED_HOSTS`, and use a production database and static-file server. Do not commit real OAuth credentials or production database files.

## License

No license has been specified for this project yet.