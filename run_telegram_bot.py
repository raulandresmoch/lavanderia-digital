# run_telegram_bot.py
"""
Script para ejecutar el bot de Telegram de manera independiente.
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Función principal para ejecutar el bot."""
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN no está configurado en el archivo .env")
        logger.info("💡 Configura tu token en el archivo .env:")
        logger.info("   TELEGRAM_BOT_TOKEN=tu_token_aqui")
        return
    
    try:
        # Importar y configurar la aplicación Flask
        from app import app, db
        
        # Importar servicios
        from telegram_service import TelegramService
        from email_service import EmailService
        from rutas_service import inicializar_rutas_service
        
        with app.app_context():
            logger.info("🚀 Inicializando bot de Telegram...")
            
            # Inicializar servicios
            email_service = EmailService()
            telegram_service = TelegramService()
            rutas_service = inicializar_rutas_service(db.session, telegram_service, email_service)
            
            # Verificar conexión del bot
            bot_info = await telegram_service.application.bot.get_me()
            logger.info(f"✅ Bot conectado: @{bot_info.username}")
            logger.info(f"📝 Nombre: {bot_info.first_name}")
            logger.info(f"🆔 ID: {bot_info.id}")
            
            # Configurar webhook o polling
            logger.info("🔄 Iniciando polling...")
            
            # Inicializar aplicación
            await telegram_service.application.initialize()
            await telegram_service.application.start()
            
            # Notificar a admins que el bot está activo
            try:
                await telegram_service.notificar_admins(
                    f"🤖 Bot de lavandería iniciado\n"
                    f"⏰ Hora: {asyncio.get_event_loop().time()}\n"
                    f"🆔 Bot: @{bot_info.username}\n"
                    f"✅ Estado: Activo y listo para recibir comandos"
                )
            except Exception as e:
                logger.warning(f"No se pudo notificar a admins: {e}")
            
            logger.info("🎯 Bot ejecutándose... Presiona Ctrl+C para detener")
            
            # Ejecutar polling
            await telegram_service.application.updater.start_polling(
                bootstrap_retries=3,
                timeout=30,
                drop_pending_updates=True
            )
            
            # Mantener el bot corriendo
            await asyncio.Event().wait()
            
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo bot...")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando bot: {e}")
        
    finally:
        # Cleanup
        try:
            await telegram_service.application.stop()
            logger.info("✅ Bot detenido correctamente")
        except:
            pass

def verificar_configuracion():
    """Verificar que la configuración esté completa."""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'OPENAI_API_KEY',
        'EMAIL_USER',
        'EMAIL_PASSWORD'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error("❌ Variables de entorno faltantes:")
        for var in missing:
            logger.error(f"   - {var}")
        logger.info("\n💡 Configura estas variables en tu archivo .env")
        return False
    
    return True

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar configuración
    if not verificar_configuracion():
        sys.exit(1)
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    try:
        # Ejecutar bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 ¡Hasta luego!")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)