import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from typing import List, Dict, Optional
from jinja2 import Template

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_from = os.getenv('EMAIL_FROM', self.email_user)
        
    def enviar_email(self, 
                     destinatario: str, 
                     asunto: str, 
                     contenido_html: str, 
                     contenido_texto: str = None,
                     adjuntos: List[str] = None) -> bool:
        """Enviar email con contenido HTML y texto"""
        try:
            # Crear mensaje
            mensaje = MIMEMultipart('alternative')
            mensaje['From'] = self.email_from
            mensaje['To'] = destinatario
            mensaje['Subject'] = asunto
            
            # Agregar contenido texto plano si no se proporciona
            if not contenido_texto:
                contenido_texto = self.html_a_texto(contenido_html)
            
            # Agregar partes del mensaje
            parte_texto = MIMEText(contenido_texto, 'plain', 'utf-8')
            parte_html = MIMEText(contenido_html, 'html', 'utf-8')
            
            mensaje.attach(parte_texto)
            mensaje.attach(parte_html)
            
            # Agregar adjuntos si los hay
            if adjuntos:
                for archivo in adjuntos:
                    self.agregar_adjunto(mensaje, archivo)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                servidor.starttls()
                servidor.login(self.email_user, self.email_password)
                servidor.send_message(mensaje)
            
            logger.info(f"Email enviado exitosamente a {destinatario}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {destinatario}: {e}")
            return False
    
    def agregar_adjunto(self, mensaje: MIMEMultipart, ruta_archivo: str):
        """Agregar adjunto al email"""
        try:
            with open(ruta_archivo, 'rb') as archivo:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(archivo.read())
                encoders.encode_base64(parte)
                
                nombre_archivo = os.path.basename(ruta_archivo)
                parte.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {nombre_archivo}'
                )
                
                mensaje.attach(parte)
                
        except Exception as e:
            logger.error(f"Error agregando adjunto {ruta_archivo}: {e}")
    
    def html_a_texto(self, html: str) -> str:
        """Convertir HTML básico a texto plano"""
        import re
        # Remover tags HTML básicos
        texto = re.sub('<[^<]+?>', '', html)
        # Limpiar espacios extras
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()
    
    def email_confirmacion_pedido(self, pedido: Dict, usuario: Dict) -> bool:
        """Enviar email de confirmación de pedido"""
        template_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .pedido-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .item { border-bottom: 1px solid #eee; padding: 10px 0; }
        .total { background: #e9ecef; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; }
        .footer { background: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚚 Lavandería Digital</h1>
        <h2>¡Pedido Confirmado!</h2>
    </div>
    
    <div class="content">
        <p>Hola <strong>{{ usuario.nombre }}</strong>,</p>
        
        <p>¡Gracias por confiar en nosotros! Tu pedido ha sido confirmado y ya está en proceso.</p>
        
        <div class="pedido-info">
            <h3>📋 Detalles del Pedido #{{ pedido.id }}</h3>
            <p><strong>📅 Fecha de Recolección:</strong> {{ pedido.fecha_recoleccion }}</p>
            <p><strong>📅 Fecha de Entrega:</strong> {{ pedido.fecha_entrega }}</p>
            <p><strong>📍 Dirección:</strong> {{ pedido.direccion }}</p>
            {% if pedido.notas %}
            <p><strong>📝 Notas:</strong> {{ pedido.notas }}</p>
            {% endif %}
        </div>
        
        <h3>🧺 Prendas Solicitadas:</h3>
        {% for item in pedido.items %}
        <div class="item">
            <strong>{{ item.tipo_prenda }}</strong> - {{ item.cantidad }} kg - ${{ item.subtotal }}
        </div>
        {% endfor %}
        
        <div class="total">
            💰 Total: ${{ pedido.precio_total }}
        </div>
        
        <h3>⏰ Horarios de Servicio:</h3>
        <ul>
            <li><strong>Recolección:</strong> Mañana (9:00 AM - 12:00 PM)</li>
            <li><strong>Entrega:</strong> Tarde (2:00 PM - 6:00 PM)</li>
        </ul>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="{{ url_tracking }}" class="btn">🔍 Rastrear mi Pedido</a>
        </p>
        
        <h3>📞 ¿Necesitas Ayuda?</h3>
        <p>Si tienes alguna pregunta, no dudes en contactarnos:</p>
        <ul>
            <li>📧 Email: info@lavanderiadigital.com</li>
            <li>📱 WhatsApp: +52 55 1234 5678</li>
            <li>🕐 Horario: Lunes a Sábado, 8:00 AM - 8:00 PM</li>
        </ul>
    </div>
    
    <div class="footer">
        <p>© {{ año }} Lavandería Digital. Todos los derechos reservados.</p>
        <p>Este es un email automático, por favor no respondas a esta dirección.</p>
    </div>
</body>
</html>
        """
        
        try:
            template = Template(template_html)
            
            # Preparar datos para el template
            datos = {
                'usuario': usuario,
                'pedido': pedido,
                'año': datetime.now().year,
                'url_tracking': f"https://tudominio.com/rastrear/{pedido['id']}"
            }
            
            contenido_html = template.render(**datos)
            
            asunto = f"✅ Pedido #{pedido['id']} Confirmado - Lavandería Digital"
            
            return self.enviar_email(
                destinatario=usuario['email'],
                asunto=asunto,
                contenido_html=contenido_html
            )
            
        except Exception as e:
            logger.error(f"Error enviando email de confirmación: {e}")
            return False
    
    def email_estado_pedido(self, pedido: Dict, usuario: Dict, nuevo_estado: str) -> bool:
        """Enviar email de cambio de estado del pedido"""
        estados_emoji = {
            'Solicitado': '📝',
            'Recolectado': '📦',
            'EnProceso': '🧼',
            'Listo': '✅',
            'Entregado': '🏠',
            'Cancelado': '❌'
        }
        
        estados_mensaje = {
            'Solicitado': 'Tu pedido ha sido solicitado y está en cola para recolección.',
            'Recolectado': '¡Hemos recolectado tu ropa! Ya está en camino a nuestra lavandería.',
            'EnProceso': 'Tu ropa está siendo lavada con el mayor cuidado.',
            'Listo': '¡Tu ropa está lista! La entregaremos pronto.',
            'Entregado': '¡Pedido entregado exitosamente! Gracias por confiar en nosotros.',
            'Cancelado': 'Tu pedido ha sido cancelado. Si tienes dudas, contáctanos.'
        }
        
        template_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .estado-box {{ background: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
        .estado-actual {{ font-size: 24px; color: #007bff; font-weight: bold; }}
        .progress-bar {{ background: #e9ecef; height: 20px; border-radius: 10px; margin: 20px 0; }}
        .progress {{ background: #007bff; height: 100%; border-radius: 10px; transition: width 0.3s; }}
        .footer {{ background: #6c757d; color: white; padding: 15px; text-align: center; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚚 Lavandería Digital</h1>
        <h2>Actualización de tu Pedido</h2>
    </div>
    
    <div class="content">
        <p>Hola <strong>{{{{ usuario.nombre }}}}</strong>,</p>
        
        <div class="estado-box">
            <div class="estado-actual">
                {estados_emoji.get(nuevo_estado, '📦')} {nuevo_estado}
            </div>
            <p>{estados_mensaje.get(nuevo_estado, 'Tu pedido ha sido actualizado.')}</p>
        </div>
        
        <h3>📋 Pedido #{{{{ pedido.id }}}}</h3>
        <p><strong>📅 Fecha de Recolección:</strong> {{{{ pedido.fecha_recoleccion }}}}</p>
        <p><strong>📅 Fecha de Entrega:</strong> {{{{ pedido.fecha_entrega }}}}</p>
        <p><strong>💰 Total:</strong> ${{{{ pedido.precio_total }}}}</p>
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="{{{{ url_tracking }}}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                🔍 Ver Detalles Completos
            </a>
        </p>
    </div>
    
    <div class="footer">
        <p>© {{{{ año }}}} Lavandería Digital. Todos los derechos reservados.</p>
    </div>
</body>
</html>
        """
        
        try:
            template = Template(template_html)
            
            datos = {
                'usuario': usuario,
                'pedido': pedido,
                'año': datetime.now().year,
                'url_tracking': f"https://tudominio.com/rastrear/{pedido['id']}"
            }
            
            contenido_html = template.render(**datos)
            
            asunto = f"{estados_emoji.get(nuevo_estado, '📦')} Pedido #{pedido['id']} - {nuevo_estado}"
            
            return self.enviar_email(
                destinatario=usuario['email'],
                asunto=asunto,
                contenido_html=contenido_html
            )
            
        except Exception as e:
            logger.error(f"Error enviando email de estado: {e}")
            return False
    
    def email_ruta_repartidor(self, repartidor_email: str, ruta: Dict) -> bool:
        """Enviar email con ruta al repartidor"""
        template_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .ruta-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .parada { border: 1px solid #dee2e6; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .recoleccion { border-left: 4px solid #007bff; }
        .entrega { border-left: 4px solid #28a745; }
        .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚚 Ruta del Día</h1>
        <h2>{{ ruta.fecha }}</h2>
    </div>
    
    <div class="content">
        <p>¡Buenos días! Aquí tienes tu ruta optimizada para hoy:</p>
        
        <div class="ruta-info">
            <h3>📊 Resumen de la Ruta</h3>
            <p><strong>🆔 ID de Ruta:</strong> {{ ruta.id }}</p>
            <p><strong>📍 Total de Paradas:</strong> {{ ruta.total_paradas }}</p>
            <p><strong>🛣️ Distancia Estimada:</strong> {{ ruta.distancia_km }} km</p>
            <p><strong>⏱️ Tiempo Estimado:</strong> {{ ruta.tiempo_minutos }} minutos</p>
            <p><strong>🕘 Hora de Inicio:</strong> {{ ruta.hora_inicio }}</p>
        </div>
        
        <h3>📋 Paradas en Orden Óptimo:</h3>
        {% for parada in ruta.paradas %}
        <div class="parada {{ parada.tipo }}">
            <h4>
                {% if parada.tipo == 'recoleccion' %}📦{% else %}🏠{% endif %}
                Parada {{ parada.orden }} - {{ parada.hora_estimada }}
            </h4>
            <p><strong>Cliente:</strong> {{ parada.cliente }}</p>
            <p><strong>Dirección:</strong> {{ parada.direccion }}</p>
            <p><strong>Teléfono:</strong> {{ parada.telefono }}</p>
            {% if parada.notas %}
            <p><strong>Notas:</strong> {{ parada.notas }}</p>
            {% endif %}
            <p><strong>Tipo:</strong> 
                {% if parada.tipo == 'recoleccion' %}
                    🔵 Recolección
                {% else %}
                    🟢 Entrega
                {% endif %}
            </p>
        </div>
        {% endfor %}
        
        <p style="text-align: center; margin: 30px 0;">
            <a href="{{ ruta.url_mapa }}" class="btn">🗺️ Abrir en Google Maps</a>
        </p>
        
        <h3>💡 Consejos para la Ruta:</h3>
        <ul>
            <li>Confirma cada recogida/entrega en el bot de Telegram</li>
            <li>Mantén contacto con los clientes si hay retrasos</li>
            <li>Revisa el tráfico antes de salir</li>
            <li>Lleva cambio en efectivo</li>
        </ul>
    </div>
</body>
</html>
        """
        
        try:
            template = Template(template_html)
            contenido_html = template.render(ruta=ruta)
            
            asunto = f"🚚 Tu Ruta del {ruta['fecha']} - {ruta['total_paradas']} paradas"
            
            return self.enviar_email(
                destinatario=repartidor_email,
                asunto=asunto,
                contenido_html=contenido_html
            )
            
        except Exception as e:
            logger.error(f"Error enviando email de ruta: {e}")
            return False

# Instancia global del servicio
email_service = EmailService()