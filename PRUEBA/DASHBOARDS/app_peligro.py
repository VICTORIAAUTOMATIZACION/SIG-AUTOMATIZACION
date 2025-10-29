# Archivo: app.py - VERSIÓN SIMPLIFICADA CON SOLO MAPA DE RIESGO CONSOLIDADO

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import re
import os

# Importamos solo la función de análisis de riesgo consolidado
from analisis_peligro_multicriterio import generar_mapa_riesgo_consolidado

# ==================== CONFIGURACIÓN DE LA APP ====================
app = Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
    ], 
    suppress_callback_exceptions=True
)

# Inyectar CSS con tema verde y animaciones
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Variables de color */
            :root {
                --escuela-verde-claro: #8BC34A;
                --escuela-verde: #7CB342;
                --escuela-verde-oscuro: #558B2F;
                --escuela-verde-profundo: #33691E;
                --gris-carga: #90A4AE;
            }
            
            /* Fuente moderna */
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            /* Fondo con gradiente verde */
            body {
                background: linear-gradient(135deg, #8BC34A 0%, #558B2F 50%, #33691E 100%) !important;
                min-height: 100vh;
            }
            
            /* Cards con efecto glassmorphism */
            .card {
                backdrop-filter: blur(10px);
                background: rgba(200, 220, 190, 0.35) !important;
                border: 1px solid rgba(255, 255, 255, 0.25) !important;
                box-shadow: 0 10px 40px rgba(51, 105, 30, 0.2) !important;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border-radius: 16px !important;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 50px rgba(51, 105, 30, 0.3) !important;
            }
            
            /* Inputs modernos con acento verde */
            .form-control, .form-select {
                border: 2px solid rgba(197, 225, 165, 0.5) !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                transition: all 0.3s ease;
                background: rgba(245, 250, 240, 0.4) !important;
                backdrop-filter: blur(5px);
            }
            
            .form-control:focus, .form-select:focus {
                border-color: #7CB342 !important;
                box-shadow: 0 0 0 3px rgba(124, 179, 66, 0.15) !important;
                transform: translateY(-2px);
                background: rgba(255, 255, 255, 0.6) !important;
            }
            
            /* Botón Generar Mapa - Verde */
            .btn-success {
                background: linear-gradient(135deg, #8BC34A 0%, #7CB342 100%) !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 14px 28px !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(139, 195, 74, 0.4) !important;
                color: white !important;
            }
            
            .btn-success:hover:not(:disabled) {
                background: linear-gradient(135deg, #7CB342 0%, #689F38 100%) !important;
                transform: translateY(-3px);
                box-shadow: 0 6px 30px rgba(139, 195, 74, 0.5) !important;
            }
            
            .btn-success:disabled {
                background: linear-gradient(135deg, #B0BEC5 0%, #90A4AE 100%) !important;
                opacity: 0.7;
                cursor: wait !important;
                box-shadow: 0 2px 10px rgba(144, 164, 174, 0.3) !important;
                animation: pulse-loading 1.5s ease-in-out infinite;
            }
            
            /* Botón Descargar Mapa - Verde Oscuro */
            .btn-info {
                background: linear-gradient(135deg, #558B2F 0%, #33691E 100%) !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 14px 28px !important;
                font-weight: 700 !important;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(85, 139, 47, 0.4) !important;
                color: white !important;
            }
            
            .btn-info:hover:not(:disabled) {
                background: linear-gradient(135deg, #33691E 0%, #1B5E20 100%) !important;
                transform: translateY(-3px);
                box-shadow: 0 6px 30px rgba(85, 139, 47, 0.5) !important;
            }
            
            .btn-info:disabled {
                background: linear-gradient(135deg, #B0BEC5 0%, #90A4AE 100%) !important;
                opacity: 0.7;
                cursor: wait !important;
                box-shadow: 0 2px 10px rgba(144, 164, 174, 0.3) !important;
            }
            
            /* Botón Logout */
            .btn-danger {
                background: linear-gradient(135deg, #EF5350 0%, #E53935 100%) !important;
                border: none !important;
                border-radius: 8px !important;
                transition: all 0.3s ease;
                font-weight: 600 !important;
            }
            
            /* Navbar premium */
            .navbar {
                backdrop-filter: blur(10px);
                background: rgba(255, 255, 255, 0.15) !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 4px 20px rgba(51, 105, 30, 0.15);
            }
            
            .navbar-custom .container-fluid {
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
            }
            
            .navbar-brand {
                font-weight: 800 !important;
                font-size: 1.3rem !important;
                letter-spacing: 0.5px !important;
                display: flex !important;
                align-items: center !important;
            }
            
            .navbar-nav {
                margin-left: auto !important;
            }
            
            /* Labels con estilo verde */
            label {
                color: #33691E;
                font-weight: 700;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-bottom: 8px;
            }
            
            /* Alertas modernas */
            .alert {
                border-radius: 16px !important;
                border: none !important;
                padding: 24px !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08) !important;
            }
            
            .alert-success {
                background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%) !important;
                border-left: 5px solid #7CB342 !important;
                color: #1B5E20 !important;
            }
            
            /* Hr decorativo */
            hr {
                border-top: 2px solid #C5E1A5 !important;
                opacity: 0.8;
                margin: 24px 0 !important;
            }
            
            /* Resumen de selección */
            .selection-summary {
                background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 100%);
                padding: 20px;
                border-radius: 12px;
                border-left: 5px solid #7CB342;
            }
            
            /* Login container */
            .login-container {
                backdrop-filter: blur(10px);
                background: rgba(240, 250, 235, 0.45);
                border-radius: 20px;
                padding: 50px;
                box-shadow: 0 25px 70px rgba(51, 105, 30, 0.3);
                border: 2px solid rgba(139, 195, 74, 0.25);
            }
            
            /* Animación de rotación para el logo */
            @keyframes logoRotation {
                from { transform: rotateY(0deg); }
                to { transform: rotateY(360deg); }
            }
            
            .logo-rotation {
                animation: logoRotation 4s linear infinite;
                filter: drop-shadow(0 4px 10px rgba(139, 195, 74, 0.3));
            }
            
            .logo-rotation:hover {
                animation-duration: 1.5s;
            }
            
            /* Animación de rotación 3D para el icono de reloj */
            @keyframes hourglassSpin {
                0% { transform: rotateZ(0deg); }
                50% { transform: rotateZ(180deg); }
                100% { transform: rotateZ(360deg); }
            }
            
            .hourglass-spin {
                display: inline-block;
                animation: hourglassSpin 2s linear infinite;
                transform-style: preserve-3d;
            }
            
            .hourglass-spin:hover {
                animation-duration: 1s;
            }
            
            /* Animación de pulso para botones en carga */
            @keyframes pulse-loading {
                0%, 100% { 
                    opacity: 0.7;
                    transform: scale(1);
                }
                50% { 
                    opacity: 0.9;
                    transform: scale(1.02);
                }
            }
            
            /* Animaciones generales */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .animated {
                animation: fadeIn 0.7s ease-out;
            }
            
            /* Scrollbar personalizado verde */
            ::-webkit-scrollbar {
                width: 12px;
            }
            
            ::-webkit-scrollbar-track {
                background: #F1F8E9;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, #8BC34A 0%, #558B2F 100%);
                border-radius: 6px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, #7CB342 0%, #33691E 100%);
            }
            
            /* Icono de éxito verde */
            .success-icon {
                color: #7CB342;
            }
            
            /* Panel de control header */
            .panel-header {
                background: linear-gradient(135deg, #8BC34A 0%, #7CB342 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            /* Logo en navbar */
            .navbar-logo {
                height: 40px;
                margin-right: 15px;
                filter: brightness(0) invert(1);
            }
            
            /* Footer de contactos */
            .contact-footer {
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: rgba(240, 250, 235, 0.5);
                backdrop-filter: blur(10px);
                padding: 15px 20px;
                border-radius: 12px;
                border: 2px solid rgba(139, 195, 74, 0.3);
                box-shadow: 0 4px 20px rgba(51, 105, 30, 0.2);
                z-index: 1000;
                transition: all 0.3s ease;
            }
            
            .contact-footer:hover {
                background: rgba(240, 250, 235, 0.7);
                transform: translateY(-3px);
                box-shadow: 0 6px 25px rgba(51, 105, 30, 0.3);
            }
            
            .contact-footer a {
                color: #33691E;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                margin: 0 10px;
            }
            
            .contact-footer a:hover {
                color: #7CB342;
                transform: translateX(3px);
            }
            
            .contact-footer a i {
                font-size: 1.2rem;
                margin-right: 6px;
            }
            
            /* Sección de descarga */
            .download-section {
                background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 100%);
                padding: 20px;
                border-radius: 12px;
                border: 2px dashed #8BC34A;
                margin-top: 15px;
            }
            
            /* Contenedor de parámetros info */
            .parametros-info {
                background: linear-gradient(135deg, #F1F8E9 0%, #E8F5E9 100%);
                padding: 15px;
                border-radius: 12px;
                border-left: 4px solid #7CB342;
                margin-bottom: 15px;
            }
            
            .parametro-item {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                color: #33691E;
            }
            
            .parametro-item i {
                font-size: 1.3rem;
                margin-right: 10px;
                color: #7CB342;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

VALID_USERS = {'admin': 'admin', 'usuario': 'admin'}

def leer_sql(ruta):
    if not os.path.exists(ruta):
        print(f"⚠️ ADVERTENCIA: La ruta del archivo SQL no existe: '{ruta}'")
        return []
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    patron = r"INSERT INTO `\w+` VALUES \(([^)]+)\);"
    matches = re.findall(patron, contenido)
    return [[v.strip().strip("'") for v in match.split(',')] for match in matches]

# Carga de datos SQL
try:
    ruta_departamentos = '/workspaces/SIG-AUTOMATIZACION/PRUEBA/DASHBOARDS/departamentos.sql'
    ruta_provincias = '/workspaces/SIG-AUTOMATIZACION/PRUEBA/DASHBOARDS/provincias.sql'
    ruta_distritos = '/workspaces/SIG-AUTOMATIZACION/PRUEBA/DASHBOARDS/distritos.sql'
    print("Cargando datos SQL para todo el Perú...")
    depa_data, prov_data, dist_data = leer_sql(ruta_departamentos), leer_sql(ruta_provincias), leer_sql(ruta_distritos)
    if not all([depa_data, prov_data, dist_data]): 
        raise ValueError("Archivos SQL no encontrados.")
    departamentos = {d[0]: d[1] for d in depa_data}
    provincias = {p[0]: {'nombre': p[1], 'id_depa': p[2]} for p in prov_data}
    distritos = {d[0]: {'nombre': d[1], 'id_prov': d[2]} for d in dist_data}
    PROVINCIAS_POR_DEPA, DISTRITOS_POR_PROV = {}, {}
    for prov_id, prov_info in provincias.items():
        if (depa_id := prov_info['id_depa']) in departamentos:
            PROVINCIAS_POR_DEPA.setdefault(departamentos[depa_id], []).append(prov_info['nombre'])
    for dist_id, dist_info in distritos.items():
        if (prov_id := dist_info['id_prov']) in provincias:
            DISTRITOS_POR_PROV.setdefault(provincias[prov_id]['nombre'], []).append(dist_info['nombre'])
    LISTA_DEPARTAMENTOS = sorted(PROVINCIAS_POR_DEPA.keys())
    print("✅ Datos SQL cargados correctamente.")
except Exception as e:
    print(f"❌ Error crítico al cargar datos SQL: {e}. Usando datos de respaldo.")
    LISTA_DEPARTAMENTOS, PROVINCIAS_POR_DEPA, DISTRITOS_POR_PROV = ['CUSCO'], {'CUSCO': ['CUSCO']}, {'CUSCO': ['PUCYURA']}

# ==================== LAYOUT DE LOGIN ====================
login_layout = dbc.Container([
    # Footer de contactos
    html.Div([
        html.A([
            html.I(className="bi bi-globe2"),
            "escuelar.org"
        ], href="https://escuelar.org/", target="_blank"),
        html.Span(" | ", style={'color': '#7CB342', 'fontWeight': '700'}),
        html.A([
            html.I(className="bi bi-linkedin"),
            "LinkedIn"
        ], href="https://www.linkedin.com/company/escuelar/about/", target="_blank")
    ], className='contact-footer'),
    
    dbc.Row(
        dbc.Col(
            html.Div([
                html.Div([
                    html.Img(
                        src='/assets/LOGO.png',
                        className='logo-rotation',
                        style={
                            'width': '150px',
                            'height': 'auto',
                            'marginBottom': '20px'
                        }
                    )
                ], className='text-center'),
                
                html.H2("ANÁLISIS DE PELIGRO MULTICRITERIO", 
                       className="text-center mb-4",
                       style={
                           'color': "#FEFFFE", 
                           'fontWeight': '800',
                           'fontSize': '1.8rem',
                           'letterSpacing': '0.5px'
                       }),
                
                html.P("Generador de Mapas de Riesgo Consolidado", 
                      className="text-center mb-4",
                      style={
                          'color': "#C8E6C9", 
                          'fontWeight': '500',
                          'fontSize': '1rem'
                      }),
                
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Label([
                                html.I(className="bi bi-person-fill me-2"),
                                "Usuario"
                            ], style={'color': '#33691E', 'fontWeight': '700'}),
                            dbc.Input(
                                id='username-input',
                                placeholder='Ingrese su usuario',
                                type='text',
                                className='mb-3'
                            )
                        ]),
                        
                        html.Div([
                            html.Label([
                                html.I(className="bi bi-lock-fill me-2"),
                                "Contraseña"
                            ], style={'color': '#33691E', 'fontWeight': '700'}),
                            dbc.Input(
                                id='password-input',
                                placeholder='Ingrese su contraseña',
                                type='password',
                                className='mb-4'
                            )
                        ]),
                        
                        dbc.Button([
                            html.I(className="bi bi-box-arrow-in-right me-2"),
                            'Iniciar Sesión'
                        ], 
                        id='login-button',
                        color='success',
                        className='w-100 btn-success',
                        style={'padding': '14px', 'fontSize': '1.1rem'}),
                        
                        html.Div(id='login-alert', className='mt-3')
                    ])
                ], className='shadow-lg border-0 login-container')
            ], 
            className='animated',
            style={
                'marginTop': '80px',
                'maxWidth': '480px',
                'margin': '80px auto'
            }),
            width=12
        ),
        justify='center'
    )
], fluid=True)

# ==================== LAYOUT DEL DASHBOARD ====================
dashboard_layout = dbc.Container([
    dcc.Download(id="download-map-image"),
    dcc.Store(id='map-filepath-store', storage_type='memory'),
    dcc.Store(id='loading-state', storage_type='memory', data=False),
    
    # Footer de contactos
    html.Div([
        html.A([
            html.I(className="bi bi-globe2"),
            "escuelar.org"
        ], href="https://escuelar.org/", target="_blank"),
        html.Span(" | ", style={'color': '#7CB342', 'fontWeight': '700'}),
        html.A([
            html.I(className="bi bi-linkedin"),
            "LinkedIn"
        ], href="https://www.linkedin.com/company/escuelar/about/", target="_blank")
    ], className='contact-footer'),
    
    # Navbar premium
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                html.Span(
                    id='user-display-nav',
                    className='navbar-text me-3',
                    style={'color': 'white', 'fontWeight': '600', 'fontSize': '1rem'}
                )
            ),
            dbc.NavItem(
                dbc.Button([
                    html.I(className="bi bi-box-arrow-right me-2"),
                    "Cerrar Sesión"
                ], 
                id='logout-button',
                color='danger',
                size='sm',
                className='btn-danger')
            )
        ],
        brand=[
            html.Img(
                src='/assets/LOGO.png',
                className='navbar-logo'
            ),
            "Análisis de Peligro Multicriterio - Mapa de Riesgo Consolidado"
        ],
        color="primary",
        dark=True,
        className='mb-4 shadow-sm navbar-custom',
        style={'fontSize': '1.2rem'},
        fluid=True
    ),
    
    dbc.Row([
        # Panel de control izquierdo
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-sliders me-2", style={'fontSize': '1.8rem', 'color': "#EEF5E7"}),
                        html.H4("Panel de Control", className='panel-header', style={'display': 'inline', 'fontWeight': '900','color': "#EEF5E7"})
                    ], className='mb-4'),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label([
                                    html.I(className="bi bi-person-badge me-2"),
                                    "Nombre de Usuario"
                                ]),
                                dbc.Input(
                                    id='user-name-input',
                                    type='text',
                                    placeholder='Ej: Daniel Porras Núñez',
                                    className='mb-4'
                                )
                            ]),
                        ], md=12)
                    ]),
                    
                    html.Hr(style={'borderTop': '2px dashed #C5E1A5', 'margin': '20px 0'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label([
                                    html.I(className="bi bi-geo-alt me-2"),
                                    "Departamento"
                                ]),
                                dcc.Dropdown(
                                    id='departamento-dropdown',
                                    options=LISTA_DEPARTAMENTOS,
                                    placeholder='Seleccione departamento',
                                    className='mb-4'
                                )
                            ]),
                            
                            html.Div([
                                html.Label([
                                    html.I(className="bi bi-building me-2"),
                                    "Provincia"
                                ]),
                                dcc.Dropdown(
                                    id='provincia-dropdown',
                                    placeholder='Primero elija departamento',
                                    disabled=True,
                                    className='mb-4'
                                )
                            ]),
                            
                            html.Div([
                                html.Label([
                                    html.I(className="bi bi-house me-2"),
                                    "Distrito"
                                ]),
                                dcc.Dropdown(
                                    id='distrito-dropdown',
                                    placeholder='Primero elija provincia',
                                    disabled=True,
                                    className='mb-4'
                                )
                            ])
                        ], md=12)
                    ]),
                    
                    html.Hr(style={'borderTop': '2px dashed #C5E1A5', 'margin': '20px 0'}),
                    
                    # Información de parámetros
                    html.Div([
                        html.H6([
                            html.I(className="bi bi-info-circle me-2", style={'color': '#7CB342'}),
                            "Parámetros Analizados"
                        ], style={'color': '#33691E', 'fontWeight': '800', 'marginBottom': '12px'}),
                        
                        html.Div([
                            html.Div([
                                html.I(className="bi bi-droplet-fill", style={'color': '#00BFFF'}),
                                html.Span("Distancia a Ríos (PESO_RIO)", style={'marginLeft': '8px'})
                            ], className='parametro-item'),
                            
                            html.Div([
                                html.I(className="bi bi-mountains", style={'color': '#8B7355'}),
                                html.Span("Geomorfología (PESO_GEOMO)", style={'marginLeft': '8px'})
                            ], className='parametro-item'),
                            
                            html.Div([
                                html.I(className="bi bi-triangle-fill", style={'color': '#FF8C00'}),
                                html.Span("Pendiente (gridcode)", style={'marginLeft': '8px'})
                            ], className='parametro-item'),
                            
                            html.Div([
                                html.I(className="bi bi-cloud-rain-fill", style={'color': '#4169E1'}),
                                html.Span("Precipitación Máxima (PESO_PPMAX)", style={'marginLeft': '8px'})
                            ], className='parametro-item'),
                        ], className='parametros-info')
                    ])
                ])
            ], className='shadow-lg border-0 animated')
        ], md=5, lg=4),
        
        # Panel de resultados derecho
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(
                        id='map-container',
                        children=[
                            dbc.Alert([
                                html.Div([
                                    html.I(className="bi bi-hourglass-split hourglass-spin", 
                                          style={'fontSize': '4rem', 'color': '#7CB342'}),
                                ], className='text-center mb-3'),
                                html.H4("Esperando Generación", className="alert-heading text-center", style={'color': '#33691E', 'fontWeight': '700'}),
                                html.P("Configure los parámetros en el panel izquierdo y haga clic en 'Generar Mapa' para comenzar.", 
                                      className='text-center mb-0', style={'color': '#558B2F'})
                            ], color="light", className='border-0 mb-4', style={'background': 'linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 100%)'})
                        ],
                        className="result-panel"
                    ),
                    
                    html.Hr(style={'borderTop': '2px dashed #C5E1A5', 'margin': '20px 0'}),
                    
                    dbc.Row([
                        # COLUMNA IZQUIERDA - Resumen de selección
                        dbc.Col([
                            html.Div([
                                html.H5([
                                    html.I(className="bi bi-clipboard-check me-2", style={'color': '#7CB342'}),
                                    "Resumen"
                                ], className='mb-3', style={'color': '#33691E', 'fontWeight': '800'}),
                                html.Div(
                                    id='selection-summary',
                                    children=[
                                        dbc.Alert([
                                            html.I(className="bi bi-info-circle me-2"),
                                            "Complete todos los campos para continuar"
                                        ], color="light", className='mb-0')
                                    ],
                                    className='selection-summary'
                                )
                            ])
                        ], md=6, className='pe-2'),
                        
                        # COLUMNA DERECHA - Botones de acción
                        dbc.Col([
                            dbc.Button([
                                html.I(className="bi bi-rocket-takeoff me-2"),
                                'Generar Mapa de Riesgo'
                            ],
                            id='generate-map-button',
                            color='success',
                            size='lg',
                            className='w-100 mb-3',
                            disabled=True),
                            
                            dbc.Button([
                                html.I(className="bi bi-download me-2"),
                                'Descargar Mapa'
                            ],
                            id='download-button',
                            color='info',
                            size='lg',
                            className='w-100 mb-3',
                            disabled=True)
                        ], md=6, className='ps-2')
                    ], className='g-0')
                ])
            ], className="h-100 shadow-lg border-0 animated")
        ], md=7, lg=8)
    ], className='g-4')
], fluid=True, className="p-4")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='loading-state', storage_type='memory', data=False),
    html.Div(id='page-content')
])

# ==================== CALLBACKS ====================
@app.callback(Output('page-content', 'children'), Input('session-store', 'data'))
def display_page(session_data): 
    return dashboard_layout if session_data and session_data.get('logged_in') else login_layout

@app.callback(
    Output('session-store', 'data'), 
    Output('login-alert', 'children'), 
    Input('login-button', 'n_clicks'), 
    State('username-input', 'value'), 
    State('password-input', 'value'), 
    prevent_initial_call=True
)
def login_user(n_clicks, username, password):
    if not username or not password: 
        return {'logged_in': False}, dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "Por favor, complete todos los campos"
        ], color="warning")
    if username in VALID_USERS and VALID_USERS[username] == password: 
        return {'logged_in': True, 'username': username}, None
    return {'logged_in': False}, dbc.Alert([
        html.I(className="bi bi-x-circle me-2"),
        "Usuario o contraseña incorrectos"
    ], color="danger")

@app.callback(
    Output('session-store', 'data', allow_duplicate=True), 
    Input('logout-button', 'n_clicks'), 
    prevent_initial_call=True
)
def logout_user(n_clicks): 
    return {'logged_in': False}

@app.callback(Output('user-display-nav', 'children'), Input('session-store', 'data'))
def display_user_nav(session_data): 
    return [
        html.I(className="bi bi-person-circle me-2"),
        session_data.get('username', 'Usuario')
    ] if session_data and session_data.get('logged_in') else None

@app.callback(
    Output('provincia-dropdown', 'options'), 
    Output('provincia-dropdown', 'disabled'), 
    Output('provincia-dropdown', 'value'), 
    Input('departamento-dropdown', 'value')
)
def update_provincias(departamento):
    if departamento: 
        return [{'label': prov, 'value': prov} for prov in sorted(PROVINCIAS_POR_DEPA.get(departamento, []))], False, None
    return [], True, None

@app.callback(
    Output('distrito-dropdown', 'options'), 
    Output('distrito-dropdown', 'disabled'), 
    Output('distrito-dropdown', 'value'), 
    Input('provincia-dropdown', 'value')
)
def update_distritos(provincia):
    if provincia: 
        return [{'label': dist, 'value': dist} for dist in sorted(DISTRITOS_POR_PROV.get(provincia, []))], False, None
    return [], True, None

@app.callback(
    Output('generate-map-button', 'disabled'), 
    Output('download-button', 'disabled'),
    [Input(c, 'value') for c in ['user-name-input', 'departamento-dropdown', 'provincia-dropdown', 'distrito-dropdown']],
    Input('loading-state', 'data')
)
def enable_buttons(*values): 
    loading_state = values[-1]
    form_values = values[:-1]
    
    # Si está cargando, deshabilitar todos los botones
    if loading_state:
        return True, True
    
    # Si no está cargando, habilitar según los valores del formulario
    all_filled = all(form_values)
    return not all_filled, not all_filled

@app.callback(
    Output('selection-summary', 'children'), 
    [Input(c, 'value') for c in ['user-name-input', 'departamento-dropdown', 'provincia-dropdown', 'distrito-dropdown']]
)
def update_summary(user_name, departamento, provincia, distrito):
    if not any([user_name, departamento, provincia, distrito]): 
        return dbc.Alert([
            html.I(className="bi bi-info-circle me-2"),
            "Complete todos los campos para continuar"
        ], color="light", className='mb-0')
    
    summary_items = []
    if user_name: summary_items.append(html.Div([
        html.I(className="bi bi-person-fill me-2", style={'color': '#7CB342'}),
        html.Strong("Usuario: "),
        user_name
    ], className='mb-2'))
    if departamento: summary_items.append(html.Div([
        html.I(className="bi bi-geo-alt-fill me-2", style={'color': '#7CB342'}),
        html.Strong("Departamento: "),
        departamento
    ], className='mb-2'))
    if provincia: summary_items.append(html.Div([
        html.I(className="bi bi-building me-2", style={'color': '#7CB342'}),
        html.Strong("Provincia: "),
        provincia
    ], className='mb-2'))
    if distrito: summary_items.append(html.Div([
        html.I(className="bi bi-house-fill me-2", style={'color': '#7CB342'}),
        html.Strong("Distrito: "),
        distrito
    ], className='mb-2'))
    
    return html.Div(summary_items)

# Callback para activar el estado de carga al presionar el botón
@app.callback(
    Output('loading-state', 'data', allow_duplicate=True),
    Output('generate-map-button', 'children', allow_duplicate=True),
    Input('generate-map-button', 'n_clicks'),
    prevent_initial_call=True
)
def activate_loading(n_clicks):
    """Activa el estado de carga cuando se presiona el botón"""
    return True, [
        html.I(className="bi bi-hourglass-split hourglass-spin me-2"),
        'Procesando...'
    ]

# Callback de generación con estado de carga
@app.callback(
    Output('map-container', 'children'),
    Output('map-filepath-store', 'data'),
    Output('loading-state', 'data'),
    Output('generate-map-button', 'children'),
    Input('generate-map-button', 'n_clicks'),
    [State('user-name-input', 'value'),
     State('departamento-dropdown', 'value'),
     State('provincia-dropdown', 'value'),
     State('distrito-dropdown', 'value')],
    prevent_initial_call=True
)
def generate_and_save_map_callback(n_clicks, user_name, departamento, provincia, distrito):
    """
    Genera el mapa de riesgo consolidado con los 4 parámetros
    """
    ruta_guardado = None
    button_text = [
        html.I(className="bi bi-rocket-takeoff me-2"),
        'Generar Mapa de Riesgo'
    ]
    
    try:
        print(f"\n{'='*80}")
        print(f"🗺️ GENERANDO MAPA DE RIESGO CONSOLIDADO")
        print(f"   Usuario: {user_name}")
        print(f"   Ubicación: {distrito}, {provincia}, {departamento}")
        print(f"{'='*80}\n")
        
        # Validar que los parámetros no sean None
        if not all([user_name, departamento, provincia, distrito]):
            error_msg = f"Parámetros incompletos:\n- Usuario: {user_name}\n- Depto: {departamento}\n- Provincia: {provincia}\n- Distrito: {distrito}"
            print(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        print(f"✓ Parámetros validados correctamente")
        print(f"  - Usuario: {user_name}")
        print(f"  - Departamento: {departamento}")
        print(f"  - Provincia: {provincia}")
        print(f"  - Distrito: {distrito}\n")
        
        # Generar mapa de riesgo consolidado
        ruta_guardado = generar_mapa_riesgo_consolidado(
            user_name, 
            departamento, 
            provincia, 
            distrito
        )
        
        if ruta_guardado and os.path.exists(ruta_guardado):
            file_size_mb = os.path.getsize(ruta_guardado) / (1024 * 1024)
            
            success_alert = html.Div([
                dbc.Alert([
                    html.Div([
                        html.I(className="bi bi-check-circle-fill success-icon", style={'fontSize': '4rem'})
                    ], className='text-center mb-3'),
                    html.H4("¡Mapa de Riesgo Generado Exitosamente!", 
                           className="alert-heading text-center",
                           style={'color': '#33691E', 'fontWeight': '800'}),
                    html.Hr(style={'borderColor': '#7CB342'}),
                    html.Div([
                        html.I(className="bi bi-file-earmark-image me-2", style={'color': '#558B2F'}),
                        html.Strong("Archivo: ", style={'color': '#33691E'}),
                        html.Code(os.path.basename(ruta_guardado), 
                                 style={'fontSize': '0.9em', 'background': '#F1F8E9', 'padding': '4px 8px', 'borderRadius': '6px'})
                    ], className='mb-2'),
                    html.Div([
                        html.I(className="bi bi-hdd me-2", style={'color': '#558B2F'}),
                        html.Strong("Tamaño: ", style={'color': '#33691E'}),
                        f"{file_size_mb:.2f} MB"
                    ], className='mb-3'),
                    html.Div([
                        html.I(className="bi bi-info-circle me-2", style={'color': '#7CB342'}),
                        html.Strong("Índice calculado como: ", style={'color': '#33691E'}),
                        html.Br(),
                        html.Code("(Ríos + Geomorfología + Pendiente + Precipitación) / 4", 
                                 style={'fontSize': '0.85em', 'background': '#F1F8E9', 'padding': '8px', 'borderRadius': '6px', 'display': 'block', 'marginTop': '8px'})
                    ], className='mb-2')
                ], color="success", className='border-0 mb-3'),
                
                html.Div([
                    html.H5([
                        html.I(className="bi bi-arrow-down-circle-fill me-2", style={'color': '#7CB342'}),
                        "Descargar Mapa"
                    ], className='text-center mb-3', style={'color': '#33691E', 'fontWeight': '700'}),
                    html.P("Haz clic en el botón 'Descargar Mapa' para obtener el archivo PNG de alta resolución (300 DPI).",
                          className='text-center mb-0', style={'color': '#558B2F', 'fontSize': '0.95rem'})
                ], className='download-section')
            ])
            
            button_text = [
                html.I(className="bi bi-rocket-takeoff me-2"),
                'Generar Mapa de Riesgo'
            ]
            
            print(f"✅ Mapa guardado exitosamente en: {ruta_guardado}")
            
            return success_alert, ruta_guardado, False, button_text
        else:
            error_alert = dbc.Alert([
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill", style={'fontSize': '3rem', 'color': '#EF6C00'})
                ], className='text-center mb-3'),
                html.H4("Error al Generar Mapa", className="alert-heading text-center", style={'fontWeight': '700'}),
                html.Hr(),
                html.P("No se pudo generar el mapa de riesgo correctamente.", className='text-center'),
                html.Div([
                    html.Strong("Verifica:"),
                    html.Ul([
                        html.Li("Que los shapefiles de peligro estén disponibles:"),
                        html.Li("   • geomorfo_cusco_peso.shp"),
                        html.Li("   • PENDIENTE_PESO.shp"),
                        html.Li("   • CPE_TR_50_clasificado_PPMAX.shp"),
                        html.Li("Que exista el archivo DEM.tif para ríos"),
                        html.Li("Que el distrito seleccionado sea correcto"),
                        html.Li("Revisa los logs en la terminal para más detalles")
                    ])
                ], className='mt-3')
            ], color="danger", className='border-0')
            
            button_text = [
                html.I(className="bi bi-rocket-takeoff me-2"),
                'Generar Mapa de Riesgo'
            ]
            
            print(f"❌ No se pudo generar el mapa")
            
            return error_alert, None, False, button_text
            
    except FileNotFoundError as e:
        error_alert = dbc.Alert([
            html.Div([
                html.I(className="bi bi-file-excel-fill", style={'fontSize': '3rem', 'color': '#FB8C00'})
            ], className='text-center mb-3'),
            html.H4("Archivo No Encontrado", className="alert-heading text-center", style={'fontWeight': '700'}),
            html.Hr(),
            html.P(f"No se pudo localizar el archivo necesario:", className='text-center'),
            html.Code(str(e), style={'background': '#FFF8E1', 'padding': '12px', 'borderRadius': '6px', 'display': 'block'})
        ], color="warning", className='border-0')
        
        button_text = [
            html.I(className="bi bi-rocket-takeoff me-2"),
            'Generar Mapa de Riesgo'
        ]
        
        print(f"❌ Error de archivo: {str(e)}")
        
        return error_alert, None, False, button_text
        
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"\n❌ ERROR DE ARCHIVO: {error_msg}")
        import traceback
        traceback.print_exc()
        
        error_alert = dbc.Alert([
            html.Div([
                html.I(className="bi bi-file-excel-fill", style={'fontSize': '3rem', 'color': '#FB8C00'})
            ], className='text-center mb-3'),
            html.H4("Archivo No Encontrado", className="alert-heading text-center", style={'fontWeight': '700'}),
            html.Hr(),
            html.P("No se pudo localizar un archivo requerido:", className='text-center'),
            html.Code(error_msg, style={'background': '#FFF8E1', 'padding': '12px', 'borderRadius': '6px', 'display': 'block', 'fontSize': '0.85em', 'marginTop': '10px'}),
            html.P("Verifica las rutas de los archivos de peligro.", className='text-center mb-0 text-muted', style={'marginTop': '12px'})
        ], color="warning", className='border-0')
        
        return error_alert, None, False, button_text
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n{'='*80}")
        print(f"❌ ERROR INESPERADO AL GENERAR MAPA")
        print(f"{'='*80}")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {error_msg}")
        print(f"{'='*80}\n")
        import traceback
        traceback.print_exc()
        
        error_alert = dbc.Alert([
            html.Div([
                html.I(className="bi bi-x-octagon-fill", style={'fontSize': '3rem', 'color': '#C62828'})
            ], className='text-center mb-3'),
            html.H4("Error Inesperado", className="alert-heading text-center", style={'fontWeight': '700'}),
            html.Hr(),
            html.Div([
                html.P("Tipo de error:", className='mb-1 font-weight-bold'),
                html.Code(type(e).__name__, style={'background': '#FFEBEE', 'padding': '6px 12px', 'borderRadius': '4px', 'fontSize': '0.9em'}),
            ], className='mb-3'),
            html.Div([
                html.P("Descripción:", className='mb-1 font-weight-bold'),
                html.Code(error_msg, style={'background': '#FFEBEE', 'padding': '12px', 'borderRadius': '4px', 'display': 'block', 'fontSize': '0.85em', 'whiteSpace': 'pre-wrap', 'wordBreak': 'break-word'}),
            ]),
            html.P("Revisa la consola (terminal) para ver el traceback completo.", className='text-center mb-0 text-muted', style={'marginTop': '12px', 'fontSize': '0.9em'})
        ], color="danger", className='border-0')
        
        return error_alert, None, False, button_text

@app.callback(
    Output('download-map-image', 'data'),
    Input('download-button', 'n_clicks'),
    State('map-filepath-store', 'data'),
    prevent_initial_call=True
)
def download_map(n_clicks, filepath):
    if not n_clicks or not filepath or not os.path.exists(filepath):
        return None
    try:
        print(f"📥 Iniciando descarga de: {filepath}")
        return dcc.send_file(filepath)
    except Exception as e:
        print(f"❌ Error al descargar archivo: {e}")
        return None

if __name__ == '__main__':
    try:
        import geopandas, contextily, matplotlib_scalebar, rasterio, whitebox
        print("✅ Librerías geoespaciales detectadas correctamente")
    except ImportError as e:
        print(f"\n{'='*80}")
        print(" FALTAN LIBRERÍAS GEOESPACIALES ".center(80, "!"))
        print(f"{'='*80}\n")
    
    print(f"\n{'='*80}")
    print("🔍 VERIFICANDO ARCHIVOS REQUERIDOS PARA ANÁLISIS".center(80))
    print(f"{'='*80}")
    
    ruta_base = "/workspaces/SIG-AUTOMATIZACION/PRUEBA"
    archivos_requeridos = [
        ("/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PENDIENTES/DEM.tif", "DEM para Ríos"),
        ("/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/GEOMORFOLOGIA/geomorfo_cusco_peso.shp", "Geomorfología"),
        ("/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PENDIENTE/PENDIENTE_PESO.shp", "Pendiente"),
        ("/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PP_MAX/CPE_TR_50_clasificado_PPMAX.shp", "Precipitación Máxima"),
    ]
    
    for ruta, nombre in archivos_requeridos:
        if os.path.exists(ruta):
            size_mb = os.path.getsize(ruta) / (1024*1024) if os.path.isfile(ruta) else "Shapefile"
            print(f"✅ {nombre:30} - Encontrado")
        else:
            print(f"⚠️  {nombre:30} - NO ENCONTRADO: {ruta}")
    
    print(f"{'='*80}\n")
    
    print(f"\n{'='*80}")
    print("🚀 INICIANDO SERVIDOR DASH - ANÁLISIS DE PELIGRO MULTICRITERIO".center(80))
    print(f"{'='*80}")
    print("🎨 Paleta de colores: Verde")
    print("📊 Análisis: Índice de Riesgo Consolidado (4 Parámetros)")
    print("📐 Fórmula: (Ríos + Geomorfología + Pendiente + Precipitación) / 4")
    print("🎯 Clases de Riesgo: Muy Bajo, Bajo, Medio, Alto, Muy Alto")
    print("📍 Puerto: 8051")
    print("🌐 URL: http://127.0.0.1:8051")
    print(f"{'='*80}\n")
    
    app.run(debug=True, port=8051)