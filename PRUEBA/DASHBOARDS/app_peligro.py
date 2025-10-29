# Archivo: app_peligro.py - DASHBOARD PARA MAPA DE PELIGRO (TEMA OSCURO)

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import re
import os

# Importar la función del mapa de peligro
from mapa_peligro import generar_mapa_peligro

# ==================== CONFIGURACIÓN DE LA APP ====================
app = Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.DARKLY,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
    ], 
    suppress_callback_exceptions=True
)

# Inyectar CSS con tema TOTALMENTE NEGRO
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Variables de color - TEMA NEGRO */
            :root {
                --negro-principal: #000000;
                --negro-secundario: #0a0a0a;
                --negro-terciario: #1a1a1a;
                --gris-oscuro: #2a2a2a;
                --gris-medio: #3a3a3a;
                --rojo-peligro: #FF3B3B;
                --rojo-oscuro: #CC0000;
                --gris-texto: #e0e0e0;
            }
            
            /* Fuente moderna */
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            /* Fondo negro total */
            body {
                background: var(--negro-principal) !important;
                min-height: 100vh;
                color: var(--gris-texto) !important;
            }
            
            /* Cards con fondo negro */
            .card {
                background: var(--negro-secundario) !important;
                border: 2px solid var(--gris-medio) !important;
                box-shadow: 0 10px 40px rgba(255, 59, 59, 0.2) !important;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border-radius: 16px !important;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 50px rgba(255, 59, 59, 0.4) !important;
                border-color: var(--rojo-peligro) !important;
            }
            
            /* Inputs oscuros */
            .form-control, .form-select {
                background: var(--negro-terciario) !important;
                border: 2px solid var(--gris-oscuro) !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                transition: all 0.3s ease;
                color: var(--gris-texto) !important;
            }
            
            .form-control:focus, .form-select:focus {
                border-color: var(--rojo-peligro) !important;
                box-shadow: 0 0 0 3px rgba(255, 59, 59, 0.2) !important;
                transform: translateY(-2px);
                background: var(--negro-secundario) !important;
                color: white !important;
            }
            
            /* Opciones del dropdown */
            .Select-menu-outer, .VirtualizedSelectOption {
                background: var(--negro-terciario) !important;
                color: var(--gris-texto) !important;
            }
            
            /* Botón Generar Mapa - Rojo */
            .btn-success {
                background: linear-gradient(135deg, var(--rojo-peligro) 0%, var(--rojo-oscuro) 100%) !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 14px 28px !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(255, 59, 59, 0.4) !important;
                color: white !important;
            }
            
            .btn-success:hover:not(:disabled) {
                background: linear-gradient(135deg, #FF5555 0%, var(--rojo-peligro) 100%) !important;
                transform: translateY(-3px);
                box-shadow: 0 6px 30px rgba(255, 59, 59, 0.6) !important;
            }
            
            .btn-success:disabled {
                background: linear-gradient(135deg, var(--gris-oscuro) 0%, var(--negro-terciario) 100%) !important;
                opacity: 0.5;
                cursor: wait !important;
                box-shadow: none !important;
                animation: pulse-loading 1.5s ease-in-out infinite;
            }
            
            /* Botón Descargar - Rojo oscuro */
            .btn-info {
                background: linear-gradient(135deg, var(--rojo-oscuro) 0%, #990000 100%) !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 14px 28px !important;
                font-weight: 700 !important;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px rgba(204, 0, 0, 0.4) !important;
                color: white !important;
            }
            
            .btn-info:hover:not(:disabled) {
                background: linear-gradient(135deg, #BB0000 0%, var(--rojo-oscuro) 100%) !important;
                transform: translateY(-3px);
                box-shadow: 0 6px 30px rgba(204, 0, 0, 0.6) !important;
            }
            
            .btn-info:disabled {
                background: linear-gradient(135deg, var(--gris-oscuro) 0%, var(--negro-terciario) 100%) !important;
                opacity: 0.5;
                cursor: wait !important;
            }
            
            /* Botón Logout */
            .btn-danger {
                background: linear-gradient(135deg, var(--rojo-peligro) 0%, var(--rojo-oscuro) 100%) !important;
                border: none !important;
                border-radius: 8px !important;
                transition: all 0.3s ease;
                font-weight: 600 !important;
            }
            
            /* Navbar oscuro */
            .navbar {
                background: var(--negro-secundario) !important;
                border-bottom: 2px solid var(--gris-oscuro);
                box-shadow: 0 4px 20px rgba(255, 59, 59, 0.15);
            }
            
            .navbar-brand {
                font-weight: 800 !important;
                font-size: 1.3rem !important;
                letter-spacing: 0.5px !important;
                color: var(--gris-texto) !important;
            }
            
            /* Labels con estilo rojo */
            label {
                color: var(--rojo-peligro);
                font-weight: 700;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-bottom: 8px;
            }
            
            /* Alertas oscuras */
            .alert {
                border-radius: 16px !important;
                border: none !important;
                padding: 24px !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
            }
            
            .alert-success {
                background: linear-gradient(135deg, var(--negro-terciario) 0%, var(--gris-oscuro) 100%) !important;
                border-left: 5px solid var(--rojo-peligro) !important;
                color: var(--gris-texto) !important;
            }
            
            .alert-danger {
                background: linear-gradient(135deg, var(--negro-terciario) 0%, #2a0000 100%) !important;
                border-left: 5px solid var(--rojo-peligro) !important;
                color: var(--gris-texto) !important;
            }
            
            .alert-warning {
                background: linear-gradient(135deg, var(--negro-terciario) 0%, #2a1a00 100%) !important;
                border-left: 5px solid #FFA000 !important;
                color: var(--gris-texto) !important;
            }
            
            .alert-light {
                background: var(--negro-terciario) !important;
                border-left: 5px solid var(--gris-medio) !important;
                color: var(--gris-texto) !important;
            }
            
            /* Hr decorativo */
            hr {
                border-top: 2px solid var(--gris-oscuro) !important;
                opacity: 1;
                margin: 24px 0 !important;
            }
            
            /* Resumen de selección */
            .selection-summary {
                background: var(--negro-terciario);
                padding: 20px;
                border-radius: 12px;
                border-left: 5px solid var(--rojo-peligro);
                color: var(--gris-texto);
            }
            
            /* Login container */
            .login-container {
                background: var(--negro-secundario);
                border-radius: 20px;
                padding: 50px;
                box-shadow: 0 25px 70px rgba(255, 59, 59, 0.3);
                border: 2px solid var(--gris-medio);
            }
            
            /* Animación de rotación para el logo */
            @keyframes logoRotation {
                from { transform: rotateY(0deg); }
                to { transform: rotateY(360deg); }
            }
            
            .logo-rotation {
                animation: logoRotation 4s linear infinite;
                filter: drop-shadow(0 4px 10px rgba(255, 59, 59, 0.5));
            }
            
            .logo-rotation:hover {
                animation-duration: 1.5s;
            }
            
            /* Animación de rotación para el icono de reloj */
            @keyframes hourglassSpin {
                0% { transform: rotateZ(0deg); }
                50% { transform: rotateZ(180deg); }
                100% { transform: rotateZ(360deg); }
            }
            
            .hourglass-spin {
                display: inline-block;
                animation: hourglassSpin 2s linear infinite;
            }
            
            /* Animación de pulso para botones en carga */
            @keyframes pulse-loading {
                0%, 100% { 
                    opacity: 0.5;
                    transform: scale(1);
                }
                50% { 
                    opacity: 0.7;
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
            
            /* Scrollbar personalizado negro */
            ::-webkit-scrollbar {
                width: 12px;
            }
            
            ::-webkit-scrollbar-track {
                background: var(--negro-principal);
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(135deg, var(--gris-oscuro) 0%, var(--gris-medio) 100%);
                border-radius: 6px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(135deg, var(--gris-medio) 0%, var(--rojo-oscuro) 100%);
            }
            
            /* Icono de éxito rojo */
            .success-icon {
                color: var(--rojo-peligro);
            }
            
            /* Panel de control header */
            .panel-header {
                color: var(--gris-texto) !important;
            }
            
            /* Sección de descarga */
            .download-section {
                background: var(--negro-terciario);
                padding: 20px;
                border-radius: 12px;
                border: 2px dashed var(--rojo-peligro);
                margin-top: 15px;
            }
            
            /* Contact footer oscuro */
            .contact-footer {
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: var(--negro-secundario);
                padding: 15px 20px;
                border-radius: 12px;
                border: 2px solid var(--gris-oscuro);
                box-shadow: 0 4px 20px rgba(255, 59, 59, 0.2);
                z-index: 1000;
                transition: all 0.3s ease;
            }
            
            .contact-footer:hover {
                background: var(--negro-terciario);
                transform: translateY(-3px);
                box-shadow: 0 6px 25px rgba(255, 59, 59, 0.4);
                border-color: var(--rojo-peligro);
            }
            
            .contact-footer a {
                color: var(--gris-texto);
                text-decoration: none;
                font-weight: 600;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }
            
            .contact-footer a:hover {
                color: var(--rojo-peligro);
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
    if not all([depa_data, prov_data, dist_data]): raise ValueError("Archivos SQL no encontrados.")
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
    LISTA_DEPARTAMENTOS, PROVINCIAS_POR_DEPA, DISTRITOS_POR_PROV = ['LIMA'], {'LIMA': ['LIMA']}, {'LIMA': ['MIRAFLORES']}

# ==================== LAYOUT DE LOGIN ====================
login_layout = dbc.Container([
    # Footer de contactos
    html.Div([
        html.A([
            html.I(className="bi bi-globe2"),
            "escuelar.org"
        ], href="https://escuelar.org/", target="_blank"),
        html.Span(" | ", style={'color': '#FF3B3B', 'fontWeight': '700'}),
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
                
                html.H2("MAPA DE SUSCEPTIBILIDAD - PLATAFORMA DE ANÁLISIS", 
                       className="text-center mb-4",
                       style={
                           'color': "#e0e0e0", 
                           'fontWeight': '800',
                           'fontSize': '1.8rem',
                           'letterSpacing': '0.5px'
                       }),
                
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Label([
                                html.I(className="bi bi-person-fill me-2"),
                                "Usuario"
                            ]),
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
                            ]),
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
        html.Span(" | ", style={'color': '#FF3B3B', 'fontWeight': '700'}),
        html.A([
            html.I(className="bi bi-linkedin"),
            "LinkedIn"
        ], href="https://www.linkedin.com/company/escuelar/about/", target="_blank")
    ], className='contact-footer'),
    
    # Navbar oscuro
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                html.Span(
                    id='user-display-nav',
                    className='navbar-text me-3',
                    style={'color': '#e0e0e0', 'fontWeight': '600', 'fontSize': '1rem'}
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
                className='navbar-logo',
                style={'height': '40px', 'marginRight': '15px'}
            ),
            "⚠️ Sistema de Mapas de Susceptibilidad"
        ],
        color="dark",
        dark=True,
        className='mb-4 shadow-sm navbar',
        style={'fontSize': '1.2rem'},
        fluid=True
    ),
    
    dbc.Row([
        # Panel de control izquierdo
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-exclamation-triangle me-2", style={'fontSize': '1.8rem', 'color': "#FF3B3B"}),
                        html.H4("Panel de Control", className='panel-header', style={'display': 'inline', 'fontWeight': '900'})
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
                                    placeholder='Ej: Daniel Porras Nuñez',
                                    className='mb-4'
                                )
                            ]),
                            
                            html.Hr(),
                            
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
                                          style={'fontSize': '4rem', 'color': '#FF3B3B'}),
                                ], className='text-center mb-3'),
                                html.H4("Esperando Generación", className="alert-heading text-center", 
                                       style={'fontWeight': '700'}),
                                html.P("Configure los parámetros en el panel izquierdo y haga clic en 'Generar Mapa de Susceptibilidad' para comenzar.", 
                                      className='text-center mb-0')
                            ], color="light", className='border-0 mb-4')
                        ],
                        className="result-panel"
                    ),
                    
                    html.Hr(),
                    
                    dbc.Row([
                        # COLUMNA IZQUIERDA - Resumen de selección
                        dbc.Col([
                            html.Div([
                                html.H5([
                                    html.I(className="bi bi-clipboard-check me-2", style={'color': '#FF3B3B'}),
                                    "Resumen de Selección"
                                ], className='mb-3', style={'fontWeight': '800'}),
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
                                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                                'Generar Mapa de Susceptibilidad'
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
        html.I(className="bi bi-person-fill me-2", style={'color': '#FF3B3B'}),
        html.Strong("Usuario: "),
        user_name
    ], className='mb-2'))
    if departamento: summary_items.append(html.Div([
        html.I(className="bi bi-geo-alt-fill me-2", style={'color': '#FF3B3B'}),
        html.Strong("Departamento: "),
        departamento
    ], className='mb-2'))
    if provincia: summary_items.append(html.Div([
        html.I(className="bi bi-building me-2", style={'color': '#FF3B3B'}),
        html.Strong("Provincia: "),
        provincia
    ], className='mb-2'))
    if distrito: summary_items.append(html.Div([
        html.I(className="bi bi-house-fill me-2", style={'color': '#FF3B3B'}),
        html.Strong("Distrito: "),
        distrito
    ], className='mb-2'))
    
    return html.Div(summary_items)

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
    ruta_guardado = None
    
    try:
        print(f"\n⚠️ Generando mapa de susceptibilidad para {distrito}...")
        ruta_guardado = generar_mapa_peligro(user_name, departamento, provincia, distrito)
        
        if ruta_guardado and os.path.exists(ruta_guardado):
            file_size_mb = os.path.getsize(ruta_guardado) / (1024 * 1024)
            
            success_alert = html.Div([
                dbc.Alert([
                    html.Div([
                        html.I(className="bi bi-check-circle-fill success-icon", style={'fontSize': '4rem'})
                    ], className='text-center mb-3'),
                    html.H4("¡Mapa de Susceptibilidad Generado Exitosamente!", 
                           className="alert-heading text-center",
                           style={'fontWeight': '800'}),
                    html.Hr(),
                    html.Div([
                        html.I(className="bi bi-file-earmark-image me-2", style={'color': '#FF3B3B'}),
                        html.Strong("Archivo: "),
                        html.Code(os.path.basename(ruta_guardado), 
                                 style={'fontSize': '0.9em', 'background': 'var(--negro-terciario)', 
                                       'padding': '4px 8px', 'borderRadius': '6px', 'color': '#e0e0e0'})
                    ], className='mb-2'),
                    html.Div([
                        html.I(className="bi bi-hdd me-2", style={'color': '#FF3B3B'}),
                        html.Strong("Tamaño: "),
                        f"{file_size_mb:.2f} MB"
                    ], className='mb-3'),
                    html.Div([
                        html.I(className="bi bi-info-circle me-2", style={'color': '#FF3B3B'}),
                        html.Strong("Parámetros combinados: "),
                        "Pendiente, Geomorfología, PP Máxima"
                    ], className='mb-2'),
                    html.Div([
                        html.I(className="bi bi-bar-chart me-2", style={'color': '#FF3B3B'}),
                        html.Strong("Clasificación: "),
                        "Baja, Media, Alta, Muy Alta (Tabla XX)"
                    ], className='mb-2'),
                ], color="success", className='border-0 mb-3'),
                
                html.Div([
                    html.H5([
                        html.I(className="bi bi-arrow-down-circle-fill me-2", style={'color': '#FF3B3B'}),
                        "Descargar Mapa"
                    ], className='text-center mb-3', style={'fontWeight': '700'}),
                    html.P("Haz clic en el botón 'Descargar Mapa' para obtener el archivo.",
                          className='text-center mb-0', style={'fontSize': '0.95rem'})
                ], className='download-section')
            ])
            
            button_text = [
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                'Generar Mapa de Susceptibilidad'
            ]
            
            print(f"\n✅ Retornando éxito al dashboard")
            print(f"   Ruta: {ruta_guardado}")
            print(f"   Tamaño: {file_size_mb:.2f} MB")
            
            return success_alert, ruta_guardado, False, button_text
        else:
            print(f"\n❌ El archivo no existe después de generarlo")
            print(f"   Ruta esperada: {ruta_guardado}")
            
            error_alert = dbc.Alert([
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill", style={'fontSize': '3rem', 'color': '#FFA000'})
                ], className='text-center mb-3'),
                html.H4("Error al Generar Mapa", className="alert-heading text-center", style={'fontWeight': '700'}),
                html.Hr(),
                html.P("No se pudo generar el mapa de susceptibilidad correctamente.", className='text-center'),
                html.Div([
                    html.Strong("Verifica:"),
                    html.Ul([
                        html.Li("Que existan los shapefiles de las 3 capas de peligro"),
                        html.Li("PENDIENTE_PESO.shp con columna PESO_PENDI"),
                        html.Li("geomorfo_cusco_peso.shp con columna PESO_GEOMO"),
                        html.Li("CPE_TR_50_clasificado_PPMAX.shp con columna PESO_PPMAX"),
                        html.Li("Que el distrito seleccionado tenga datos disponibles"),
                        html.Li("Los logs en la terminal para más detalles")
                    ])
                ], className='mt-3')
            ], color="danger", className='border-0')
            
            button_text = [
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                'Generar Mapa de Susceptibilidad'
            ]
            
            return error_alert, None, False, button_text
            
    except FileNotFoundError as e:
        error_alert = dbc.Alert([
            html.Div([
                html.I(className="bi bi-file-excel-fill", style={'fontSize': '3rem', 'color': '#FFA000'})
            ], className='text-center mb-3'),
            html.H4("Archivo No Encontrado", className="alert-heading text-center", style={'fontWeight': '700'}),
            html.Hr(),
            html.P(f"No se pudo localizar el archivo necesario: {str(e)}", className='text-center'),
            html.Div([
                html.Strong("Ubicaciones esperadas:"),
                html.Br(),
                html.Code("PENDIENTE_PESO.shp: /workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PENDIENTE/",
                         style={'background': 'var(--negro-terciario)', 'padding': '8px', 'borderRadius': '6px', 
                               'display': 'block', 'marginBottom': '8px'}),
                html.Code("geomorfo_cusco_peso.shp: /workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/GEOMORFOLOGIA/",
                         style={'background': 'var(--negro-terciario)', 'padding': '8px', 'borderRadius': '6px', 
                               'display': 'block', 'marginBottom': '8px'}),
                html.Code("CPE_TR_50_clasificado_PPMAX.shp: /workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PP_MAX/",
                         style={'background': 'var(--negro-terciario)', 'padding': '8px', 'borderRadius': '6px', 
                               'display': 'block'})
            ], className='mt-3 text-center')
        ], color="warning", className='border-0')
        
        button_text = [
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            'Generar Mapa de Peligro'
        ]
        
        return error_alert, None, False, button_text
        
    except Exception as e:
        print(f"❌ Excepción al generar mapa: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_alert = dbc.Alert([
            html.Div([
                html.I(className="bi bi-x-octagon-fill", style={'fontSize': '3rem', 'color': '#C62828'})
            ], className='text-center mb-3'),
            html.H4("Error Inesperado", className="alert-heading text-center", style={'fontWeight': '700'}),
            html.Hr(),
            html.P(f"Ocurrió un error: {str(e)}", className='text-center'),
            html.P("Revisa la consola para más detalles.", className='text-center mb-0')
        ], color="danger", className='border-0')
        
        button_text = [
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            'Generar Mapa de Peligro'
        ]
        
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
    print(f"\n{'='*80}")
    print("⚠️ VERIFICANDO ARCHIVOS DE PELIGRO".center(80))
    print(f"{'='*80}")
    
    # Verificar estructura de carpetas
    ruta_base_pendiente = "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PENDIENTE"
    ruta_base_geomorfo = "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/GEOMORFOLOGIA"
    ruta_base_ppmax = "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PELIGRO/PP_MAX"
    
    # Contar archivos de pendiente
    if os.path.exists(ruta_base_pendiente):
        pendiente_files = []
        for root, dirs, files in os.walk(ruta_base_pendiente):
            pendiente_files.extend([f for f in files if f.endswith('.shp')])
        print(f"✅ Carpeta PENDIENTE encontrada: {len(pendiente_files)} archivos .shp")
        if pendiente_files:
            print(f"   📋 Ejemplos: {', '.join(pendiente_files[:3])}")
    else:
        print("❌ ADVERTENCIA: Carpeta PENDIENTE no encontrada")
    
    # Contar archivos de geomorfología
    if os.path.exists(ruta_base_geomorfo):
        geomorfo_files = []
        for root, dirs, files in os.walk(ruta_base_geomorfo):
            geomorfo_files.extend([f for f in files if f.endswith('.shp')])
        print(f"✅ Carpeta GEOMORFOLOGÍA encontrada: {len(geomorfo_files)} archivos .shp")
        if geomorfo_files:
            print(f"   📋 Ejemplos: {', '.join(geomorfo_files[:3])}")
    else:
        print("❌ ADVERTENCIA: Carpeta GEOMORFOLOGÍA no encontrada")
    
    # Contar archivos de PP Máxima
    if os.path.exists(ruta_base_ppmax):
        ppmax_files = []
        for root, dirs, files in os.walk(ruta_base_ppmax):
            ppmax_files.extend([f for f in files if f.endswith('.shp')])
        print(f"✅ Carpeta PP_MAX encontrada: {len(ppmax_files)} archivos .shp")
        if ppmax_files:
            print(f"   📋 Ejemplos: {', '.join(ppmax_files[:3])}")
    else:
        print("❌ ADVERTENCIA: Carpeta PP_MAX no encontrada")
    
    print(f"{'='*80}\n")
    
    print(f"\n{'='*80}")
    print("🚀 INICIANDO SERVIDOR DASH - MAPA DE SUSCEPTIBILIDAD".center(80))
    print(f"{'='*80}")
    print("⚫ Tema: TOTALMENTE NEGRO")
    print("⚠️ Paleta de colores: Rojo (Susceptibilidad)")
    print("🎨 Interfaz oscura profesional")
    print("⏳ Indicador de carga visual con animaciones")
    print("📊 Combina: Pendiente + Geomorfología + PP Máxima")
    print("🔢 Fórmula: SUSCEPTIBILIDAD = (PESO_PENDI + PESO_GEOMO + PESO_PPMAX) / 3")
    print("🎯 Clasificación:")
    print("   🟢 BAJA: 1.00 - 2.00")
    print("   🟡 MEDIA: 2.00 - 3.00")
    print("   🟠 ALTA: 3.00 - 4.00")
    print("   🔴 MUY ALTA: 4.00 - 5.00")
    print("🔍 Búsqueda inteligente de archivos por provincia/departamento")
    print("🌐 Puerto: 8052")
    print("🔗 URL: http://127.0.0.1:8052")
    print(f"{'='*80}\n")
    
    app.run(debug=True, port=8052)