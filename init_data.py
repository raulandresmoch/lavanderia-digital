"""
Script para inicializar la base de datos con datos de ejemplo
Ejecutar una sola vez después de crear la aplicación
"""

from app import create_app
from app.models import db, TipoPrenda, Configuracion

def init_database():
    app = create_app()
    
    with app.app_context():
        # Verificar si ya hay datos
        if TipoPrenda.query.first():
            print("La base de datos ya tiene datos inicializados.")
            return
        
        # Crear tipos de prendas
        tipos_prenda = [
            {
                'nombre': 'Ropa Normal',
                'precio_por_kg': 25.0,
                'tiempo_lavado_horas': 24,
                'descripcion': 'Ropa casual, camisetas, pantalones, ropa interior'
            },
            {
                'nombre': 'Ropa Delicada',
                'precio_por_kg': 35.0,
                'tiempo_lavado_horas': 48,
                'descripcion': 'Seda, lana, prendas que requieren cuidado especial'
            },
            {
                'nombre': 'Edredones y Cobijas',
                'precio_por_kg': 40.0,
                'tiempo_lavado_horas': 48,
                'descripcion': 'Edredones, cobijas gruesas, almohadas grandes'
            },
            {
                'nombre': 'Sábanas y Toallas',
                'precio_por_kg': 20.0,
                'tiempo_lavado_horas': 24,
                'descripcion': 'Juegos de sábanas, toallas de baño, manteles'
            },
            {
                'nombre': 'Ropa de Trabajo',
                'precio_por_kg': 30.0,
                'tiempo_lavado_horas': 36,
                'descripcion': 'Uniformes, overoles, ropa con manchas difíciles'
            },
            {
                'nombre': 'Cortinas',
                'precio_por_kg': 45.0,
                'tiempo_lavado_horas': 72,
                'descripcion': 'Cortinas de casa, persianas de tela'
            }
        ]
        
        for tipo_data in tipos_prenda:
            tipo = TipoPrenda(**tipo_data)
            db.session.add(tipo)
        
        # Configuraciones del sistema
        configuraciones = [
            {
                'clave': 'horario_recoleccion',
                'valor': 'Mañana (9:00-12:00)',
                'descripcion': 'Horario fijo de recolección'
            },
            {
                'clave': 'horario_entrega',
                'valor': 'Tarde (14:00-18:00)',
                'descripcion': 'Horario fijo de entrega'
            },
            {
                'clave': 'dias_laborales',
                'valor': '1,2,3,4,5,6',
                'descripcion': 'Días de la semana que trabajamos (1=Lunes, 6=Sábado)'
            },
            {
                'clave': 'telefono_contacto',
                'valor': '+52 55 1234-5678',
                'descripcion': 'Teléfono de contacto para clientes'
            },
            {
                'clave': 'email_contacto',
                'valor': 'soporte@lavanderia-digital.com',
                'descripcion': 'Email de soporte'
            },
            {
                'clave': 'zona_cobertura',
                'valor': 'Benito Juárez, Roma Norte, Condesa, Del Valle',
                'descripcion': 'Zonas donde damos servicio'
            }
        ]
        
        for config_data in configuraciones:
            config = Configuracion(**config_data)
            db.session.add(config)
        
        # Guardar cambios
        db.session.commit()
        
        print("✅ Base de datos inicializada correctamente!")
        print(f"✅ Creados {len(tipos_prenda)} tipos de prendas")
        print(f"✅ Creadas {len(configuraciones)} configuraciones")
        print("\nTipos de prendas disponibles:")
        for tipo in TipoPrenda.query.all():
            print(f"- {tipo.nombre}: ${tipo.precio_por_kg}/kg ({tipo.tiempo_lavado_horas}h)")

if __name__ == "__main__":
    init_database()