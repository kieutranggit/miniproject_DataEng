import requests
from dotenv import load_dotenv
import os

load_dotenv()  # đọc file .env

webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

data = {
    "content": "🎉 Test kết nối thành công! Bot job alert đã sẵn sàng."
}

response = requests.post(webhook_url, json=data)
print(f"Status code: {response.status_code}")