# Archivo: app.py

from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import re
import os

# Importamos la lógica de los diferentes tipos de mapas
from geografica_final import generar_mapa_final
from geomorfologia_final import generar_mapa_geomorfologia
from climatica_final import generar_mapa_climatica
from poblacion_final import generar_mapa_poblacion

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
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

try:
    ruta_departamentos = '/workspaces/GIT_PRUEBA_SIG/PRUEBA/DASHBOARDS/departamentos.sql'
    ruta_provincias = '/workspaces/GIT_PRUEBA_SIG/PRUEBA/DASHBOARDS/provincias.sql'
    ruta_distritos = '/workspaces/GIT_PRUEBA_SIG/PRUEBA/DASHBOARDS/distritos.sql'
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

login_layout = dbc.Container([dbc.Row(dbc.Col(html.Div([html.H2("🔐 Iniciar Sesión", className="text-center mb-4"), dbc.Card(dbc.CardBody([dbc.Input(id='username-input', placeholder='Usuario', type='text', className='mb-3'), dbc.Input(id='password-input', placeholder='Contraseña', type='password', className='mb-3'), dbc.Button('Ingresar', id='login-button', color='primary', className='w-100'), html.Div(id='login-alert', className='mt-3')]), className='shadow')], style={'marginTop': '100px', 'maxWidth': '400px', 'margin': '100px auto'})))], fluid=True)

dashboard_layout = dbc.Container([
    dcc.Download(id="download-map-image"),
    dcc.Store(id='map-filepath-store', storage_type='memory'),
    dbc.NavbarSimple(children=[dbc.NavItem(html.Span(id='user-display-nav', className='navbar-text me-3 text-white')), dbc.NavItem(dbc.Button("Cerrar Sesión", id='logout-button', color='danger', size='sm'))], brand="🗺️ Panel de Control de Mapas - Perú", color="primary", dark=True, className='mb-4'), 
    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("NOMBRE DE USUARIO", className='fw-bold mb-2'), 
                    dbc.Input(id='user-name-input', type='text', className='mb-4'), 
                    html.Label("TIPO DE MAPA", className='fw-bold mb-2'), 
                    dcc.Dropdown(
                        id='map-type', 
                        options=[
                            {'label': '🗺️ Mapa de Ubicación Geográfica', 'value': 'geografico'},
                            {'label': '🌄 Mapa de Geomorfología', 'value': 'geomorfologia'},
                            {'label': '🌡️ Mapa de Clasificación Climática', 'value': 'climatica'},
                            {'label': '🛣️ Mapa de Vías', 'value': 'vias'},
                            {'label': '🏘️ Mapa de Centros Poblados', 'value': 'centros'}
                        ], 
                        placeholder='Seleccione tipo de mapa', 
                        className='mb-4'
                    )
                ], md=6), 
                dbc.Col([
                    html.Label("DEPARTAMENTO", className='fw-bold mb-2'), 
                    dcc.Dropdown(id='departamento-dropdown', options=LISTA_DEPARTAMENTOS, placeholder='Seleccione', className='mb-4'), 
                    html.Label("PROVINCIA", className='fw-bold mb-2'), 
                    dcc.Dropdown(id='provincia-dropdown', placeholder='Primero elija Dpto.', disabled=True, className='mb-4'), 
                    html.Label("DISTRITO", className='fw-bold mb-2'), 
                    dcc.Dropdown(id='distrito-dropdown', placeholder='Primero elija Prov.', disabled=True, className='mb-4')
                ], md=6)
            ]), 
            html.Hr(), 
            html.H5("📋 Resumen de Selección:", className='mb-3'), 
            html.Div(id='selection-summary', children=[dbc.Alert("Complete el formulario para ver el resumen.", color="light")]), 
            html.Hr(), 
            dbc.Row([
                dbc.Col(dbc.Button('🚀 Generar y Guardar Mapa', id='generate-map-button', color='success', size='lg', className='w-100', disabled=True), md=6), 
                dbc.Col(dbc.Button('💾 Descargar Mapa Generado', id='download-button', color='info', size='lg', className='w-100', disabled=True), md=6)
            ])
        ])), md=5), 
        dbc.Col(dbc.Card(dbc.CardBody(id='map-container', children=[dbc.Alert([html.H4("Estado de Generación", className="alert-heading"), html.P("El resultado del proceso aparecerá aquí.")], color="info")], className="h-100"), className="h-100"), md=7)
    ])
], fluid=True, className="p-4")

app.layout = html.Div([dcc.Location(id='url', refresh=False), dcc.Store(id='session-store', storage_type='session'), html.Div(id='page-content')])

# CALLBACKS
@app.callback(Output('page-content', 'children'), Input('session-store', 'data'))
def display_page(session_data): return dashboard_layout if session_data and session_data.get('logged_in') else login_layout

@app.callback(Output('session-store', 'data'), Output('login-alert', 'children'), Input('login-button', 'n_clicks'), State('username-input', 'value'), State('password-input', 'value'), prevent_initial_call=True)
def login_user(n_clicks, username, password):
    if not username or not password: return {'logged_in': False}, dbc.Alert("⚠️ Ingrese usuario y contraseña.", color="warning")
    if username in VALID_USERS and VALID_USERS[username] == password: return {'logged_in': True, 'username': username}, None
    return {'logged_in': False}, dbc.Alert("❌ Datos incorrectos.", color="danger")

@app.callback(Output('session-store', 'data', allow_duplicate=True), Input('logout-button', 'n_clicks'), prevent_initial_call=True)
def logout_user(n_clicks): return {'logged_in': False}

@app.callback(Output('user-display-nav', 'children'), Input('session-store', 'data'))
def display_user_nav(session_data): return f"👤 {session_data.get('username', 'Usuario')}" if session_data and session_data.get('logged_in') else None

@app.callback(Output('provincia-dropdown', 'options'), Output('provincia-dropdown', 'disabled'), Output('provincia-dropdown', 'value'), Input('departamento-dropdown', 'value'))
def update_provincias(departamento):
    if departamento: return [{'label': prov, 'value': prov} for prov in sorted(PROVINCIAS_POR_DEPA.get(departamento, []))], False, None
    return [], True, None

@app.callback(Output('distrito-dropdown', 'options'), Output('distrito-dropdown', 'disabled'), Output('distrito-dropdown', 'value'), Input('provincia-dropdown', 'value'))
def update_distritos(provincia):
    if provincia: return [{'label': dist, 'value': dist} for dist in sorted(DISTRITOS_POR_PROV.get(provincia, []))], False, None
    return [], True, None

@app.callback(Output('generate-map-button', 'disabled'), Output('download-button', 'disabled'), [Input(c, 'value') for c in ['user-name-input', 'map-type', 'departamento-dropdown', 'provincia-dropdown', 'distrito-dropdown']])
def enable_buttons(*values): return not all(values), not all(values)

@app.callback(Output('selection-summary', 'children'), [Input(c, 'value') for c in ['user-name-input', 'map-type', 'departamento-dropdown', 'provincia-dropdown', 'distrito-dropdown']])
def update_summary(user_name, map_type, departamento, provincia, distrito):
    if not any([user_name, map_type, departamento, provincia, distrito]): return dbc.Alert("Complete el formulario.", color="light")
    map_types_dict = {
        'geografico': 'Ubicación Geográfica',
        'geomorfologia': 'Geomorfología',
        'climatica': 'Clasificación Climática',
        'vias': 'Vías',
        'centros': 'Centros Poblados'
    }
    summary_items = []
    if user_name: summary_items.append(html.Li(f"👤 Usuario: {user_name}"))
    if map_type: summary_items.append(html.Li(f"🗺️ Tipo: {map_types_dict.get(map_type, '')}"))
    if departamento: summary_items.append(html.Li(f"📍 Dpto: {departamento}"))
    if provincia: summary_items.append(html.Li(f"🏙️ Prov: {provincia}"))
    if distrito: summary_items.append(html.Li(f"🏘️ Dist: {distrito}"))
    return html.Ul(summary_items, className='list-unstyled')

# CALLBACK DE GENERACIÓN - CORREGIDO
@app.callback(
    Output('map-container', 'children'),
    Output('map-filepath-store', 'data'),
    Input('generate-map-button', 'n_clicks'),
    [State('user-name-input', 'value'),
     State('map-type', 'value'),
     State('departamento-dropdown', 'value'),
     State('provincia-dropdown', 'value'),
     State('distrito-dropdown', 'value')],
    prevent_initial_call=True
)
def generate_and_save_map_callback(n_clicks, user_name, map_type, departamento, provincia, distrito):
    ruta_guardado = None
    
    try:
        # LÓGICA SEGÚN EL TIPO DE MAPA SELECCIONADO
        if map_type == 'geografico':
            print(f"\n🗺️ Generando mapa geográfico para {distrito}...")
            ruta_guardado = generar_mapa_final(user_name, departamento, provincia, distrito)
        
        elif map_type == 'geomorfologia':
            print(f"\n🌄 Generando mapa de geomorfología para {distrito}...")
            ruta_guardado = generar_mapa_geomorfologia(user_name, departamento, provincia, distrito)
        
        elif map_type == 'climatica':
            print(f"\n🌡️ Generando mapa climático para {distrito}...")
            ruta_guardado = generar_mapa_climatica(user_name, departamento, provincia, distrito)
        
        elif map_type == 'vias':
            # PLACEHOLDER: Aquí irá la lógica para el mapa de vías
            return dbc.Alert([
                html.H4("🛣️ Mapa de Vías", className="alert-heading"),
                html.P("Esta funcionalidad está en desarrollo. Pronto estará disponible.")
            ], color="warning"), None
        
        elif map_type == 'centros':
            print(f"\n🏘️ Generando mapa de centros poblados para {distrito}...")
            ruta_guardado = generar_mapa_poblacion(user_name, departamento, provincia, distrito)
        
        # RESULTADO FINAL - VALIDACIÓN MEJORADA
        if ruta_guardado and os.path.exists(ruta_guardado):
            print(f"✅ Mapa generado exitosamente en: {ruta_guardado}")
            success_alert = dbc.Alert(
                [
                    html.H4("✅ ¡Éxito!", className="alert-heading"),
                    html.P("El mapa se ha generado y guardado correctamente."),
                    html.Hr(),
                    html.P("📂 Archivo guardado:", className="mb-1 fw-bold"),
                    html.Code(os.path.basename(ruta_guardado), style={'fontSize': '0.9em'}),
                    html.Hr(),
                    html.P("💡 Haz clic en 'Descargar Mapa Generado' para obtener el archivo.", className="mb-0")
                ],
                color="success"
            )
            return success_alert, ruta_guardado
        else:
            print(f"❌ Error: No se pudo generar el mapa o el archivo no existe")
            error_alert = dbc.Alert(
                [
                    html.H4("❌ Error al generar mapa", className="alert-heading"),
                    html.P("No se pudo generar el mapa correctamente."),
                    html.Hr(),
                    html.P("Verifica:", className="mb-1 fw-bold"),
                    html.Ul([
                        html.Li("Que los datos geográficos estén disponibles"),
                        html.Li("Que el distrito seleccionado sea correcto"),
                        html.Li("Los logs en la terminal para más detalles")
                    ])
                ],
                color="danger"
            )
            return error_alert, None
            
    except Exception as e:
        print(f"❌ Excepción al generar mapa: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_alert = dbc.Alert(
            [
                html.H4("❌ Error inesperado", className="alert-heading"),
                html.P(f"Ocurrió un error durante la generación: {str(e)}"),
                html.Hr(),
                html.P("Revisa la consola para más detalles.", className="mb-0")
            ],
            color="danger"
        )
        return error_alert, None

# CALLBACK PARA DESCARGA - CORREGIDO
@app.callback(
    Output('download-map-image', 'data'),
    Input('download-button', 'n_clicks'),
    State('map-filepath-store', 'data'),
    prevent_initial_call=True
)
def download_map(n_clicks, filepath):
    """Callback mejorado para descargar el mapa generado"""
    if not n_clicks:
        return None
    
    if not filepath:
        print("⚠️ No hay ruta de archivo almacenada")
        return None
    
    if not os.path.exists(filepath):
        print(f"⚠️ El archivo no existe: {filepath}")
        return None
    
    try:
        print(f"📥 Iniciando descarga de: {filepath}")
        return dcc.send_file(filepath)
    except Exception as e:
        print(f"❌ Error al descargar archivo: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    try:
        import geopandas, contextily, matplotlib_scalebar
        print("✅ Librerías geoespaciales detectadas correctamente")
    except ImportError:
        print("\n" + "="*80)
        print(" FALTAN LIBRERÍAS GEOESPACIALES ".center(80, "!"))
        print("Por favor, instálalas con:")
        print("pip install geopandas contextily matplotlib-scalebar")
        print("="*80 + "\n")
    
    print("\n" + "="*80)
    print("🚀 INICIANDO SERVIDOR DASH".center(80))
    print("="*80)
    print(f"📍 Puerto: 8051")
    print(f"🌐 URL: http://127.0.0.1:8051")
    print("="*80 + "\n")
    
    app.run(debug=True, port=8051)