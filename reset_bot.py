import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')

def reset_bot():
    print("🔄 Reseteando bot...")
    
    # 1. Eliminar webhook si existe
    webhook_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(webhook_url)
    print(f"Webhook eliminado: {response.json()}")
    
    # 2. Obtener updates pendientes y marcarlos como leídos
    updates_url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(updates_url)
    data = response.json()
    
    if data.get('result'):
        # Marcar todos como leídos
        last_update_id = data['result'][-1]['update_id'] + 1
        clear_url = f"https://api.telegram.org/bot{token}/getUpdates"
        requests.get(clear_url, params={'offset': last_update_id})
        print(f"✅ {len(data['result'])} updates pendientes eliminados")
    
    # 3. Verificar bot
    me_url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(me_url)
    bot_info = response.json()
    print(f"✅ Bot verificado: @{bot_info['result']['username']}")

if __name__ == "__main__":
    reset_bot()