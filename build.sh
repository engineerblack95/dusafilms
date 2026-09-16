#!/usr/bin/env bash
# ==================================================
# Render build script
# ==================================================
set -o errexit  # exit on error

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Applying database migrations..."
python manage.py migrate

echo "==> Creating superuser (if requested)..."
if [[ "$CREATE_SUPERUSER" == "true" ]]; then
  python manage.py createsuperuser --no-input || true
fi

echo "==> Build complete."