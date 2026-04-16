FROM python:3.12.3-slim

RUN apt-get update && apt-get install -y cron

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN chmod +x /app/crontab_list.sh

CMD ["/app/crontab_list.sh"]