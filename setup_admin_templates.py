"""
Script para crear automáticamente todos los templates necesarios
"""

import os

def create_all_templates():
    # Crear carpetas necesarias
    os.makedirs("templates", exist_ok=True)
    os.makedirs("templates/admin", exist_ok=True)
    
    # Template de login regular (actualizado)
    login_html = '''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Iniciar Sesión - Lavandería Digital</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container">
    <div class="row justify-content-center min-vh-100 align-items-center">
      <div class="col-md-6 col-lg-4">
        <div class="text-center mb-4">
          <i class="fas fa-tshirt fa-3x text-primary mb-3"></i>
          <h2 class="text-primary">Lavandería Digital</h2>
          <p class="text-muted">Servicio de lavandería a domicilio</p>
        </div>
        
        <div class="card shadow">
          <div class="card-header bg-primary text-white text-center">
            <h4 class="mb-0"><i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión</h4>
          </div>
          <div class="card-body p-4">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                  </div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            
            <form method="POST">
              <div class="mb-3">
                <label for="email" class="form-label">Correo electrónico</label>
                <input type="email" class="form-control" id="email" name="email" placeholder="tu@email.com" required />
              </div>
              
              <div class="mb-4">
                <label for="contrasena" class="form-label">Contraseña</label>
                <input type="password" class="form-control" id="contrasena" name="contrasena" placeholder="Tu contraseña" required />
              </div>
              
              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg">
                  <i class="fas fa-sign-in-alt me-2"></i>Entrar
                </button>
              </div>
            </form>
          </div>
          <div class="card-footer text-center">
            <p class="mb-0">¿No tienes cuenta? <a href="/registrar" class="text-decoration-none">Registrarse aquí</a></p>
            <hr>
            <small><a href="/admin/login" class="text-muted text-decoration-none">Acceso Admin</a></small>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Template de registro (actualizado)
    register_html = '''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Registro de Usuario - Lavandería Digital</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container">
    <div class="row justify-content-center min-vh-100 align-items-center">
      <div class="col-md-6 col-lg-5">
        <div class="card shadow">
          <div class="card-header bg-primary text-white text-center">
            <h4 class="mb-0"><i class="fas fa-user-plus me-2"></i>Registro de Usuario</h4>
          </div>
          <div class="card-body p-4">
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                  </div>
                {% endfor %}
              {% endif %}
            {% endwith %}
            
            <form action="/registrar" method="POST">
              <div class="mb-3">
                <label for="nombre" class="form-label">Nombre completo</label>
                <input type="text" class="form-control" id="nombre" name="nombre" placeholder="Tu nombre completo" required />
              </div>
              
              <div class="mb-3">
                <label for="email" class="form-label">Correo electrónico</label>
                <input type="email" class="form-control" id="email" name="email" placeholder="tu@email.com" required />
              </div>
              
              <div class="mb-3">
                <label for="telefono" class="form-label">Teléfono</label>
                <input type="tel" class="form-control" id="telefono" name="telefono" placeholder="55 1234 5678" />
                <div class="form-text">Opcional - Para notificaciones de recolección</div>
              </div>
              
              <div class="mb-3">
                <label for="contrasena" class="form-label">Contraseña</label>
                <input type="password" class="form-control" id="contrasena" name="contrasena" placeholder="Mínimo 6 caracteres" required />
              </div>
              
              <div class="mb-4">
                <label for="ubicacion" class="form-label">Dirección / Colonia</label>
                <textarea class="form-control" id="ubicacion" name="ubicacion" rows="2" placeholder="Calle, número, colonia..." required></textarea>
                <div class="form-text">Necesario para calcular rutas de recolección</div>
              </div>
              
              <div class="d-grid">
                <button type="submit" class="btn btn-primary btn-lg">
                  <i class="fas fa-check me-2"></i>Registrarse
                </button>
              </div>
            </form>
          </div>
          <div class="card-footer text-center">
            <p class="mb-0">¿Ya tienes cuenta? <a href="/login" class="text-decoration-none">Iniciar sesión</a></p>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Template de index (actualizado)
    index_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lavandería Digital - Inicio</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.home') }}">
                <i class="fas fa-tshirt me-2"></i>Lavandería Digital
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('main.cotizar') }}">Cotizar</a>
                <a class="nav-link" href="{{ url_for('main.mis_pedidos') }}">Mis Pedidos</a>
                <a class="nav-link" href="{{ url_for('main.logout') }}">Cerrar Sesión</a>
            </div>
        </div>
    </nav>

    <div class="container my-5">
        <!-- Hero Section -->
        <div class="row mb-5">
            <div class="col-lg-12 text-center">
                <h1 class="display-4 text-primary mb-3">
                    ¡Bienvenido {{ usuario.nombre }}!
                </h1>
                <p class="lead text-muted">
                    Tu servicio de lavandería digital con recolección y entrega a domicilio
                </p>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="row g-4 mb-5">
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center p-4">
                        <div class="mb-3">
                            <i class="fas fa-calculator fa-3x text-primary"></i>
                        </div>
                        <h5 class="card-title">Solicitar Servicio</h5>
                        <p class="card-text text-muted">
                            Cotiza y agenda tu recolección en minutos
                        </p>
                        <a href="{{ url_for('main.cotizar') }}" class="btn btn-primary">
                            <i class="fas fa-plus me-2"></i>Nuevo Pedido
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center p-4">
                        <div class="mb-3">
                            <i class="fas fa-list-alt fa-3x text-success"></i>
                        </div>
                        <h5 class="card-title">Mis Pedidos</h5>
                        <p class="card-text text-muted">
                            Revisa el estado de tus servicios
                        </p>
                        <a href="{{ url_for('main.mis_pedidos') }}" class="btn btn-success">
                            <i class="fas fa-eye me-2"></i>Ver Pedidos
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm">
                    <div class="card-body text-center p-4">
                        <div class="mb-3">
                            <i class="fas fa-clock fa-3x text-info"></i>
                        </div>
                        <h5 class="card-title">Horarios</h5>
                        <p class="card-text text-muted">
                            Recolección: 9:00-12:00<br>
                            Entrega: 14:00-18:00
                        </p>
                        <span class="badge bg-info">Lun - Sáb</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Features -->
        <div class="row">
            <div class="col-lg-12">
                <h3 class="text-center mb-4">¿Cómo funciona?</h3>
                <div class="row g-4">
                    <div class="col-md-3 text-center">
                        <div class="mb-3">
                            <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 60px; height: 60px;">
                                <span class="fw-bold">1</span>
                            </div>
                        </div>
                        <h6>Cotiza Online</h6>
                        <p class="text-muted small">Selecciona tus prendas y obtén precio instantáneo</p>
                    </div>
                    
                    <div class="col-md-3 text-center">
                        <div class="mb-3">
                            <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 60px; height: 60px;">
                                <span class="fw-bold">2</span>
                            </div>
                        </div>
                        <h6>Agenda Recolección</h6>
                        <p class="text-muted small">Elige fecha y horario que más te convenga</p>
                    </div>
                    
                    <div class="col-md-3 text-center">
                        <div class="mb-3">
                            <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 60px; height: 60px;">
                                <span class="fw-bold">3</span>
                            </div>
                        </div>
                        <h6>Lavado Profesional</h6>
                        <p class="text-muted small">Cuidamos tu ropa con productos de calidad</p>
                    </div>
                    
                    <div class="col-md-3 text-center">
                        <div class="mb-3">
                            <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 60px; height: 60px;">
                                <span class="fw-bold">4</span>
                            </div>
                        </div>
                        <h6>Entrega a Domicilio</h6>
                        <p class="text-muted small">Recibe tu ropa limpia y doblada</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # TEMPLATES ADMIN (ya creados anteriormente)
    admin_login_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Lavandería Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-dark">
    <div class="container">
        <div class="row justify-content-center min-vh-100 align-items-center">
            <div class="col-md-6 col-lg-4">
                <div class="text-center mb-4">
                    <i class="fas fa-shield-alt fa-3x text-warning mb-3"></i>
                    <h2 class="text-white">Panel Administrativo</h2>
                    <p class="text-muted">Lavandería Digital</p>
                </div>
                
                <div class="card shadow-lg">
                    <div class="card-header bg-warning text-dark text-center">
                        <h4 class="mb-0"><i class="fas fa-key me-2"></i>Acceso Admin</h4>
                    </div>
                    <div class="card-body p-4">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="usuario" class="form-label">Usuario</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-user"></i></span>
                                    <input type="text" class="form-control" id="usuario" name="usuario" placeholder="Usuario admin" required />
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="contrasena" class="form-label">Contraseña</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                                    <input type="password" class="form-control" id="contrasena" name="contrasena" placeholder="Contraseña" required />
                                </div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-warning btn-lg text-dark">
                                    <i class="fas fa-sign-in-alt me-2"></i>Acceder al Panel
                                </button>
                            </div>
                        </form>
                    </div>
                    <div class="card-footer text-center text-muted">
                        <small>
                            <i class="fas fa-home me-1"></i>
                            <a href="{{ url_for('main.home') }}" class="text-decoration-none">Volver al sitio público</a>
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Escribir todos los archivos
    templates = {
        "templates/login.html": login_html,
        "templates/register.html": register_html,
        "templates/index.html": index_html,
        "templates/admin/login.html": admin_login_html,
    }
    
    for path, content in templates.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    
    print("✅ TODOS los templates creados exitosamente!")
    print("📁 Archivos creados/actualizados:")
    for path in templates.keys():
        print(f"   - {path}")
    
    print("\n🚀 Ahora puedes:")
    print("   - Sitio público: http://localhost:5000")
    print("   - Panel admin: http://localhost:5000/admin/login")
    print("   - Credenciales admin: admin / admin123")

if __name__ == "__main__":
    create_all_templates()
    # Crear carpeta admin si no existe
    admin_dir = "templates/admin"
    os.makedirs(admin_dir, exist_ok=True)
    
    # Template de login admin
    login_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - Lavandería Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-dark">
    <div class="container">
        <div class="row justify-content-center min-vh-100 align-items-center">
            <div class="col-md-6 col-lg-4">
                <div class="text-center mb-4">
                    <i class="fas fa-shield-alt fa-3x text-warning mb-3"></i>
                    <h2 class="text-white">Panel Administrativo</h2>
                    <p class="text-muted">Lavandería Digital</p>
                </div>
                
                <div class="card shadow-lg">
                    <div class="card-header bg-warning text-dark text-center">
                        <h4 class="mb-0"><i class="fas fa-key me-2"></i>Acceso Admin</h4>
                    </div>
                    <div class="card-body p-4">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                                        {{ message }}
                                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="usuario" class="form-label">Usuario</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-user"></i></span>
                                    <input type="text" class="form-control" id="usuario" name="usuario" placeholder="Usuario admin" required />
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="contrasena" class="form-label">Contraseña</label>
                                <div class="input-group">
                                    <span class="input-group-text"><i class="fas fa-lock"></i></span>
                                    <input type="password" class="form-control" id="contrasena" name="contrasena" placeholder="Contraseña" required />
                                </div>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-warning btn-lg text-dark">
                                    <i class="fas fa-sign-in-alt me-2"></i>Acceder al Panel
                                </button>
                            </div>
                        </form>
                    </div>
                    <div class="card-footer text-center text-muted">
                        <small>
                            <i class="fas fa-home me-1"></i>
                            <a href="{{ url_for('main.home') }}" class="text-decoration-none">Volver al sitio público</a>
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Template básico de dashboard
    dashboard_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Admin - Lavandería Digital</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <!-- Navbar Admin -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('admin.dashboard') }}">
                <i class="fas fa-shield-alt me-2"></i>Admin Panel
            </a>
            
            <div class="navbar-nav me-auto">
                <a class="nav-link active" href="{{ url_for('admin.dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('admin.pedidos') }}">Pedidos</a>
            </div>
            
            <div class="navbar-nav">
                <span class="navbar-text me-3">
                    <i class="fas fa-user-shield me-1"></i>{{ session.admin_nombre }}
                </span>
                <a class="nav-link" href="{{ url_for('admin.logout') }}">
                    <i class="fas fa-sign-out-alt me-1"></i>Salir
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid my-4">
        <div class="row mb-4">
            <div class="col-12">
                <h2><i class="fas fa-tachometer-alt me-2"></i>Dashboard Administrativo</h2>
            </div>
        </div>

        <!-- Cards de estadísticas básicas -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-truck fa-2x mb-2"></i>
                        <h4>{{ stats.pedidos_hoy or 0 }}</h4>
                        <p>Recolecciones Hoy</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-box fa-2x mb-2"></i>
                        <h4>{{ stats.entregas_hoy or 0 }}</h4>
                        <p>Entregas Hoy</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <i class="fas fa-dollar-sign fa-2x mb-2"></i>
                        <h4>${{ "%.0f" | format(stats.ingresos_mes or 0) }}</h4>
                        <p>Ingresos del Mes</p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-warning text-dark">
                    <div class="card-body text-center">
                        <i class="fas fa-list fa-2x mb-2"></i>
                        <h4>{{ (stats.estados or []) | length }}</h4>
                        <p>Total Pedidos</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Pedidos recientes -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-clock me-2"></i>Actividad Reciente</h5>
                    </div>
                    <div class="card-body">
                        {% if pedidos_recientes %}
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Pedido</th>
                                            <th>Cliente</th>
                                            <th>Estado</th>
                                            <th>Total</th>
                                            <th>Fecha</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for pedido in pedidos_recientes %}
                                        <tr>
                                            <td><strong>#{{ pedido.id }}</strong></td>
                                            <td>{{ pedido.usuario.nombre }}</td>
                                            <td>
                                                <span class="badge bg-secondary">{{ pedido.estado }}</span>
                                            </td>
                                            <td>${{ "%.2f" | format(pedido.precio_total) }}</td>
                                            <td>{{ pedido.creado.strftime('%d/%m/%Y') }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        {% else %}
                            <div class="text-center py-4">
                                <i class="fas fa-inbox fa-3x text-muted mb-2"></i>
                                <p class="text-muted">No hay pedidos recientes</p>
                            </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

    # Template básico de pedidos
    pedidos_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestión de Pedidos - Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <!-- Navbar Admin -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('admin.dashboard') }}">
                <i class="fas fa-shield-alt me-2"></i>Admin Panel
            </a>
            
            <div class="navbar-nav me-auto">
                <a class="nav-link" href="{{ url_for('admin.dashboard') }}">Dashboard</a>
                <a class="nav-link active" href="{{ url_for('admin.pedidos') }}">Pedidos</a>
            </div>
            
            <div class="navbar-nav">
                <span class="navbar-text me-3">
                    <i class="fas fa-user-shield me-1"></i>{{ session.admin_nombre }}
                </span>
                <a class="nav-link" href="{{ url_for('admin.logout') }}">
                    <i class="fas fa-sign-out-alt me-1"></i>Salir
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid my-4">
        <h2><i class="fas fa-list-alt me-2"></i>Gestión de Pedidos</h2>

        <!-- Lista de Pedidos -->
        <div class="card mt-4">
            <div class="card-header">
                <h5>Todos los Pedidos ({{ pedidos | length }})</h5>
            </div>
            <div class="card-body">
                {% if pedidos %}
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Pedido</th>
                                    <th>Cliente</th>
                                    <th>Estado</th>
                                    <th>Total</th>
                                    <th>Fecha</th>
                                    <th>Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for pedido in pedidos %}
                                <tr>
                                    <td><strong>#{{ pedido.id }}</strong></td>
                                    <td>
                                        {{ pedido.usuario.nombre }}<br>
                                        <small class="text-muted">{{ pedido.usuario.email }}</small>
                                    </td>
                                    <td>
                                        <select class="form-select form-select-sm" onchange="cambiarEstado({{ pedido.id }}, this.value)">
                                            <option value="Solicitado" {% if pedido.estado == 'Solicitado' %}selected{% endif %}>Solicitado</option>
                                            <option value="Recolectado" {% if pedido.estado == 'Recolectado' %}selected{% endif %}>Recolectado</option>
                                            <option value="EnProceso" {% if pedido.estado == 'EnProceso' %}selected{% endif %}>En Proceso</option>
                                            <option value="Listo" {% if pedido.estado == 'Listo' %}selected{% endif %}>Listo</option>
                                            <option value="Entregado" {% if pedido.estado == 'Entregado' %}selected{% endif %}>Entregado</option>
                                        </select>
                                    </td>
                                    <td>${{ "%.2f" | format(pedido.precio_total) }}</td>
                                    <td>{{ pedido.creado.strftime('%d/%m/%Y') }}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No hay pedidos disponibles</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function cambiarEstado(pedidoId, nuevoEstado) {
            fetch('/admin/api/actualizar-estado', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pedido_id: pedidoId,
                    estado: nuevoEstado
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Estado actualizado correctamente');
                } else {
                    alert('Error: ' + (data.error || 'Error desconocido'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error de conexión');
            });
        }
    </script>
</body>
</html>'''

    # Escribir archivos
    with open(f"{admin_dir}/login.html", "w", encoding="utf-8") as f:
        f.write(login_html)
    
    with open(f"{admin_dir}/dashboard.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
        
    with open(f"{admin_dir}/pedidos.html", "w", encoding="utf-8") as f:
        f.write(pedidos_html)
    
    print("✅ Templates del admin creados exitosamente!")
    print("📁 Archivos creados:")
    print("   - templates/admin/login.html")
    print("   - templates/admin/dashboard.html") 
    print("   - templates/admin/pedidos.html")
    print("\n🚀 Ahora puedes acceder a: http://localhost:5000/admin/login")

if __name__ == "__main__":
    create_admin_templates()