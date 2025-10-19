# Archivo: pendientes_final.py

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
import xarray as xr
from scipy.ndimage import sobel
from matplotlib.colors import BoundaryNorm
from matplotlib import colors
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.transform import from_bounds

# --- RUTA BASE ORIGINAL ---
ruta_base = "/workspaces/SIG-AUTOMATIZACION/PRUEBA"

AMARILLO_CLARO = "#FFEE58"

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 PALETA DE COLORES PARA PENDIENTES
# ═══════════════════════════════════════════════════════════════════════════════
COLORES_PENDIENTE = ['#7FBF3F', '#BFDF3F', '#FFFF00', '#FF9F00', '#FF0000']
ETIQUETAS_PENDIENTE = ['< 5°', '5° - 15°', '15° - 25°', '25° - 45°', '> 45°']

# ═══════════════════════════════════════════════════════════════════════════════
# 📐 FUNCIÓN PARA CALCULAR PENDIENTES
# ═══════════════════════════════════════════════════════════════════════════════
def calcular_pendientes_desde_dem(ruta_dem, gdf_distrito):
    """Calcula pendientes desde un archivo DEM NetCDF y las recorta al distrito"""
    print("   Abriendo archivo DEM...")
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(ruta_dem):
            print(f"   ❌ El archivo no existe: {ruta_dem}")
            return None
        
        print(f"   📂 Archivo encontrado: {ruta_dem}")
        print(f"   📊 Tamaño del archivo: {os.path.getsize(ruta_dem) / (1024*1024):.2f} MB")
        
        dem = xr.open_dataset(ruta_dem)
        print(f"   ✅ Dataset abierto correctamente")
        print(f"   Variables disponibles: {list(dem.data_vars)}")
        
        elevation_data = dem['DEM']
        elevation = elevation_data.values
        
        print(f"   Shape de elevación: {elevation.shape}")
        
        lats = dem.latitude.values
        lons = dem.longitude.values
        
        print(f"   Rango de latitudes: {lats.min():.4f} a {lats.max():.4f}")
        print(f"   Rango de longitudes: {lons.min():.4f} a {lons.max():.4f}")
        
        # Verificar que el distrito está dentro del rango del DEM
        distrito_bounds = gdf_distrito.total_bounds
        print(f"   Bounds del distrito (EPSG:3857): {distrito_bounds}")
        
        # Convertir bounds del distrito a lat/lon para comparar
        transformer_inv = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
        dist_lon_min, dist_lat_min = transformer_inv.transform(distrito_bounds[0], distrito_bounds[1])
        dist_lon_max, dist_lat_max = transformer_inv.transform(distrito_bounds[2], distrito_bounds[3])
        
        print(f"   Bounds del distrito (lat/lon): lon[{dist_lon_min:.4f}, {dist_lon_max:.4f}], lat[{dist_lat_min:.4f}, {dist_lat_max:.4f}]")
        
        # Verificar superposición
        if dist_lon_max < lons.min() or dist_lon_min > lons.max() or dist_lat_max < lats.min() or dist_lat_min > lats.max():
            print("   ⚠️ ADVERTENCIA: El distrito podría estar fuera del rango del DEM")
        
        # Calcular resolución espacial
        lat_res = abs(lats[1] - lats[0])
        lon_res = abs(lons[1] - lons[0])
        
        dy = lat_res * 111000  # metros
        dx = lon_res * 111000 * np.cos(np.radians(np.mean(lats)))
        
        print(f"   Resolución espacial: dx={dx:.2f}m, dy={dy:.2f}m")
        
        # Calcular gradientes
        grad_x = sobel(elevation, axis=1) / (8 * dx)
        grad_y = sobel(elevation, axis=0) / (8 * dy)
        
        # Calcular pendiente en grados
        slope = np.arctan(np.sqrt(grad_x**2 + grad_y**2)) * (180 / np.pi)
        
        # Clasificar pendientes
        slope_classes = np.zeros_like(slope)
        slope_classes[slope < 5] = 1
        slope_classes[(slope >= 5) & (slope < 15)] = 2
        slope_classes[(slope >= 15) & (slope < 25)] = 3
        slope_classes[(slope >= 25) & (slope < 45)] = 4
        slope_classes[slope >= 45] = 5
        
        print(f"   ✅ Pendientes calculadas: {slope.shape}")
        
        # Crear GeoDataFrame con el raster de pendientes
        # Transformar coordenadas a metros (EPSG:3857)
        transformer = pyproj.Transformer.from_crs(4326, 3857, always_xy=True)
        
        print(f"   Creando GeoDataFrame de pendientes...")
        # Crear cuadrícula de polígonos para cada celda del raster
        geometrias = []
        valores_clase = []
        
        total_celdas = len(lats) * len(lons)
        celdas_procesadas = 0
        
        for i in range(len(lats)):
            for j in range(len(lons)):
                if not np.isnan(slope_classes[i, j]):
                    # Definir los límites de la celda
                    lon_min = lons[j] - lon_res/2
                    lon_max = lons[j] + lon_res/2
                    lat_min = lats[i] - lat_res/2
                    lat_max = lats[i] + lat_res/2
                    
                    # Transformar a metros
                    x_min, y_min = transformer.transform(lon_min, lat_min)
                    x_max, y_max = transformer.transform(lon_max, lat_max)
                    
                    # Crear polígono
                    geometrias.append(box(x_min, y_min, x_max, y_max))
                    valores_clase.append(slope_classes[i, j])
            
            celdas_procesadas += len(lons)
            if i % max(1, len(lats) // 10) == 0:  # Mostrar progreso cada 10%
                print(f"   Progreso: {(celdas_procesadas/total_celdas)*100:.1f}%")
        
        print(f"   Total de celdas con datos: {len(geometrias)}")
        
        if len(geometrias) == 0:
            print("   ❌ No se generaron geometrías válidas")
            return None
        
        gdf_pendientes = gpd.GeoDataFrame({
            'clase_pendiente': valores_clase
        }, geometry=geometrias, crs='EPSG:3857')
        
        print(f"   Recortando pendientes al área del distrito...")
        gdf_pendientes_clipped = gpd.clip(gdf_pendientes, gdf_distrito)
        
        if gdf_pendientes_clipped.empty:
            print("   ⚠️ No hay datos de pendiente en el área del distrito")
            return None
        
        print(f"   ✅ Pendientes recortadas: {len(gdf_pendientes_clipped)} celdas")
        
        # Calcular estadísticas
        stats = {
            'min': np.nanmin(slope),
            'max': np.nanmax(slope),
            'mean': np.nanmean(slope),
            'median': np.nanmedian(slope)
        }
        
        # Contar píxeles por clase
        total_celdas = len(gdf_pendientes_clipped)
        clases_count = {
            1: len(gdf_pendientes_clipped[gdf_pendientes_clipped['clase_pendiente'] == 1]),
            2: len(gdf_pendientes_clipped[gdf_pendientes_clipped['clase_pendiente'] == 2]),
            3: len(gdf_pendientes_clipped[gdf_pendientes_clipped['clase_pendiente'] == 3]),
            4: len(gdf_pendientes_clipped[gdf_pendientes_clipped['clase_pendiente'] == 4]),
            5: len(gdf_pendientes_clipped[gdf_pendientes_clipped['clase_pendiente'] == 5])
        }
        
        stats['clases'] = clases_count
        stats['total'] = total_celdas
        
        return gdf_pendientes_clipped, stats
        
    except Exception as e:
        print(f"   ❌ Error calculando pendientes: {e}")
        import traceback
        traceback.print_exc()
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES (COPIADAS DE geomorfologia_final.py)
# ═══════════════════════════════════════════════════════════════════════════════
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
            ha='center', va='center', color='white', 
            path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

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
        "MAPA": f"MAPA DE PENDIENTES: DISTRITO DE {dist.upper()}",
        "DPTO": dpto.upper(),
        "PROVINCIA": prov.upper(),
        "DISTRITO": dist.upper(),
        "MAPA_N": "002-2025",
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
        print(f"   No se encontró shapefile: {alias}")
        return None
    
    try:
        gdf = gpd.read_file(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf.set_crs(epsg=4326, inplace=True)
        return gdf.to_crs(epsg=3857)
    except Exception as e:
        print(f"   Error cargando {alias} desde {path}: {e}")
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
    ax.tick_params(axis='x', labelsize=7, width=0.5, length=3, direction="out", pad=2, 
                   top=False, bottom=True, labeltop=False, labelbottom=True)
    ax.tick_params(axis='y', labelsize=7, width=0.5, length=3, direction="out", pad=2, 
                   left=True, right=False, labelleft=True, labelright=False)
    
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
    ax.tick_params(labelsize=6, width=0.4, length=2, direction="out", pad=2, 
                   top=True, bottom=True, left=True, right=True, labeltop=True, labelright=False)
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontsize(6)
    
    for label in ax.get_yticklabels():
        label.set_rotation(90)
        label.set_verticalalignment('center')
        label.set_horizontalalignment('right')

def mapa_ubicacion(ax, gdf_base_map, gdf_context, gdf_focus, titulo, etiqueta, tipo_mapa, 
                   gdf_dpto_sel=None, gdf_prov_sel=None, col_prov=None, col_dpto=None, 
                   departamento_sel=None, provincia_sel=None, gdf_departamentos=None, 
                   gdf_provincias=None, gdf_oceano=None):
    
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
            gdf_provincias[gdf_provincias[col_prov] != provincia_sel].plot(
                ax=ax, color='lightgray', edgecolor='darkgray', linewidth=0.4, zorder=2)
            gdf_prov_sel.plot(ax=ax, color=AMARILLO_CLARO, edgecolor='black', linewidth=0.7, zorder=3)
        if gdf_context is not None:
            gdf_context.plot(ax=ax, facecolor='none', edgecolor="gray", linewidth=0.4, zorder=4)
    
    if is_focus_valid:
        gdf_focus.plot(ax=ax, facecolor="red", edgecolor="red", linewidth=0.2, hatch='o', zorder=5)
    
    if all(np.isfinite(bbox)):
        grillado_grados_mejorado(ax, bbox, ndiv=5, decimales=1)
    
    ax.text(0.03, 0.05, titulo, transform=ax.transAxes, color="white", fontsize=8, 
            ha="left", va="bottom", zorder=8, 
            bbox=dict(facecolor="#4A90E2", edgecolor="black", boxstyle="round,pad=0.3", alpha=0.9))
    
    if is_focus_valid:
        ax.text(gdf_focus.geometry.centroid.iloc[0].x, gdf_focus.geometry.centroid.iloc[0].y, 
                etiqueta.upper(), color="white", fontsize=8, ha="center", va="center", zorder=9, 
                path_effects=[path_effects.withStroke(linewidth=3, foreground="black")])
    
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    ax.set_facecolor("#f0f8ff")
    ax.set_aspect('equal', adjustable='box')
    ax.axis('on')

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA BUSCAR EL ARCHIVO DEM
# ═══════════════════════════════════════════════════════════════════════════════
def buscar_archivo_dem():
    """Busca el archivo DEM.nc en la estructura del proyecto"""
    rutas_posibles = [
        f"{ruta_base}/DATA/PENDIENTES/DEM.nc",
        "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/PENDIENTES/DEM.nc",
        "/content/DEM.nc",
        "./DEM.nc",
        f"{ruta_base}/DEM.nc"
    ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            print(f"   ✅ DEM encontrado en: {ruta}")
            return ruta
    
    print("   ❌ No se encontró el archivo DEM.nc en ninguna ubicación")
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE GENERACIÓN DE MAPA DE PENDIENTES
# ═══════════════════════════════════════════════════════════════════════════════
def generar_mapa_pendientes(nombre_usuario, departamento_sel, provincia_sel, distrito_sel, ruta_dem=None):
    print("\n" + "="*80)
    print("INICIANDO PROCESO DE GENERACIÓN DE MAPA DE PENDIENTES...")
    print(f"   - Usuario: {nombre_usuario}")
    print(f"   - Ubicación: {distrito_sel}, {provincia_sel}, {departamento_sel}")
    
    # Si no se proporciona ruta, buscar automáticamente
    if ruta_dem is None:
        print("\n🔍 Buscando archivo DEM...")
        ruta_dem = buscar_archivo_dem()
        if ruta_dem is None:
            print("❌ No se puede continuar sin el archivo DEM")
            return None
    
    print(f"   - DEM: {ruta_dem}")
    
    try:
        carpeta_usuario = os.path.join(ruta_base, "USUARIOS", nombre_usuario)
        carpeta_salida = os.path.join(carpeta_usuario, "MAPA DE PENDIENTES")
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"   - Carpeta de salida verificada: {carpeta_salida}")
    except Exception as e:
        print(f"Error creando la estructura de carpetas para el usuario: {e}")
        return None
    
    print("\n📂 Cargando capas base...")
    gdf_departamentos = cargar_shapefile("departamento", "Departamentos")
    gdf_provincias = cargar_shapefile("provincia", "Provincias")
    gdf_distritos = cargar_shapefile("distrito", "Distritos del Perú")
    
    try:
        gdf_paises = gpd.read_file(f"{ruta_base}/DATA/MAPA DE UBICACION/PAISES DE SUDAMERICA/Sudamérica.shp").to_crs(3857)
        gdf_oceano = gpd.read_file(f"{ruta_base}/DATA/MAPA DE UBICACION/OCEANO/Océano.shp").to_crs(3857)
    except Exception as e:
        print(f"Error cargando shapefiles de Países u Océano: {e}")
        gdf_paises = None
        gdf_oceano = None
    
    if gdf_departamentos is None or gdf_provincias is None or gdf_distritos is None:
        print("Faltan capas base (departamento, provincia o distrito). Abortando.")
        return None
    
    col_dpto = next((c for c in ['NOMBDEP', 'DEPARTAMEN'] if c in gdf_departamentos.columns), None)
    col_prov = next((c for c in ['NOMBPROV', 'PROVINCIA'] if c in gdf_provincias.columns), None)
    col_distr = next((c for c in ['NOMBDIST', 'DISTRITO'] if c in gdf_distritos.columns), None)
    
    if not all([col_dpto, col_prov, col_distr]):
        print("No se pudieron identificar las columnas de nombres en los shapefiles")
        return None
    
    print("\n🗺️  Filtrando datos del área seleccionada...")
    gdf_dpto_sel = gdf_departamentos[gdf_departamentos[col_dpto] == departamento_sel]
    gdf_prov_sel = gdf_provincias[gdf_provincias[col_prov] == provincia_sel]
    gdf_distrito = gdf_distritos[(gdf_distritos[col_distr] == distrito_sel) & 
                                  (gdf_distritos[col_prov] == provincia_sel)]
    gdf_distritos_en_provincia = gdf_distritos[gdf_distritos[col_prov] == provincia_sel]
    
    if gdf_distrito.empty:
        print(f"Error: No se pudo encontrar la geometría para el distrito '{distrito_sel}'.")
        return None
    
    print(f"   ✅ Distrito encontrado con geometría válida")
    
    print("\n📐 Calculando pendientes desde DEM...")
    resultado = calcular_pendientes_desde_dem(ruta_dem, gdf_distrito)
    
    if resultado is None:
        print("No se pudieron calcular las pendientes")
        return None
    
    gdf_pendientes, stats = resultado
    
    print("\n📊 Estadísticas de pendiente:")
    print(f"   Pendiente mínima:  {stats['min']:>8.2f}°")
    print(f"   Pendiente máxima:  {stats['max']:>8.2f}°")
    print(f"   Pendiente media:   {stats['mean']:>8.2f}°")
    print(f"   Pendiente mediana: {stats['median']:>8.2f}°")
    
    print("\n🗺️  Generando layout del mapa...")
    fig = plt.figure(figsize=(14, 9.9))
    grid = plt.GridSpec(1, 2, width_ratios=[3.0, 1], wspace=0.05)
    gs_izquierda = grid[0, 0].subgridspec(3, 1, height_ratios=[0.08, 3.5, 0.42], hspace=0.08)
    
    ax_titulo = fig.add_subplot(gs_izquierda[0])
    ax_titulo.text(0.5, 0.5, f"MAPA DE PENDIENTES - DISTRITO DE {distrito_sel.upper()}",
                   ha='center', va='center', fontsize=12, fontweight="normal",
                   bbox=dict(boxstyle='square,pad=0.5', facecolor='white', 
                            edgecolor='black', linewidth=1.5, alpha=0.95))
    ax_titulo.axis('off')
    
    ax_main = fig.add_subplot(gs_izquierda[1])
    
    # BBOX con aspect ratio consistente
    minx, miny, maxx, maxy = gdf_distrito.total_bounds
    buffer_factor = 0.15
    buffer_x = (maxx - minx) * buffer_factor
    buffer_y = (maxy - miny) * buffer_factor
    bbox_temp = (minx - buffer_x, miny - buffer_y, maxx + buffer_x, maxy + buffer_y)
    
    aspect_ratio_objetivo = 1.21
    cx = (bbox_temp[0] + bbox_temp[2]) / 2
    cy = (bbox_temp[1] + bbox_temp[3]) / 2
    ancho_actual = bbox_temp[2] - bbox_temp[0]
    alto_actual = bbox_temp[3] - bbox_temp[1]
    
    if (ancho_actual / alto_actual) > aspect_ratio_objetivo:
        nuevo_alto = ancho_actual / aspect_ratio_objetivo
        bbox_main = (bbox_temp[0], cy - nuevo_alto/2, bbox_temp[2], cy + nuevo_alto/2)
    else:
        nuevo_ancho = alto_actual * aspect_ratio_objetivo
        bbox_main = (cx - nuevo_ancho/2, bbox_temp[1], cx + nuevo_ancho/2, bbox_temp[3])
    
    ax_main.set_xlim(bbox_main[0], bbox_main[2])
    ax_main.set_ylim(bbox_main[1], bbox_main[3])
    ax_main.set_aspect('equal', adjustable='box')
    
    print("   Descargando imagen satelital...")
    try:
        ctx.add_basemap(ax_main, source=ctx.providers.Esri.WorldImagery, 
                       attribution=False, zoom='auto')
    except Exception as e:
        print(f"   No se pudo cargar el mapa base: {e}")
        ax_main.set_facecolor("#e8e8e8")
    
    print("   Dibujando clases de pendiente...")
    
    # Crear colormap para las clases
    cmap = colors.ListedColormap(COLORES_PENDIENTE)
    bounds = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    norm = BoundaryNorm(bounds, cmap.N)
    
    # Dibujar cada clase de pendiente
    for clase in range(1, 6):
        gdf_clase = gdf_pendientes[gdf_pendientes['clase_pendiente'] == clase]
        if not gdf_clase.empty:
            gdf_clase.plot(ax=ax_main, color=COLORES_PENDIENTE[clase-1], 
                          edgecolor='none', alpha=0.7, zorder=4)
    
    # Límite distrital
    gdf_distrito.plot(ax=ax_main, facecolor="none", edgecolor="red", linewidth=2,
                     linestyle='--', alpha=0.9, zorder=15)
    
    grillado_utm_proyectado(ax_main, bbox_main, ndiv=8)
    add_north_arrow_blanco_completo(ax_main, xy_pos=(0.93, 0.08), size=0.06)
    ax_main.add_artist(ScaleBar(1, units="m", location="lower left", 
                                box_alpha=0.6, border_pad=0.5, scale_loc='bottom'))
    
    # MEMBRETE Y LEYENDA
    gs_memb_ley = gs_izquierda[2].subgridspec(1, 2, wspace=0.1)
    ax_membrete = fig.add_subplot(gs_memb_ley[0])
    fig.canvas.draw()
    add_membrete(ax_membrete, departamento_sel, provincia_sel, distrito_sel, ax_main, fig)
    
    ax_leyenda = fig.add_subplot(gs_memb_ley[1])
    ax_leyenda.axis('off')
    
    legend_elements = [
        Patch(facecolor='white', edgecolor='white', label='PENDIENTES (°):', linewidth=0)
    ]
    
    # Agregar colores de pendiente
    for idx, etiqueta in enumerate(ETIQUETAS_PENDIENTE):
        legend_elements.append(
            Patch(facecolor=COLORES_PENDIENTE[idx], edgecolor='black', label=etiqueta)
        )
    
    legend_elements.extend([
        Patch(facecolor='white', edgecolor='white', label='', linewidth=0),
        Line2D([0], [0], color='red', lw=2, linestyle='--', label='Límite Distrital'),
        Line2D([0], [0], color='black', ls='-', lw=1, label='Grillado UTM')
    ])
    
    leg = ax_leyenda.legend(
        handles=legend_elements,
        loc='center',
        ncol=1,
        frameon=True,
        fontsize=8,
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
    
    print("   Generando mapas de ubicación...")
    
    gs_ubicaciones = grid[0, 1].subgridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.15)
    ax_depto = fig.add_subplot(gs_ubicaciones[0])
    ax_prov = fig.add_subplot(gs_ubicaciones[1])
    ax_dist = fig.add_subplot(gs_ubicaciones[2])
    
    mapa_ubicacion(ax_depto, gdf_paises, gdf_departamentos, gdf_dpto_sel,
                   f"DEPARTAMENTO DE\n{departamento_sel.upper()}", departamento_sel,
                   tipo_mapa="pais", gdf_departamentos=gdf_departamentos, gdf_oceano=gdf_oceano)
    
    mapa_ubicacion(ax_prov, gdf_departamentos, gdf_dpto_sel, gdf_prov_sel,
                   f"PROVINCIA DE\n{provincia_sel.upper()}", provincia_sel,
                   tipo_mapa="provincia", gdf_dpto_sel=gdf_dpto_sel, 
                   departamento_sel=departamento_sel, col_dpto=col_dpto, 
                   gdf_departamentos=gdf_departamentos, gdf_oceano=gdf_oceano)
    
    mapa_ubicacion(ax_dist, gdf_prov_sel, gdf_distritos_en_provincia, gdf_distrito,
                   f"DISTRITO DE\n{distrito_sel.upper()}", distrito_sel,
                   tipo_mapa="distrito", gdf_prov_sel=gdf_prov_sel, 
                   provincia_sel=provincia_sel, col_prov=col_prov, 
                   gdf_provincias=gdf_provincias, gdf_oceano=gdf_oceano)
    
    plt.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98, hspace=0.2, wspace=0.05)
    
    rect_frame = fig.add_axes([0, 0, 1, 1], frameon=False)
    rect_frame.set_xticks([])
    rect_frame.set_yticks([])
    rect_frame.patch.set_visible(False)
    
    for spine in rect_frame.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)
        spine.set_color('black')
    
    print("\n💾 Guardando mapa final en carpeta de usuario...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_base = f"MAPA_PENDIENTES_{distrito_sel.replace(' ', '_')}_{timestamp}.png"
    ruta_guardado_final = os.path.join(carpeta_salida, nombre_base)
    
    try:
        plt.savefig(ruta_guardado_final, dpi=300, bbox_inches='tight', pad_inches=0.01)
        plt.close(fig)
        
        if os.path.exists(ruta_guardado_final):
            file_size = os.path.getsize(ruta_guardado_final) / (1024 * 1024)
            print(f"✅ Mapa de pendientes guardado exitosamente")
            print(f"   Ubicación: {ruta_guardado_final}")
            print(f"   Tamaño: {file_size:.2f} MB")
            
            # Mostrar distribución de clases
            print(f"\n📈 DISTRIBUCIÓN DE PENDIENTES:")
            print("=" * 65)
            for clase in range(1, 6):
                count = stats['clases'][clase]
                porcentaje = (count / stats['total']) * 100 if stats['total'] > 0 else 0
                print(f"   {ETIQUETAS_PENDIENTE[clase-1]:<15}: {count:>6} celdas ({porcentaje:>5.1f}%)")
            print("=" * 65)
            print(f"   {'TOTAL':<15}: {stats['total']:>6} celdas")
            print("="*80 + "\n")
            
            return ruta_guardado_final
        else:
            print("❌ El archivo no se guardó correctamente")
            return None
            
    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}")
        import traceback
        traceback.print_exc()
        plt.close(fig)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Ejemplo de llamada a la función (la ruta DEM es opcional, se buscará automáticamente)
    resultado = generar_mapa_pendientes(
        nombre_usuario="TU_NOMBRE",
        departamento_sel="LIMA",
        provincia_sel="LIMA",
        distrito_sel="SAN ISIDRO"
        # ruta_dem="/content/DEM.nc"  # Opcional: si no se especifica, se busca automáticamente
    )
    
    if resultado:
        print(f"\n✅ Proceso completado exitosamente")
        print(f"📁 Archivo generado: {resultado}")
    else:
        print("\n❌ Hubo un error en la generación del mapa")