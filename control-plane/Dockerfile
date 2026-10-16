FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8100

CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && if [ -n \"$BOOTSTRAP_ADMIN_PASSWORD\" ]; then python manage.py bootstrap_control_plane --org-name \"${BOOTSTRAP_ORG_NAME:-PlanetMind Org}\" --org-slug \"${BOOTSTRAP_ORG_SLUG:-planetmind-org}\" --admin-username \"${BOOTSTRAP_ADMIN_USERNAME:-orgadmin}\" --admin-email \"${BOOTSTRAP_ADMIN_EMAIL:-admin@planetmind.local}\" --admin-password \"$BOOTSTRAP_ADMIN_PASSWORD\"; fi && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8100} --workers 2 --timeout 120"]
