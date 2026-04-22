FROM python:3.12.3-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

FROM base AS initdb
CMD ["python", "scripts/init_business_dbs.py"]

FROM base AS web
CMD ["python", "main.py", "web", "--host", "0.0.0.0", "--port", "8000", "--no-reload"]

FROM base AS worker
CMD ["python", "main.py", "worker"]

FROM base AS cron
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
RUN chmod +x /app/crontab_list.sh
CMD ["/app/crontab_list.sh"]