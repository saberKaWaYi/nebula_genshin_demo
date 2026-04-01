FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt .

Run pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY main.py .

CMD ["python", "main.py"]