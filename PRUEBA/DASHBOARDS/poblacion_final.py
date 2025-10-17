# -*- coding: utf-8 -*-
"""poblacion_final.py - VERSIÓN CORREGIDA CON RÍOS Y VÍAS VECINALES VISIBLES"""

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib_scalebar.scalebar import ScaleBar
import os
import numpy as np
import matplotlib.patheffects as path_effects
from shapely.geometry import box
import pyproj
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Polygon, Rectangle, Patch
from matplotlib.lines import Line2D
import datetime

# --- RUTA BASE ---
ruta_base = "/workspaces/SIG-AUTOMATIZACION/PRUEBA"
AMARILLO_CLARO = "#FFEE58"

# ════════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA CARGAR CENTROS POBLADOS
# ════════════════════════════════════════════════════════════════════════
def cargar_centros_poblados():
    """Carga el shapefile de centros poblados"""
    ruta_directa = f"{ruta_base}/DATA/CENTROS POBLADOS/Centros_Poblados_INEI_geogpsperu_SuyoPomalia.shp"

    if os.path.exists(ruta_directa):
        try:
            print(f"📂 Encontrado en: {ruta_directa}")
            gdf_cp = gpd.read_file(ruta_directa)
            if gdf_cp.crs is None:
                gdf_cp.set_crs(epsg=4326, inplace=True)
            gdf_cp = gdf_cp.to_crs(epsg=3857)
            print(f"✅ Centros Poblados cargados: {len(gdf_cp)} registros")
            return gdf_cp
        except Exception as e:
            print(f"❌ Error cargando desde ruta directa: {e}")

    print(f"❌ No se encontraron centros poblados en {ruta_base}/DATA")
    return None

# ════════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA CARGAR RÍOS - RUTA DIRECTA
# ════════════════════════════════════════════════════════════════════════
def cargar_rios():
    """Carga el shapefile de ríos desde ruta directa"""
    ruta_directa = "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/MAPA DE UBICACION/RIOS/Rios_lineal_IGN_IDEP_geogpsperu_SuyoPomalia.shp"
    
    if os.path.exists(ruta_directa):
        try:
            print(f"📂 Ríos encontrado en: {ruta_directa}")
            gdf_rios = gpd.read_file(ruta_directa)
            print(f"   → CRS original: {gdf_rios.crs}")
            print(f"   → Registros totales: {len(gdf_rios)}")
            
            if gdf_rios.crs is None:
                gdf_rios.set_crs(epsg=4326, inplace=True)
                print(f"   → Asignado CRS 4326")
            
            gdf_rios = gdf_rios.to_crs(epsg=3857)
            print(f"✅ Ríos cargados y proyectados: {len(gdf_rios)} registros")
            return gdf_rios
        except Exception as e:
            print(f"❌ Error cargando ríos: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Archivo de ríos NO encontrado en: {ruta_directa}")
    
    return None

# ════════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA CARGAR VÍAS - RUTAS DIRECTAS
# ════════════════════════════════════════════════════════════════════════
def cargar_vias():
    """Carga los shapefiles de vías desde rutas directas"""
    vias = {
        'nacional': None,
        'departamental': None,
        'vecinal': None
    }

    rutas = {
        'nacional': f"{ruta_base}/DATA/MAPA DE UBICACION/VIAS/VIA NACIONAL/red_vial_nacional_dic18.shp",
        'departamental': f"{ruta_base}/DATA/MAPA DE UBICACION/VIAS/VIA DEPARTAMENTAL/red_vial_departamental_dic18.shp",
        'vecinal': f"{ruta_base}/DATA/MAPA DE UBICACION/VIAS/VIA VECINAL/red_vial_vecinal_dic18.shp"
    }

    for tipo, ruta in rutas.items():
        if os.path.exists(ruta):
            try:
                print(f"📂 Vía {tipo} encontrada en: {ruta}")
                gdf = gpd.read_file(ruta)
                if gdf.crs is None:
                    gdf.set_crs(epsg=4326, inplace=True)
                vias[tipo] = gdf.to_crs(epsg=3857)
                print(f"✅ Vías {tipo}: {len(vias[tipo])} registros")
            except Exception as e:
                print(f"❌ Error cargando vías {tipo}: {e}")
        else:
            print(f"❌ Archivo de vías {tipo} NO encontrado en: {ruta}")

    return vias

# ════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ════════════════════════════════════════════════════════════════════════
def add_north_arrow_blanco_completo(ax, xy_pos=(0.93, 0.08), size=0.06):
    x_pos, y_pos = xy_pos
    s = size / 2
    trans = ax.transAxes
    inv_trans = ax.transData.inverted()
    body_width = s * 0.15
    points_body = np.array([
        (x_pos - body_width / 2, y_pos + s * 0.5),
        (x_pos + body_width / 2, y_pos + s * 0.5),
        (x_pos + body_width / 2, y_pos - s * 0.5),
        (x_pos - body_width / 2, y_pos - s * 0.5)
    ])
    points_body_data = inv_trans.transform(trans.transform(points_body))
    points_head = np.array([
        (x_pos, y_pos + s * 1.5),
        (x_pos - s * 0.5, y_pos + s * 0.5),
        (x_pos + s * 0.5, y_pos + s * 0.5)
    ])
    points_head_data = inv_trans.transform(trans.transform(points_head))
    ax.add_patch(Polygon(points_body_data, facecolor='white', edgecolor='black', linewidth=1.5, zorder=11, transform=ax.transData))
    ax.add_patch(Polygon(points_head_data, facecolor='white', edgecolor='black', linewidth=1.5, zorder=11, transform=ax.transData))
    ax.text(x_pos, y_pos + s * 1.5 + 0.015, "N", transform=ax.transAxes, fontsize=16, fontweight='bold',
            ha='center', va='center', color='white', path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

def calculate_numeric_scale(ax, fig):
    xlim = ax.get_xlim()
    ground_width_m = xlim[1] - xlim[0]
    fig_width_in = fig.get_size_inches()[0]
    ax_pos = ax.get_position()
    ax_width_in = fig_width_in * ax_pos.width
    scale_denominator = ground_width_m / (ax_width_in * 0.0254)
    rounding = 5000 if scale_denominator > 100000 else 1000 if scale_denominator > 10000 else 500
    scale_rounded = int(round(scale_denominator / rounding) * rounding)
    return f"1:{scale_rounded:,}"

def add_membrete(ax, dpto, prov, dist, main_map_ax, fig_obj):
    escala_numerica = calculate_numeric_scale(main_map_ax, fig_obj)
    info = {
        "MAPA": f"MAPA DE CENTROS POBLADOS: DISTRITO DE {dist.upper()}",
        "DPTO": dpto.upper(),
        "PROVINCIA": prov.upper(),
        "DISTRITO": dist.upper(),
        "MAPA_N": "001-2025",
        "ESCALA": escala_numerica,
        "FECHA": datetime.date.today().strftime("%d / %m / %Y")
    }
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), 10, 4, fill=False, edgecolor='black', lw=1.2))
    ax.plot([0, 10], [3, 3], color='black', lw=1.2)
    ax.plot([0, 7.5], [1.5, 1.5], color='black', lw=1.2)
    ax.plot([2.5, 2.5], [1.5, 3], color='black', lw=1.2)
    ax.plot([5, 5], [0, 3], color='black', lw=1.2)
    ax.plot([7.5, 7.5], [0, 3], color='black', lw=1.2)
    padding = 0.15
    ax.text(0 + padding, 3.5, "MAPA:", fontweight='bold', va='center', fontsize=8)
    ax.text(1.8 + padding, 3.5, info["MAPA"], va='center', fontsize=8)
    ax.text(0 + padding, 2.6, "DPTO:", fontweight='bold', va='center', fontsize=8)
    ax.text(0 + padding, 2.0, info["DPTO"], va='center', fontsize=8)
    ax.text(2.5 + padding, 2.6, "PROVINCIA:", fontweight='bold', va='center', fontsize=8)
    ax.text(2.5 + padding, 2.0, info["PROVINCIA"], va='center', fontsize=8)
    ax.text(5 + padding, 2.6, "DISTRITO:", fontweight='bold', va='center', fontsize=8)
    ax.text(5 + padding, 2.0, info["DISTRITO"], va='center', fontsize=8)
    ax.text(7.5 + padding, 2.5, "MAPA N°", fontweight='bold', ha='left', va='center', fontsize=8)
    ax.text(7.5 + padding, 0.8, info["MAPA_N"], ha='left', va='center', fontsize=10)
    ax.text(0 + padding, 1.0, "ESCALA:", fontweight='bold', va='center', fontsize=8)
    ax.text(0 + padding, 0.5, info["ESCALA"], va='center', fontsize=8)
    ax.text(5 + padding, 1.0, "FECHA:", fontweight='bold', va='center', fontsize=8)
    ax.text(5 + padding, 0.5, info["FECHA"], va='center', fontsize=8)

def buscar_shapefile(nombre_busqueda):
    for root, _, files in os.walk(ruta_base):
        for file in files:
            if file.lower().endswith(".shp") and nombre_busqueda.lower() in file.lower():
                return os.path.join(root, file)
    return None

def cargar_shapefile(nombre, alias):
    path = buscar_shapefile(nombre)
    if not path:
        return None
    try:
        gdf = gpd.read_file(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf.set_crs(epsg=4326, inplace=True)
        return gdf.to_crs(epsg=3857)
    except Exception as e:
        print(f"❌ Error cargando {alias} desde {path}: {e}")
        return None

def grillado_utm_proyectado(ax, bbox, ndiv=8):
    x0, y0, x1, y1 = bbox
    for x in np.linspace(x0, x1, ndiv):
        ax.plot([x, x], [y0, y1], color="black", linestyle="-", linewidth=0.4, alpha=0.6, zorder=0)
    for y in np.linspace(y0, y1, ndiv):
        ax.plot([x0, x1], [y, y], color="black", linestyle="-", linewidth=0.4, alpha=0.6, zorder=0)

    def fmt_este(x, pos):
        return f"{int(x):06d}"[:3] + " " + f"{int(x):06d}"[3:] + " E"

    def fmt_norte(y, pos):
        return f"{int(y):07d}"[0] + " " + f"{int(y):07d}"[1:4] + " " + f"{int(y):07d}"[4:] + " N"

    ax.xaxis.set_major_formatter(FuncFormatter(fmt_este))
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_norte))
    ax.tick_params(axis='x', labelsize=7, width=0.5, length=3, direction="out", pad=2, top=False, bottom=True, labeltop=False, labelbottom=True)
    ax.tick_params(axis='y', labelsize=7, width=0.5, length=3, direction="out", pad=2, left=True, right=False, labelleft=True, labelright=False)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(7)
    for label in ax.get_yticklabels():
        label.set_rotation(90)
        label.set_verticalalignment('center')
        label.set_horizontalalignment('right')

def grillado_grados_mejorado(ax, bbox, ndiv=5, decimales=2):
    transformer = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
    x0, y0, x1, y1 = bbox
    lon_start, lat_start = transformer.transform(x0, y0)
    lon_end, lat_end = transformer.transform(x1, y1)
    for lon in np.linspace(lon_start, lon_end, ndiv):
        xs, ys = transformer.transform(np.full(2, lon), [lat_start, lat_end])
        ax.plot(xs, ys, color="gray", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)
    for lat in np.linspace(lat_start, lat_end, ndiv):
        xs, ys = transformer.transform([lon_start, lon_end], np.full(2, lat))
        ax.plot(xs, ys, color="gray", linestyle="--", linewidth=0.3, alpha=0.5, zorder=0)

    def fmt_lon(x, pos):
        lon, _ = transformer.transform(x, y0)
        return f"{abs(lon):.{decimales}f}°{'W' if lon < 0 else 'E'}"

    def fmt_lat(y, pos):
        _, lat = transformer.transform(x0, y)
        return f"{abs(lat):.{decimales}f}°{'S' if lat < 0 else 'N'}"

    ax.xaxis.set_major_formatter(FuncFormatter(fmt_lon))
    ax.yaxis.set_major_formatter(FuncFormatter(fmt_lat))
    ax.tick_params(labelsize=6, width=0.4, length=2, direction="out", pad=2, top=True, bottom=True, left=True, right=True, labeltop=True, labelright=False)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(6)
    for label in ax.get_yticklabels():
        label.set_rotation(90)
        label.set_verticalalignment('center')
        label.set_horizontalalignment('right')

def mapa_ubicacion(ax, gdf_base_map, gdf_context, gdf_focus, titulo, etiqueta, tipo_mapa, gdf_dpto_sel=None, gdf_prov_sel=None, col_prov=None, col_dpto=None, departamento_sel=None, provincia_sel=None, gdf_departamentos=None, gdf_provincias=None, gdf_oceano=None):
    is_focus_valid = not gdf_focus.empty and all(np.isfinite(gdf_focus.total_bounds))
    
    if tipo_mapa == "pais":
        bbox_geom = gdf_departamentos.total_bounds
        dx, dy = (bbox_geom[2] - bbox_geom[0]) * 0.25, (bbox_geom[3] - bbox_geom[1]) * 0.25
    elif tipo_mapa == "provincia":
        bbox_geom = gdf_dpto_sel.total_bounds
        dx, dy = (bbox_geom[2] - bbox_geom[0]) * 0.12, (bbox_geom[3] - bbox_geom[1]) * 0.12
    elif tipo_mapa == "distrito":
        provincia_seleccionada_geom = gdf_prov_sel.geometry.unary_union
        geoms_vecinas = [prov.geometry for _, prov in gdf_provincias.iterrows()
                        if prov[col_prov] != provincia_sel and prov.geometry.touches(provincia_seleccionada_geom)]
        area_de_interes = gpd.GeoSeries([provincia_seleccionada_geom] + geoms_vecinas).unary_union
        bbox_geom = area_de_interes.bounds
        dx, dy = (bbox_geom[2] - bbox_geom[0]) * 0.15, (bbox_geom[3] - bbox_geom[1]) * 0.15
    else:
        bbox_geom = gdf_departamentos.total_bounds
        dx, dy = (bbox_geom[2] - bbox_geom[0]) * 0.25, (bbox_geom[3] - bbox_geom[1]) * 0.25
    
    x0, y0, x1, y1 = bbox_geom[0] - dx, bbox_geom[1] - dy, bbox_geom[2] + dx, bbox_geom[3] + dy
    S = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bbox = (cx - S / 2, cy - S / 2, cx + S / 2, cy + S / 2)
    
    if gdf_oceano is not None:
        gdf_oceano.clip(box(*bbox)).plot(ax=ax, color="#A4D4FF", edgecolor="none", zorder=2)
    
    if tipo_mapa == "pais":
        if gdf_base_map is not None:
            gdf_base_map.plot(ax=ax, color="#f0eee8", edgecolor="black", linewidth=0.4, zorder=1)
        if gdf_context is not None:
            gdf_context.plot(ax=ax, color=AMARILLO_CLARO, edgecolor="black", linewidth=0.7, zorder=3)
    elif tipo_mapa == "provincia":
        if gdf_base_map is not None:
            gdf_base_map.plot(ax=ax, color="#f0eee8", edgecolor="black", linewidth=0.4, zorder=1)
        if gdf_context is not None:
            gdf_context.plot(ax=ax, color=AMARILLO_CLARO, edgecolor="black", linewidth=0.7, zorder=3)
    elif tipo_mapa == "distrito":
        if gdf_provincias is not None:
            gdf_provincias[gdf_provincias[col_prov] != provincia_sel].plot(ax=ax, color='lightgray', edgecolor='darkgray', linewidth=0.4, zorder=2)
            gdf_prov_sel.plot(ax=ax, color=AMARILLO_CLARO, edgecolor='black', linewidth=0.7, zorder=3)
        if gdf_context is not None:
            gdf_context.plot(ax=ax, facecolor='none', edgecolor="gray", linewidth=0.4, zorder=4)
    
    if is_focus_valid:
        gdf_focus.plot(ax=ax, facecolor="red", edgecolor="red", linewidth=0.2, hatch='o', zorder=5)
    
    if all(np.isfinite(bbox)):
        grillado_grados_mejorado(ax, bbox, ndiv=5, decimales=1)
    
    ax.text(0.03, 0.05, titulo, transform=ax.transAxes, color="white", fontsize=8, ha="left", va="bottom", zorder=8, bbox=dict(facecolor="#4A90E2", edgecolor="black", boxstyle="round,pad=0.3", alpha=0.9))
    
    if is_focus_valid:
        ax.text(gdf_focus.geometry.centroid.iloc[0].x, gdf_focus.geometry.centroid.iloc[0].y, etiqueta.upper(), color="white", fontsize=8, ha="center", va="center", zorder=9, path_effects=[path_effects.withStroke(linewidth=3, foreground="black")])
    
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    ax.set_facecolor("#f0f8ff")
    ax.set_aspect('equal', adjustable='box')
    ax.axis('on')

# ════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE GENERACIÓN DE MAPA DE CENTROS POBLADOS
# ════════════════════════════════════════════════════════════════════════
def generar_mapa_poblacion(nombre_usuario, departamento_sel, provincia_sel, distrito_sel):
    print("\n" + "="*80)
    print("🗺️ INICIANDO PROCESO DE GENERACIÓN DE MAPA DE CENTROS POBLADOS...")
    print(f"   - Usuario: {nombre_usuario}")
    print(f"   - Ubicación: {distrito_sel}, {provincia_sel}, {departamento_sel}")

    # --- LÓGICA DE CARPETA DE USUARIO ---
    try:
        carpeta_usuario = os.path.join(ruta_base, "USUARIOS", nombre_usuario)
        carpeta_salida = os.path.join(carpeta_usuario, "MAPA DE CENTROS POBLADOS")
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"   - Carpeta de salida verificada: {carpeta_salida}")
    except Exception as e:
        print(f"❌ Error creando la estructura de carpetas para el usuario: {e}")
        return None

    # --- CARGAR CAPAS BASE ---
    print("\n📦 Cargando capas base...")
    gdf_departamentos = cargar_shapefile("departamento", "Departamentos")
    gdf_provincias = cargar_shapefile("provincia", "Provincias")
    gdf_distritos = cargar_shapefile("distrito", "Distritos del Perú")

    try:
        gdf_paises = gpd.read_file(f"{ruta_base}/DATA/MAPA DE UBICACION/PAISES DE SUDAMERICA/Sudamérica.shp").to_crs(3857)
        gdf_oceano = gpd.read_file(f"{ruta_base}/DATA/MAPA DE UBICACION/OCEANO/Océano.shp").to_crs(3857)
    except Exception as e:
        print(f"❌ Error cargando shapefiles de Países u Océano: {e}")
        gdf_paises = None
        gdf_oceano = None

    if gdf_departamentos is None or gdf_provincias is None or gdf_distritos is None:
        print("❌ Faltan capas base (departamento, provincia o distrito). Abortando.")
        return None

    # --- IDENTIFICAR COLUMNAS ---
    col_dpto = next((c for c in ['NOMBDEP', 'DEPARTAMEN'] if c in gdf_departamentos.columns), None)
    col_prov = next((c for c in ['NOMBPROV', 'PROVINCIA'] if c in gdf_provincias.columns), None)
    col_distr = next((c for c in ['NOMBDIST', 'DISTRITO'] if c in gdf_distritos.columns), None)

    # --- FILTRAR DATOS DEL ÁREA SELECCIONADA ---
    print("\n🔍 Filtrando datos del área seleccionada...")
    gdf_dpto_sel = gdf_departamentos[gdf_departamentos[col_dpto] == departamento_sel]
    gdf_prov_sel = gdf_provincias[gdf_provincias[col_prov] == provincia_sel]
    gdf_distrito = gdf_distritos[(gdf_distritos[col_distr] == distrito_sel) & (gdf_distritos[col_prov] == provincia_sel)]
    gdf_distritos_en_provincia = gdf_distritos[gdf_distritos[col_prov] == provincia_sel]

    if gdf_distrito.empty:
        print(f"❌ Error: No se pudo encontrar la geometría para el distrito '{distrito_sel}'.")
        return None

    # --- CARGAR CAPAS ADICIONALES ---
    print("\n📦 Cargando centros poblados, ríos y vías...")
    gdf_centros_poblados = cargar_centros_poblados()
    gdf_rios = cargar_rios()
    vias = cargar_vias()

    # Identificar columna de nombre de centro poblado
    col_cp_name = None
    if gdf_centros_poblados is not None:
        col_cp_name = next((c for c in ['NOMB_CCPP', 'NOMBCP', 'NOMB_CP', 'NOMBRE_CP', 'CENTRO_POB', 'NOMBRE']
                           if c in gdf_centros_poblados.columns), None)
        if col_cp_name:
            print(f"   ✅ Columna de nombre CP identificada: {col_cp_name}")

    # --- RECORTAR CAPAS AL DISTRITO Y BUFFER ---
    print("\n✂️ Recortando y procesando capas...")
    gdf_centros_clip = None
    gdf_rios_clip = None
    vias_clip = {'nacional': None, 'departamental': None, 'vecinal': None}

    if gdf_centros_poblados is not None and not gdf_distrito.empty:
        try:
            gdf_centros_clip = gpd.clip(gdf_centros_poblados, gdf_distrito)
            if not gdf_centros_clip.empty:
                print(f"✅ Centros poblados recortados: {len(gdf_centros_clip)} registros")
            else:
                print("⚠️ No hay centros poblados en el área")
        except Exception as e:
            print(f"❌ Error al recortar centros poblados: {e}")

    # Calcular bbox del distrito con buffer
    minx, miny, maxx, maxy = gdf_distrito.total_bounds
    buffer_factor = 0.15
    buffer_x = (maxx - minx) * buffer_factor
    buffer_y = (maxy - miny) * buffer_factor
    bbox_temp = (minx - buffer_x, miny - buffer_y, maxx + buffer_x, maxy + buffer_y)
    bbox_clip = box(*bbox_temp)

    # --- RECORTAR RÍOS POR BBOX (IGUAL QUE VÍAS) ---
    if gdf_rios is not None:
        try:
            gdf_rios_clip = gpd.clip(gdf_rios, bbox_clip)
            if gdf_rios_clip is not None and not gdf_rios_clip.empty:
                print(f"✅ Ríos recortados: {len(gdf_rios_clip)} registros")
            else:
                print("⚠️ No hay ríos en el área")
                gdf_rios_clip = None
        except Exception as e:
            print(f"❌ Error al recortar ríos: {e}")
            gdf_rios_clip = None
    else:
        gdf_rios_clip = None

    # --- RECORTAR VÍAS POR BBOX (IGUAL PARA TODAS) ---
    for tipo in ['nacional', 'departamental', 'vecinal']:
        if vias[tipo] is not None:
            try:
                vias_clip[tipo] = gpd.clip(vias[tipo], bbox_clip)
                if vias_clip[tipo] is not None and not vias_clip[tipo].empty:
                    print(f"✅ Vías {tipo} recortadas: {len(vias_clip[tipo])} registros")
                else:
                    print(f"⚠️ No hay vías {tipo} en el área")
                    vias_clip[tipo] = None
            except Exception as e:
                print(f"❌ Error al recortar vías {tipo}: {e}")
                vias_clip[tipo] = None
        else:
            vias_clip[tipo] = None

    # --- CREAR FIGURA ---
    print("\n🎨 Generando layout del mapa...")
    fig = plt.figure(figsize=(14, 9.9))
    grid = plt.GridSpec(1, 2, width_ratios=[3.0, 1], wspace=0.05)
    gs_izquierda = grid[0, 0].subgridspec(3, 1, height_ratios=[0.08, 3.5, 0.42], hspace=0.08)

    # --- TÍTULO PRINCIPAL ---
    ax_titulo = fig.add_subplot(gs_izquierda[0])
    ax_titulo.text(0.5, 0.5, f"MAPA DE CENTROS POBLADOS - DISTRITO DE {distrito_sel.upper()}",
                   ha='center', va='center', fontsize=12, fontweight="normal",
                   bbox=dict(boxstyle='square,pad=0.5', facecolor='white', edgecolor='black', linewidth=1.5, alpha=0.95))
    ax_titulo.axis('off')

    # --- MAPA PRINCIPAL ---
    ax_main = fig.add_subplot(gs_izquierda[1])

    # Ajustar bbox a proporción fija
    aspect_ratio_objetivo = 1.21
    cx = (bbox_temp[0] + bbox_temp[2]) / 2
    cy = (bbox_temp[1] + bbox_temp[3]) / 2
    ancho_actual = bbox_temp[2] - bbox_temp[0]
    alto_actual = bbox_temp[3] - bbox_temp[1]
    aspecto_actual = ancho_actual / alto_actual

    if aspecto_actual > aspect_ratio_objetivo:
        nuevo_alto = ancho_actual / aspect_ratio_objetivo
        bbox_main = (bbox_temp[0], cy - nuevo_alto/2, bbox_temp[2], cy + nuevo_alto/2)
    else:
        nuevo_ancho = alto_actual * aspect_ratio_objetivo
        bbox_main = (cx - nuevo_ancho/2, bbox_temp[1], cx + nuevo_ancho/2, bbox_temp[3])

    ax_main.set_xlim(bbox_main[0], bbox_main[2])
    ax_main.set_ylim(bbox_main[1], bbox_main[3])
    ax_main.set_aspect('equal', adjustable='box')

    # Agregar basemap
    print("   📡 Descargando imagen satelital...")
    try:
        ctx.add_basemap(ax_main, source=ctx.providers.Esri.WorldImagery, attribution=False, zoom='auto')
    except Exception as e:
        print(f"   ⚠️ No se pudo cargar el mapa base: {e}")
        ax_main.set_facecolor("#e8e8e8")

    # ════════════════════════════════════════════════════════════════════════
    # DIBUJAR CAPAS EN ORDEN CORRECTO
    # ════════════════════════════════════════════════════════════════════════
    
    # --- DIBUJAR VÍAS NACIONALES ---
    if vias_clip['nacional'] is not None and not vias_clip['nacional'].empty:
        print(f"   Dibujando vías nacionales ({len(vias_clip['nacional'])} segmentos)...")
        vias_clip['nacional'].plot(ax=ax_main, color='#FF0000', linewidth=2.5, zorder=8, alpha=0.9)
    
    # --- DIBUJAR VÍAS DEPARTAMENTALES ---
    if vias_clip['departamental'] is not None and not vias_clip['departamental'].empty:
        print(f"   Dibujando vías departamentales ({len(vias_clip['departamental'])} segmentos)...")
        vias_clip['departamental'].plot(ax=ax_main, color='#FF69B4', linewidth=2.0, zorder=9, alpha=0.85)
    
    # --- DIBUJAR VÍAS VECINALES (ROSADO PASTEL) ---
    if vias_clip['vecinal'] is not None and not vias_clip['vecinal'].empty:
        print(f"   Dibujando vías vecinales ({len(vias_clip['vecinal'])} segmentos)...")
        vias_clip['vecinal'].plot(ax=ax_main, color='#FFB6D9', linewidth=1.5, zorder=10, alpha=0.85)
    
    # --- DIBUJAR RÍOS (CELESTE) ---
    if gdf_rios_clip is not None and not gdf_rios_clip.empty:
        print(f"   Dibujando ríos ({len(gdf_rios_clip)} segmentos)...")
        gdf_rios_clip.plot(ax=ax_main, color='#87CEEB', linewidth=2.5, zorder=11, alpha=0.8)
    
    # --- DIBUJAR LÍMITE DEL DISTRITO CON RELLENO VERDE INTENSO ---
    if not gdf_distrito.empty:
        print("   🟩 Dibujando límite distrital con relleno verde intenso...")
        gdf_distrito.plot(ax=ax_main, facecolor='#00AA00', edgecolor='#000000', linewidth=3.0,
                         linestyle='-', alpha=0.25, zorder=12)

    # --- DIBUJAR CENTROS POBLADOS ---
    if gdf_centros_clip is not None and not gdf_centros_clip.empty and col_cp_name:
        print(f"   😀 Dibujando centros poblados ({len(gdf_centros_clip)} puntos)...")
        gdf_centros_clip.plot(ax=ax_main, color='#1B5E20', markersize=50, marker='h',
                             edgecolor='#0D3D0D', linewidth=1.2, zorder=15, alpha=0.75)

        # Agregar etiquetas con color verde y delineado negro
        for _, row in gdf_centros_clip.iterrows():
            try:
                nombre_cp = row[col_cp_name]
                x_coord = row.geometry.x
                y_coord = row.geometry.y

                ax_main.text(x_coord, y_coord, nombre_cp,
                           fontsize=6.5, fontweight='bold', color='#228B22',
                           ha='left', va='bottom', zorder=16,
                           path_effects=[path_effects.withStroke(linewidth=2.5, foreground='black')])
            except Exception:
                pass

    # --- GRILLADO, NORTE Y ESCALA ---
    grillado_utm_proyectado(ax_main, bbox_main, ndiv=8)
    add_north_arrow_blanco_completo(ax_main, xy_pos=(0.93, 0.08), size=0.06)
    ax_main.add_artist(ScaleBar(1, units="m", location="lower left", box_alpha=0.6, border_pad=0.5, scale_loc='bottom'))

    # --- MEMBRETE Y LEYENDA ---
    gs_memb_ley = gs_izquierda[2].subgridspec(1, 2, wspace=0.1)
    ax_membrete = fig.add_subplot(gs_memb_ley[0])
    fig.canvas.draw()
    add_membrete(ax_membrete, departamento_sel, provincia_sel, distrito_sel, ax_main, fig)

    # --- LEYENDA ---
    ax_leyenda = fig.add_subplot(gs_memb_ley[1])
    ax_leyenda.axis('off')

    legend_elements = []

    if gdf_centros_clip is not None and not gdf_centros_clip.empty:
        legend_elements.append(Line2D([0], [0], marker='h', color='w', markerfacecolor='#1B5E20',
                                      markeredgecolor='#0D3D0D', markersize=8, label='Centros Poblados'))

    if gdf_rios_clip is not None and not gdf_rios_clip.empty:
        legend_elements.append(Line2D([0], [0], color='#87CEEB', lw=2.5, label='Ríos'))

    if vias_clip['nacional'] is not None and not vias_clip['nacional'].empty:
        legend_elements.append(Line2D([0], [0], color='#FF0000', lw=2.5, label='Vía Nacional'))

    if vias_clip['departamental'] is not None and not vias_clip['departamental'].empty:
        legend_elements.append(Line2D([0], [0], color='#FF69B4', lw=2.5, label='Vía Departamental'))

    if vias_clip['vecinal'] is not None and not vias_clip['vecinal'].empty:
        legend_elements.append(Line2D([0], [0], color='#FFB6D9', lw=2.5, label='Vía Vecinal'))

    legend_elements.extend([
        Line2D([0], [0], color='#00AA00', lw=2.5, alpha=0.25, label='Zona Estudio'),
        Line2D([0], [0], color='black', lw=2, label='Límite Distrital'),
        Line2D([0], [0], color='black', ls='-', lw=1, label='Grillado UTM')
    ])

    num_elementos = len(legend_elements)
    ncols = 2 if num_elementos <= 6 else 3

    leg = ax_leyenda.legend(
        handles=legend_elements,
        loc='center',
        ncol=ncols,
        frameon=True,
        fontsize=7.5,
        title="LEYENDA",
        title_fontproperties={'size': 10, 'weight': 'bold'},
        handletextpad=0.5,
        columnspacing=1.0,
        borderpad=0.7,
        handlelength=1.5
    )

    leg.get_title().set_ha('center')
    leg.get_frame().set_edgecolor('black')
    leg.get_frame().set_linewidth(1.2)

    # --- MAPAS DE UBICACIÓN A LA DERECHA ---
    print("   🗺️ Generando mapas de ubicación...")

    gs_ubicaciones = grid[0, 1].subgridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.15)
    ax_depto = fig.add_subplot(gs_ubicaciones[0])
    ax_prov = fig.add_subplot(gs_ubicaciones[1])
    ax_dist = fig.add_subplot(gs_ubicaciones[2])

    mapa_ubicacion(ax_depto, gdf_paises, gdf_departamentos, gdf_dpto_sel,
                   f"DEPARTAMENTO DE\n{departamento_sel.upper()}", departamento_sel,
                   tipo_mapa="pais", gdf_departamentos=gdf_departamentos, gdf_oceano=gdf_oceano)
    mapa_ubicacion(ax_prov, gdf_departamentos, gdf_dpto_sel, gdf_prov_sel,
                   f"PROVINCIA DE\n{provincia_sel.upper()}", provincia_sel,
                   tipo_mapa="provincia", gdf_dpto_sel=gdf_dpto_sel, departamento_sel=departamento_sel,
                   col_dpto=col_dpto, gdf_departamentos=gdf_departamentos, gdf_oceano=gdf_oceano)
    mapa_ubicacion(ax_dist, gdf_prov_sel, gdf_distritos_en_provincia, gdf_distrito,
                   f"DISTRITO DE\n{distrito_sel.upper()}", distrito_sel,
                   tipo_mapa="distrito", gdf_prov_sel=gdf_prov_sel, provincia_sel=provincia_sel,
                   col_prov=col_prov, gdf_provincias=gdf_provincias, gdf_oceano=gdf_oceano)

    # --- AJUSTES FINALES ---
    plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.05)

    rect_frame = fig.add_axes([0, 0, 1, 1], frameon=False)
    rect_frame.set_xticks([])
    rect_frame.set_yticks([])
    rect_frame.patch.set_visible(False)

    for spine in rect_frame.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)
        spine.set_color('black')

    # --- GUARDAR MAPA FINAL ---
    print("\n💾 Guardando mapa final en carpeta de usuario...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"MAPA_CENTROS_POBLADOS_{distrito_sel.replace(' ', '_')}_{timestamp}.png"
    ruta_guardado_final = os.path.join(carpeta_salida, nombre_base)

    plt.savefig(ruta_guardado_final, dpi=300, bbox_inches='tight', pad_inches=0.01)
    plt.close(fig)

    print(f"✅ Mapa de centros poblados guardado exitosamente en: {ruta_guardado_final}")
    if gdf_centros_clip is not None:
        print(f"   📊 Centros poblados identificados: {len(gdf_centros_clip)}")

    return ruta_guardado_final