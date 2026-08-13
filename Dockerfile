FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN DJANGO_SETTINGS_MODULE=config.settings.demo_seed \
    VANTA_DEMO_SEED_PATH=/app/demo-seed/vanta-demo-0.22.2-1.sqlite3 \
    uv run --no-sync python manage.py build_vanta_demo_seed --force

RUN DJANGO_SETTINGS_MODULE=config.settings.demo \
    DJANGO_SECRET_KEY=build-time-placeholder \
    DJANGO_ALLOWED_HOSTS=localhost \
    DJANGO_CSRF_TRUSTED_ORIGINS=https://localhost \
    DATABASE_URL=postgres://build:build@localhost:5432/build \
    uv run --no-sync python manage.py collectstatic --noinput

RUN DJANGO_SETTINGS_MODULE=config.settings.demo_seed \
    VANTA_DEMO_STATIC_ROOT=/app/demo-staticfiles \
    VANTA_DEMO_SEED_PATH=/app/demo-seed/vanta-demo-0.22.2-1.sqlite3 \
    uv run --no-sync python manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('PORT', '8000'); host = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')[0].strip() or 'localhost'; path = '/readyz/' if os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings.demo' else '/healthz/'; request = urllib.request.Request(f'http://127.0.0.1:{port}{path}', headers={'Host': host, 'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(request, timeout=4).read()"

CMD ["sh", "-c", "uv run --no-sync python manage.py check --tag vanta_demo && uv run --no-sync python manage.py migrate --noinput && uv run --no-sync gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-2} --max-requests ${GUNICORN_MAX_REQUESTS:-1000} --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100}"]
