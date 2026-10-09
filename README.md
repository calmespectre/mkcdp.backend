# MKCDP Backend

Production Django backend for the MKCDP NGO platform (donations, gift orders, beneficiaries, volunteers, partnerships, safeguarding, content).

## Requirements

- Python 3.11+
- PostgreSQL 13+
- Redis 6+

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with real credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver