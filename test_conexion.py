import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_telegram_connection():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        print("🔄 Probando conexión a Telegram...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Conexión exitosa!")
            print(f"Bot: @{data['result']['username']}")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_telegram_connection()