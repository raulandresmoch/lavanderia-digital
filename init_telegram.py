# init_simple.py - Versión sin emojis para Windows
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging SIN emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sistema_inicializacion.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verificar_dependencias():
    """Verificar que todas las dependencias estén instaladas."""
    dependencias = [
        'telegram',
        'openai', 
        'flask',
        'flask_sqlalchemy',
        'python_dotenv',  # Cambiado el guión por guión bajo
        'requests'
    ]
    
    faltantes = []
    for dep in dependencias:
        try:
            __import__(dep)
            logger.info(f"OK - {dep}")
        except ImportError:
            faltantes.append(dep)
            logger.error(f"FALTA - {dep}")
    
    if faltantes:
        logger.error(f"Dependencias faltantes: {', '.join(faltantes)}")
        logger.info("Instala con: pip install " + " ".join(faltantes))
        return False
    
    logger.info("TODAS las dependencias están instaladas")
    return True

def verificar_variables_entorno():
    """Verificar variables de entorno."""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram',
        'OPENAI_API_KEY': 'API Key de OpenAI'
    }
    
    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({desc})")
            logger.error(f"FALTA - {var}")
        else:
            logger.info(f"OK - {var}")
    
    if missing:
        logger.error("Variables de entorno faltantes:")
        for var in missing:
            logger.error(f"  - {var}")
        return False
    
    logger.info("Variables de entorno configuradas correctamente")
    return True

async def test_telegram_bot():
    """Probar conexión del bot de Telegram"""
    try:
        from telegram import Bot
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        bot = Bot(token=bot_token)
        
        # Obtener info del bot
        bot_info = await bot.get_me()
        logger.info(f"Bot conectado: @{bot_info.username}")
        logger.info(f"Nombre: {bot_info.first_name}")
        logger.info(f"ID: {bot_info.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error conectando bot: {e}")
        return False

def test_openai():
    """Probar conexión a OpenAI"""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Di 'OK' si funciono correctamente"}],
            max_tokens=10
        )
        
        logger.info("OpenAI conectado correctamente")
        logger.info(f"Respuesta: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        logger.error(f"Error con OpenAI: {e}")
        return False

def test_flask_app():
    """Probar que la app Flask funciona"""
    try:
        from app import create_app
        
        app = create_app()
        logger.info("Flask app creada correctamente")
        
        with app.app_context():
            from app.models import db
            # Verificar conexión a DB
            db.create_all()
            logger.info("Base de datos inicializada")
        
        return True
        
    except Exception as e:
        logger.error(f"Error con Flask: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    logger.info("INICIANDO PRUEBAS DEL SISTEMA")
    logger.info("=" * 50)
    
    # Lista de pruebas
    pruebas = [
        ("Verificar dependencias", verificar_dependencias),
        ("Verificar variables de entorno", verificar_variables_entorno),
        ("Probar Flask app", test_flask_app),
        ("Probar OpenAI", test_openai),
        ("Probar bot de Telegram", test_telegram_bot),
    ]
    
    # Ejecutar pruebas
    resultados = []
    for nombre, funcion in pruebas:
        logger.info(f"\nEjecutando: {nombre}")
        logger.info("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(funcion):
                resultado = await funcion()
            else:
                resultado = funcion()
            
            resultados.append((nombre, resultado))
            
            if resultado:
                logger.info(f"EXITOSO - {nombre}")
            else:
                logger.error(f"FALLIDO - {nombre}")
                
        except Exception as e:
            logger.error(f"ERROR en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Mostrar resumen
    logger.info("\n" + "=" * 50)
    logger.info("RESUMEN DE PRUEBAS")
    logger.info("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        status = "EXITOSO" if resultado else "FALLIDO"
        logger.info(f"{status:<10} - {nombre}")
        if resultado:
            exitosos += 1
    
    logger.info(f"\nResultado: {exitosos}/{len(resultados)} pruebas exitosas")
    
    if exitosos == len(resultados):
        logger.info("SISTEMA LISTO PARA USAR!")
        mostrar_instrucciones()
    else:
        logger.error("Hay errores que corregir.")

def mostrar_instrucciones():
    """Mostrar instrucciones de uso"""
    instrucciones = """
===============================================
         SISTEMA LISTO PARA USAR!
===============================================

PROXIMOS PASOS:

1. EJECUTAR SERVIDOR WEB:
   python run.py

2. EJECUTAR BOT DE TELEGRAM:
   python -c "import asyncio; from telegram_service import telegram_service; asyncio.run(telegram_service.inicializar_bot())"

3. PROBAR FUNCIONALIDADES:
   - Web: http://localhost:5000
   - Admin: http://localhost:5000/admin  
   - Telegram: Busca tu bot en Telegram

4. GENERAR RUTAS:
   - Ve al panel admin
   - Crea algunos pedidos de prueba
   - Genera rutas automáticas

El sistema está funcionando correctamente!
"""
    
    print(instrucciones)

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar pruebas
    asyncio.run(main())