FROM python:3.9

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY ./app .

# 設定環境變數
ENV PYTHONPATH=/app

# 啟動應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 