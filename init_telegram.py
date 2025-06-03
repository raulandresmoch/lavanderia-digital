# init_sistema_completo.py
"""
Script para inicializar completamente el sistema de lavandería digital
con todas las funcionalidades de Telegram, emails y rutas.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sistema_inicializacion.log'),
        logging.StreamHandler()
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
        'flask_mail',
        'python-dotenv',
        'requests',
        'geopy'
    ]
    
    faltantes = []
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            faltantes.append(dep)
    
    if faltantes:
        logger.error(f"Dependencias faltantes: {', '.join(faltantes)}")
        logger.info("Instala con: pip install " + " ".join(faltantes))
        return False
    
    logger.info("✅ Todas las dependencias están instaladas")
    return True

def verificar_variables_entorno():
    """Verificar variables de entorno."""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram',
        'OPENAI_API_KEY': 'API Key de OpenAI',
        'EMAIL_USER': 'Usuario del email SMTP',
        'EMAIL_PASSWORD': 'Contraseña del email SMTP',
        'EMAIL_SMTP_SERVER': 'Servidor SMTP (ej: smtp.gmail.com)',
        'EMAIL_SMTP_PORT': 'Puerto SMTP (ej: 587)',
        'SECRET_KEY': 'Clave secreta de Flask'
    }
    
    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({desc})")
    
    if missing:
        logger.error("Variables de entorno faltantes:")
        for var in missing:
            logger.error(f"  - {var}")
        return False
    
    logger.info("✅ Variables de entorno configuradas")
    return True

def crear_estructura_directorios():
    """Crear estructura de directorios necesaria."""
    directorios = [
        'logs',
        'templates/admin',
        'templates/emails',
        'static/css',
        'static/js',
        'instance'
    ]
    
    for directorio in directorios:
        os.makedirs(directorio, exist_ok=True)
    
    logger.info("✅ Estructura de directorios creada")
    return True

def inicializar_base_datos():
    """Inicializar la base de datos."""
    try:
        from app import app, db
        
        with app.app_context():
            # Crear todas las tablas
            db.create_all()
            
            # Verificar que las tablas se crearon
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            logger.info(f"✅ Base de datos inicializada con {len(tables)} tablas")
            logger.info(f"Tablas: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        return False

async def inicializar_servicios():
    """Inicializar todos los servicios."""
    try:
        from app import app, db
        from telegram_service import TelegramService
        from email_service import EmailService
        from rutas_service import inicializar_rutas_service
        
        with app.app_context():
            # Inicializar servicios
            logger.info("Inicializando servicios...")
            
            # Email Service
            email_service = EmailService()
            logger.info("✅ Servicio de email inicializado")
            
            # Telegram Service
            telegram_service = TelegramService()
            logger.info("✅ Servicio de Telegram inicializado")
            
            # Rutas Service
            rutas_service = inicializar_rutas_service(db.session, telegram_service, email_service)
            logger.info("✅ Servicio de rutas inicializado")
            
            # Verificar conexión del bot
            try:
                bot_info = await telegram_service.application.bot.get_me()
                logger.info(f"✅ Bot conectado: @{bot_info.username}")
            except Exception as e:
                logger.error(f"❌ Error conectando bot: {e}")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error inicializando servicios: {e}")
        return False

def crear_datos_demo():
    """Crear datos de demostración."""
    try:
        from app import app, db
        from models import Usuario, DireccionUsuario, Pedido, TipoPrenda, Admin
        from datetime import datetime, timedelta
        
        with app.app_context():
            # Verificar si ya existen datos
            if Usuario.query.count() > 0:
                logger.info("✅ Ya existen datos en la base de datos")
                return True
            
            logger.info("Creando datos de demostración...")
            
            # Crear admin
            admin = Admin(
                username='admin',
                email='admin@lavanderia.com',
                chat_id_telegram='123456789'  # Reemplazar con tu chat_id
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Crear tipos de prenda
            tipos_prenda = [
                TipoPrenda(nombre='Camisa', precio=15.0),
                TipoPrenda(nombre='Pantalón', precio=20.0),
                TipoPrenda(nombre='Vestido', precio=25.0),
                TipoPrenda(nombre='Chaqueta', precio=30.0),
                TipoPrenda(nombre='Blusa', precio=18.0),
            ]
            for tipo in tipos_prenda:
                db.session.add(tipo)
            
            # Crear usuarios demo
            usuarios_demo = [
                {
                    'nombre': 'María González',
                    'email': 'maria@ejemplo.com',
                    'telefono': '+525512345678',
                    'direcciones': [
                        {
                            'alias': 'Casa',
                            'direccion': 'Av. Insurgentes Sur 1234, Roma Norte, CDMX',
                            'lat': 19.4150, 'lng': -99.1620, 'cp': '06700'
                        }
                    ]
                },
                {
                    'nombre': 'Carlos Hernández',
                    'email': 'carlos@ejemplo.com',
                    'telefono': '+525587654321',
                    'direcciones': [
                        {
                            'alias': 'Oficina',
                            'direccion': 'Polanco, Miguel Hidalgo, CDMX',
                            'lat': 19.4326, 'lng': -99.1980, 'cp': '11560'
                        }
                    ]
                },
                {
                    'nombre': 'Ana López',
                    'email': 'ana@ejemplo.com',
                    'telefono': '+525511223344',
                    'direcciones': [
                        {
                            'alias': 'Casa',
                            'direccion': 'Coyoacán, CDMX',
                            'lat': 19.3467, 'lng': -99.1618, 'cp': '04000'
                        }
                    ]
                }
            ]
            
            for usuario_data in usuarios_demo:
                usuario = Usuario(
                    nombre=usuario_data['nombre'],
                    email=usuario_data['email'],
                    telefono=usuario_data['telefono']
                )
                db.session.add(usuario)
                db.session.flush()
                
                for dir_data in usuario_data['direcciones']:
                    direccion = DireccionUsuario(
                        usuario_id=usuario.id,
                        alias=dir_data['alias'],
                        direccion_completa=dir_data['direccion'],
                        latitud=dir_data['lat'],
                        longitud=dir_data['lng'],
                        ciudad='Ciudad de México',
                        codigo_postal=dir_data['cp']
                    )
                    db.session.add(direccion)
                    db.session.flush()
                    
                    # Crear pedido demo
                    pedido = Pedido(
                        usuario_id=usuario.id,
                        direccion_id=direccion.id,
                        tipo_servicio='lavado_secado',
                        total=150.00,
                        estado='confirmado',
                        fecha_recoleccion=datetime.now() + timedelta(days=1),
                        notas=f'Pedido demo para {usuario.nombre}'
                    )
                    db.session.add(pedido)
            
            db.session.commit()
            logger.info("✅ Datos de demostración creados")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creando datos demo: {e}")
        db.session.rollback()
        return False

def crear_archivos_configuracion():
    """Crear archivos de configuración necesarios."""
    try:
        # Crear .env.example si no existe
        env_example = """# Configuración del sistema de lavandería digital

# Bot de Telegram
TELEGRAM_BOT_TOKEN=tu_token_aqui

# OpenAI API
OPENAI_API_KEY=tu_api_key_aqui

# Email SMTP
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_contraseña_app
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Flask
SECRET_KEY=tu_clave_secreta_muy_segura
FLASK_ENV=development

# Base de datos
DATABASE_URL=sqlite:///lavanderia.db

# Configuración de la aplicación
ZONA_COBERTURA_KM=25
CENTRO_OPERACIONES_LAT=19.4326
CENTRO_OPERACIONES_LNG=-99.1332
"""
        
        if not os.path.exists('.env.example'):
            with open('.env.example', 'w', encoding='utf-8') as f:
                f.write(env_example)
            logger.info("✅ Archivo .env.example creado")
        
        # Crear requirements.txt si no existe
        requirements = """Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Mail==0.9.1
python-telegram-bot==20.7
openai==1.3.5
python-dotenv==1.0.0
requests==2.31.0
geopy==2.4.0
"""
        
        if not os.path.exists('requirements.txt'):
            with open('requirements.txt', 'w') as f:
                f.write(requirements)
            logger.info("✅ Archivo requirements.txt creado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando archivos de configuración: {e}")
        return False

async def probar_sistema():
    """Probar que el sistema funcione correctamente."""
    try:
        from test_telegram_system import main as test_main
        
        logger.info("🧪 Ejecutando pruebas del sistema...")
        await test_main()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en pruebas del sistema: {e}")
        return False

def mostrar_instrucciones_finales():
    """Mostrar instrucciones finales al usuario."""
    instrucciones = """
🎉 ¡SISTEMA INICIALIZADO EXITOSAMENTE!

📋 PRÓXIMOS PASOS:

1. 🔧 Configurar variables de entorno:
   - Copia .env.example a .env
   - Completa todas las variables requeridas

2. 🤖 Configurar Bot de Telegram:
   - Ve a @BotFather en Telegram
   - Crea un nuevo bot y obtén el token
   - Agrega el token a tu archivo .env

3. 🧠 Configurar OpenAI:
   - Ve a https://platform.openai.com/
   - Obtén tu API key
   - Agrégala a tu archivo .env

4. 📧 Configurar Email:
   - Usa Gmail con contraseña de aplicación
   - O configura otro servidor SMTP

5. 🚀 Ejecutar el sistema:
   - python app.py (para el servidor web)
   - python init_telegram.py (para el bot)

📱 FUNCIONALIDADES DISPONIBLES:
   ✅ Sistema completo de usuarios y direcciones
   ✅ Cotización automática con mapas
   ✅ Panel administrativo
   ✅ Bot de Telegram para repartidores
   ✅ Emails automáticos
   ✅ Rutas optimizadas con IA
   ✅ Tracking en tiempo real

🌐 URLs DEL SISTEMA:
   - Aplicación web: http://localhost:5000
   - Admin panel: http://localhost:5000/admin
   - Telegram: @tu_bot_name

📖 DOCUMENTACIÓN:
   - Revisa los comentarios en el código
   - Usa /help en el bot de Telegram
   - Consulta los logs en la carpeta logs/

¡Tu lavandería digital está lista para funcionar! 🧺✨
"""
    
    print(instrucciones)
    logger.info("✅ Instrucciones finales mostradas")

async def main():
    """Función principal de inicialización."""
    logger.info("🚀 Iniciando configuración del sistema de lavandería digital...")
    
    # Lista de pasos de inicialización
    pasos = [
        ("Verificar dependencias", verificar_dependencias),
        ("Verificar variables de entorno", verificar_variables_entorno),
        ("Crear estructura de directorios", crear_estructura_directorios),
        ("Crear archivos de configuración", crear_archivos_configuracion),
        ("Inicializar base de datos", inicializar_base_datos),
        ("Crear datos de demostración", crear_datos_demo),
        ("Inicializar servicios", inicializar_servicios),
    ]
    
    # Ejecutar pasos
    resultados = []
    for nombre, funcion in pasos:
        logger.info(f"\n📋 Ejecutando: {nombre}")
        try:
            if asyncio.iscoroutinefunction(funcion):
                resultado = await funcion()
            else:
                resultado = funcion()
            resultados.append((nombre, resultado))
            
            if not resultado:
                logger.error(f"❌ Falló: {nombre}")
                break
                
        except Exception as e:
            logger.error(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
            break
    
    # Mostrar resumen
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMEN DE INICIALIZACIÓN")
    logger.info("="*50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        status = "✅ EXITOSO" if resultado else "❌ FALLIDO"
        logger.info(f"{status:<12} - {nombre}")
        if resultado:
            exitosos += 1
    
    logger.info(f"\n🎯 Resultado: {exitosos}/{len(resultados)} pasos completados")
    
    if exitosos == len(resultados):
        logger.info("🎉 ¡Inicialización completada exitosamente!")
        mostrar_instrucciones_finales()
    else:
        logger.error("⚠️ La inicialización tuvo errores. Revisa los logs.")
        logger.info("💡 Tip: Asegúrate de tener todas las variables de entorno configuradas")

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar inicialización
    asyncio.run(main())