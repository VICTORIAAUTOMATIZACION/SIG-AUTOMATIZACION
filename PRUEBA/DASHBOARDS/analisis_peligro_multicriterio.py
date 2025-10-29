# Archivo: analisis_peligro_multicriterio.py - CON RED DE RÍOS COMPLETA (SIN BORRAR PROCESOS)

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib_scalebar.scalebar import ScaleBar
import os
import numpy as np
import matplotlib.patheffects as path_effects
from shapely.geometry import box
from shapely.geometry import mapping
import datetime
import pandas as pd
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
import rasterio
from rasterio.mask import mask as rio_mask
from whitebox import WhiteboxTools
from shapely.ops import unary_union
import tempfile
import shutil
import time

# --- RUTA BASE ORIGINAL ---
ruta_base = "/workspaces/SIG-AUTOMATIZACION/PRUEBA"

# PALETA DE COLORES PARA RIESGO CONSOLIDADO
COLORES_RIESGO = {
    'muy_bajo': '#0080FF',
    'bajo': '#00FF00',
    'medio': '#FFFF00',
    'alto': '#FF7F00',
    'muy_alto': '#FF0000'
}

LIMITES_RIESGO = {
    'muy_bajo': (0, 20),
    'bajo': (20, 40),
    'medio': (40, 60),
    'alto': (60, 80),
    'muy_alto': (80, 100)
}

# FUNCIÓN PARA GENERAR RED DE RÍOS CON WHITEBOX (PROCESOS COMPLETOS)
def generar_red_rios_desde_geotiff(ruta_dem, gdf_distrito, intensidad="media"):
    """Genera red hidrográfica desde DEM usando WhiteboxTools - PROCESOS COMPLETOS SIN BORRAR"""
    print("   Generando red hidrográfica desde DEM con WhiteboxTools...")
    
    try:
        if not os.path.exists(ruta_dem):
            print(f"   ERROR: El archivo no existe: {ruta_dem}")
            return None, None
        
        print(f"   Archivo DEM encontrado: {ruta_dem}")
        
        temp_dir = tempfile.mkdtemp()
        print(f"   Directorio temporal: {temp_dir}")
        
        wbt = WhiteboxTools()
        wbt.set_working_dir(temp_dir)
        wbt.set_verbose_mode(False)
        
        with rasterio.open(ruta_dem) as src:
            print(f"   CRS del DEM: {src.crs}")
            print(f"   Dimensiones: {src.width} x {src.height}")
            
            gdf_distrito_reproj = gdf_distrito.to_crs(src.crs)
            
            buffer_dist = 1000
            gdf_buffer = gdf_distrito_reproj.copy()
            gdf_buffer['geometry'] = gdf_buffer.geometry.buffer(buffer_dist)
            
            geoms = [mapping(geom) for geom in gdf_buffer.geometry]
            
            out_image, out_transform = rio_mask(src, geoms, crop=True, filled=False)
            elevation = out_image[0]
            
            dem_clipped = os.path.join(temp_dir, "dem_clipped.tif")
            
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": elevation.shape[0],
                "width": elevation.shape[1],
                "transform": out_transform
            })
            
            with rasterio.open(dem_clipped, "w", **out_meta) as dest:
                dest.write(elevation, 1)
            
            print(f"   ✓ DEM recortado guardado")
        
        filled_dem = os.path.join(temp_dir, "filled.tif")
        flow_dir = os.path.join(temp_dir, "flow_dir.tif")
        flow_acc = os.path.join(temp_dir, "flow_acc.tif")
        streams_raster = os.path.join(temp_dir, "streams.tif")
        streams_vector = os.path.join(temp_dir, "streams.shp")
        
        print("   1/5 Rellenando depresiones...")
        wbt.fill_depressions(dem_clipped, filled_dem)
        
        print("   2/5 Calculando dirección de flujo...")
        wbt.d8_pointer(filled_dem, flow_dir)
        
        print("   3/5 Calculando acumulación de flujo...")
        wbt.d8_flow_accumulation(filled_dem, flow_acc, out_type="cells")
        
        UMBRALES = {
            "muy_alta": 50,
            "alta": 200,
            "media": 500,
            "baja": 1000,
            "muy_baja": 2000
        }
        
        threshold = UMBRALES.get(intensidad, 500)
        print(f"   Umbral de acumulación: {threshold} celdas (intensidad: {intensidad})")
        
        print("   4/5 Extrayendo red de ríos...")
        wbt.extract_streams(flow_acc, streams_raster, threshold)
        
        print("   5/5 Convirtiendo a vector...")
        wbt.raster_streams_to_vector(streams_raster, flow_dir, streams_vector)
        
        # Esperar a que se cree el archivo
        tiempo_espera = 0
        while not os.path.exists(streams_vector) and tiempo_espera < 30:
            time.sleep(0.5)
            tiempo_espera += 0.5
        
        if not os.path.exists(streams_vector):
            print(f"   ⚠️  El archivo streams.shp no se creó")
            print(f"   Archivos en directorio temporal:")
            for f in os.listdir(temp_dir):
                print(f"      - {f}")
            shutil.rmtree(temp_dir)
            return None, None
        
        rivers = gpd.read_file(streams_vector)
        
        if rivers.empty:
            print(f"   ⚠️  El shapefile de ríos está vacío")
            shutil.rmtree(temp_dir)
            return None, None
        
        if rivers.crs is None:
            with rasterio.open(dem_clipped) as dem_src:
                rivers = rivers.set_crs(dem_src.crs)
        
        rivers_3857 = rivers.to_crs(3857)
        gdf_distrito_3857 = gdf_distrito.to_crs(3857)
        rivers_clipped = gpd.clip(rivers_3857, gdf_distrito_3857)
        
        if rivers_clipped.empty:
            print(f"   ⚠️  No hay ríos dentro del distrito")
            shutil.rmtree(temp_dir)
            return None, None
        
        print(f"   ✓ Red de ríos generada: {len(rivers_clipped)} segmentos")
        
        rivers_clipped['length_km'] = rivers_clipped.geometry.length / 1000
        total_length = rivers_clipped['length_km'].sum()
        
        print(f"   ✓ Longitud total: {total_length:.2f} km")
        
        stats = {
            'segmentos': len(rivers_clipped),
            'longitud_total_km': total_length,
            'longitud_promedio_km': rivers_clipped['length_km'].mean() if len(rivers_clipped) > 0 else 0,
            'intensidad': intensidad,
            'umbral': threshold
        }
        
        # NO BORRAR - MANTENER EN MEMORIA
        print(f"   ✓ Archivos de proceso mantenidos en: {temp_dir}")
        
        return rivers_clipped, stats
                
    except Exception as e:
        print(f"   ERROR generando red de ríos: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# FUNCIÓN PARA GENERAR BUFFERS DE DISTANCIA CON PESOS (EN MEMORIA)
def generar_buffers_distancia(rivers_gdf, gdf_distrito):
    """Genera buffers de distancia a ríos con pesos"""
    print("   Generando buffers de distancia a ríos...")
    
    try:
        rivers_union = unary_union(rivers_gdf.geometry)
        
        buffers_config = [
            {"name": "0-50m", "inner": 0, "outer": 50, "peso": 5},
            {"name": "50-100m", "inner": 50, "outer": 100, "peso": 4},
            {"name": "100-150m", "inner": 100, "outer": 150, "peso": 3},
            {"name": "150-200m", "inner": 150, "outer": 200, "peso": 2},
            {"name": ">200m", "inner": 200, "outer": None, "peso": 1}
        ]
        
        buffer_list = []
        
        for config in buffers_config:
            name = config["name"]
            inner = config["inner"]
            outer = config["outer"]
            peso = config["peso"]
            
            if outer is None:
                outer_buffer = gdf_distrito.geometry.union_all()
                inner_buffer = rivers_union.buffer(inner)
                buffer_ring = outer_buffer.difference(inner_buffer)
            else:
                outer_buffer = rivers_union.buffer(outer)
                inner_buffer = rivers_union.buffer(inner)
                buffer_ring = outer_buffer.difference(inner_buffer)
                buffer_ring = buffer_ring.intersection(gdf_distrito.geometry.union_all())
            
            area_km2 = buffer_ring.area / 1_000_000
            
            gdf = gpd.GeoDataFrame(
                {
                    'clase': [name],
                    'PESO_RIO': [peso]
                },
                geometry=[buffer_ring],
                crs=rivers_gdf.crs
            )
            
            buffer_list.append(gdf)
            print(f"      {name:12} - Peso: {peso} - Área: {area_km2:.4f} km²")
        
        buffers_gdf = gpd.GeoDataFrame(pd.concat(buffer_list, ignore_index=True))
        return buffers_gdf
        
    except Exception as e:
        print(f"   ERROR generando buffers: {e}")
        import traceback
        traceback.print_exc()
        return None

def cargar_shapefile_completo(ruta_completa):
    """Carga un shapefile"""
    try:
        if not os.path.exists(ruta_completa):
            print(f"   ⚠️  Archivo no encontrado: {ruta_completa}")
            return None
        gdf = gpd.read_file(ruta_completa)
        if gdf.empty:
            print(f"   ⚠️  Shapefile vacío: {ruta_completa}")
            return None
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf.set_crs(epsg=4326, inplace=True)
        return gdf.to_crs(epsg=3857)
    except Exception as e:
        print(f"   ⚠️  Error cargando shapefile: {e}")
        return None

def rasterizar_shapefile(gdf, referencia_bounds, referencia_crs, resolucion=30, columna_peso=None):
    """Convierte GeoDataFrame a raster"""
    try:
        if gdf is None or gdf.empty:
            return None, None
        
        if gdf.crs != referencia_crs:
            gdf = gdf.to_crs(referencia_crs)
        
        minx, miny, maxx, maxy = referencia_bounds
        ancho = int((maxx - minx) / resolucion)
        alto = int((maxy - miny) / resolucion)
        
        transform = from_bounds(minx, miny, maxx, maxy, ancho, alto)
        raster = np.zeros((alto, ancho), dtype=np.float32)
        
        if columna_peso is None:
            columnas_posibles = ['PESO_RIO', 'PESO_GEOMO', 'gridcode', 'PESO_PPMAX']
            columna_peso = next((c for c in columnas_posibles if c in gdf.columns), None)
        
        for idx, row in gdf.iterrows():
            try:
                valor = row[columna_peso] if columna_peso and columna_peso in row else 1
                geom = row.geometry
                mask = geometry_mask([geom], out_shape=(alto, ancho), transform=transform, invert=True)
                raster[mask] = valor
            except:
                continue
        
        return raster, transform
    except Exception as e:
        print(f"   ⚠️  Error rasterizando: {e}")
        return None, None

def calcular_indice_riesgo_consolidado(gdf_rios, gdf_geomorfo, gdf_pendiente, gdf_ppmax, gdf_distrito, resolucion=30):
    """Calcula índice consolidado"""
    try:
        bounds = gdf_distrito.to_crs(3857).total_bounds
        crs = 3857
        
        rasters_validos = []
        
        if gdf_rios is not None and not gdf_rios.empty:
            r, _ = rasterizar_shapefile(gdf_rios, bounds, crs, resolucion, 'PESO_RIO')
            if r is not None:
                rasters_validos.append(r)
                print(f"   ✓ Raster de ríos generado")
        
        if gdf_geomorfo is not None and not gdf_geomorfo.empty:
            r, _ = rasterizar_shapefile(gdf_geomorfo, bounds, crs, resolucion, 'PESO_GEOMO')
            if r is not None:
                rasters_validos.append(r)
                print(f"   ✓ Raster de geomorfología generado")
        
        if gdf_pendiente is not None and not gdf_pendiente.empty:
            r, _ = rasterizar_shapefile(gdf_pendiente, bounds, crs, resolucion, 'gridcode')
            if r is not None:
                rasters_validos.append(r)
                print(f"   ✓ Raster de pendiente generado")
        
        if gdf_ppmax is not None and not gdf_ppmax.empty:
            r, _ = rasterizar_shapefile(gdf_ppmax, bounds, crs, resolucion, 'PESO_PPMAX')
            if r is not None:
                rasters_validos.append(r)
                print(f"   ✓ Raster de precipitación generado")
        
        if len(rasters_validos) == 0:
            print(f"   ⚠️  No hay rasters válidos para calcular índice")
            return None, None, None, None
        
        def normalizar_raster(raster):
            if raster is None or raster.max() == 0:
                return np.zeros_like(raster)
            raster_norm = np.copy(raster).astype(float)
            mask_valido = raster_norm > 0
            if mask_valido.sum() > 0:
                min_val = raster_norm[mask_valido].min()
                max_val = raster_norm[mask_valido].max()
                raster_norm[mask_valido] = ((raster_norm[mask_valido] - min_val) / (max_val - min_val + 0.0001)) * 100
            return raster_norm
        
        rasters_normalizados = [normalizar_raster(r) for r in rasters_validos]
        
        mascara_valida = np.zeros_like(rasters_normalizados[0], dtype=bool)
        for raster in rasters_normalizados:
            mascara_valida = mascara_valida | (raster > 0)
        
        raster_indice = np.zeros_like(rasters_normalizados[0])
        suma_rasters = np.zeros_like(rasters_normalizados[0])
        
        for raster in rasters_normalizados:
            suma_rasters = suma_rasters + raster
        
        raster_indice[mascara_valida] = suma_rasters[mascara_valida] / len(rasters_normalizados)
        
        _, transform = rasterizar_shapefile(gdf_geomorfo if gdf_geomorfo is not None else gpd.GeoDataFrame(geometry=[box(*bounds)], crs=crs), bounds, crs, resolucion)
        
        return raster_indice, transform, bounds, crs
        
    except Exception as e:
        print(f"   ⚠️  Error calculando índice: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

def convertir_raster_a_poligonos(raster, transform, bounds, crs):
    """Convierte raster a polígonos"""
    try:
        from rasterio.features import shapes as rasterio_shapes
        
        raster_clasificado = np.zeros_like(raster)
        
        for clase, (min_val, max_val) in LIMITES_RIESGO.items():
            mascara = (raster >= min_val) & (raster < max_val)
            raster_clasificado[mascara] = list(LIMITES_RIESGO.keys()).index(clase) + 1
        
        shapes_list = []
        for geom, valor in rasterio_shapes(raster_clasificado.astype(np.uint8), transform=transform):
            if valor > 0:
                clase_nombre = list(LIMITES_RIESGO.keys())[int(valor) - 1]
                valor_indice = raster[raster_clasificado == valor].mean()
                shapes_list.append({'geometry': geom, 'clase_riesgo': clase_nombre, 'indice': valor_indice})
        
        if shapes_list:
            return gpd.GeoDataFrame(shapes_list, crs=crs)
        return None
    except Exception as e:
        print(f"   ⚠️  Error convirtiendo a polígonos: {e}")
        return None

def add_north_arrow(ax, xy_pos=(0.93, 0.08), size=0.06):
    """Flecha norte"""
    from matplotlib.patches import Polygon
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
    ax.text(x_pos, y_pos + s * 1.5 + 0.015, "N", transform=ax.transAxes, fontsize=16, fontweight='bold', ha='center', va='center', color='white', path_effects=[path_effects.withStroke(linewidth=3, foreground='black')])

# FUNCIÓN PRINCIPAL
def generar_mapa_riesgo_consolidado(nombre_usuario, departamento_sel, provincia_sel, distrito_sel, ruta_dem=None, intensidad="media"):
    """Genera mapa de riesgo consolidado"""
    
    print("\n" + "="*80)
    print("INICIANDO GENERACIÓN DE MAPA DE RIESGO CONSOLIDADO")
    print(f"   Usuario: {nombre_usuario}")
    print(f"   Ubicación: {distrito_sel}, {provincia_sel}, {departamento_sel}")
    print("="*80)
    
    try:
        # Crear carpeta
        carpeta_usuario = os.path.join(ruta_base, "USUARIOS", nombre_usuario)
        carpeta_salida = os.path.join(carpeta_usuario, "MAPA DE RIESGO CONSOLIDADO")
        os.makedirs(carpeta_salida, exist_ok=True)
        print(f"   Carpeta de salida: {carpeta_salida}")
        
        # Cargar distrito
        print("\nCargando geometría del distrito...")
        gdf_distrito = None
        try:
            gdf_distritos = gpd.read_file(f"{ruta_base}/DATA/DISTRITOS/distritos.shp").to_crs(3857)
            gdf_distrito = gdf_distritos[(gdf_distritos['NOMBDIST'] == distrito_sel) & (gdf_distritos['NOMBPROV'] == provincia_sel)]
            if gdf_distrito.empty:
                print(f"   ⚠️  Distrito no encontrado, usando primer distrito disponible")
                gdf_distrito = gdf_distritos.head(1)
            print(f"   ✓ Distrito cargado")
        except Exception as e:
            print(f"   ❌ Error cargando distrito: {e}")
            return None
        
        if gdf_distrito is None or gdf_distrito.empty:
            print("❌ No se pudo cargar geometría del distrito")
            return None
        
        print("\nCargando parámetros de riesgo...")
        
        # DEPURACIÓN: Verificar rutas
        rutas_verificar = {
            'Geomorfología': f"{carpeta_usuario}/PELIGRO/01 GEOMORFOLOGIA/01_geomorfologia.shp",
            'Pendiente': f"{carpeta_usuario}/PELIGRO/02 PENDIENTE/02_pendiente.shp",
            'Precipitación': f"{carpeta_usuario}/PELIGRO/03 PRECIPITACION_MAXIMA/03_precipitacion_maxima.shp"
        }
        
        print("\n🔍 VERIFICANDO ARCHIVOS:")
        for nombre, ruta in rutas_verificar.items():
            existe = "✅" if os.path.exists(ruta) else "❌"
            print(f"   {existe} {nombre}: {ruta}")
        
        print(f"\n🔍 DEM: {'✅' if ruta_dem and os.path.exists(ruta_dem) else '❌'} {ruta_dem}")
        
        # 1. Red de ríos (GENERAR desde DEM)
        rivers_gdf = None
        rivers_stats = None
        buffers_rios = None
        
        if ruta_dem and os.path.exists(ruta_dem):
            print(f"\n1️⃣ GENERANDO RED DE RÍOS desde DEM (Intensidad: {intensidad})...")
            rivers_gdf, rivers_stats = generar_red_rios_desde_geotiff(ruta_dem, gdf_distrito, intensidad)
            if rivers_gdf is not None and not rivers_gdf.empty:
                print(f"   ✓ Red de ríos generada: {rivers_stats['segmentos']} segmentos, {rivers_stats['longitud_total_km']:.2f} km")
                
                # Generar buffers de distancia
                buffers_rios = generar_buffers_distancia(rivers_gdf, gdf_distrito)
                if buffers_rios is not None:
                    print(f"   ✓ Buffers de distancia generados")
                else:
                    print(f"   ⚠️ No se pudieron generar buffers")
            else:
                print(f"   ⚠️ No se pudo generar red de ríos")
        else:
            print(f"\n1️⃣ ⚠️ DEM no encontrado o no especificado - Red de ríos omitida")
        
        # 2. Geomorfología
        print(f"\n2️⃣ CARGANDO GEOMORFOLOGÍA...")
        gdf_geomorfo = cargar_shapefile_completo(f"{carpeta_usuario}/PELIGRO/01 GEOMORFOLOGIA/01_geomorfologia.shp")
        if gdf_geomorfo is not None:
            print(f"   ✓ Geomorfología cargada: {len(gdf_geomorfo)} polígonos")
        else:
            print(f"   ⚠️ Geomorfología no disponible")
        
        # 3. Pendiente
        print(f"\n3️⃣ CARGANDO PENDIENTE...")
        gdf_pendiente = cargar_shapefile_completo(f"{carpeta_usuario}/PELIGRO/02 PENDIENTE/02_pendiente.shp")
        if gdf_pendiente is not None:
            print(f"   ✓ Pendiente cargada: {len(gdf_pendiente)} polígonos")
        else:
            print(f"   ⚠️ Pendiente no disponible")
        
        # 4. Precipitación máxima
        print(f"\n4️⃣ CARGANDO PRECIPITACIÓN MÁXIMA...")
        gdf_ppmax = cargar_shapefile_completo(f"{carpeta_usuario}/PELIGRO/03 PRECIPITACION_MAXIMA/03_precipitacion_maxima.shp")
        if gdf_ppmax is not None:
            print(f"   ✓ Precipitación máxima cargada: {len(gdf_ppmax)} polígonos")
        else:
            print(f"   ⚠️ Precipitación máxima no disponible")
        
        # Verificar que al menos tengamos algo para procesar
        parametros_disponibles = sum([
            buffers_rios is not None,
            gdf_geomorfo is not None,
            gdf_pendiente is not None,
            gdf_ppmax is not None
        ])
        
        if parametros_disponibles == 0:
            print("\n❌ ERROR: No hay parámetros disponibles para generar el mapa")
            return None
        
        print(f"\n✓ Parámetros disponibles: {parametros_disponibles}/4")
        
        # Calcular índice consolidado
        print("\n📊 CALCULANDO ÍNDICE DE RIESGO CONSOLIDADO...")
        raster_indice, transform, bounds, crs = calcular_indice_riesgo_consolidado(
            buffers_rios, gdf_geomorfo, gdf_pendiente, gdf_ppmax, gdf_distrito
        )
        
        if raster_indice is None:
            print("\n❌ ERROR: No se pudo calcular el índice de riesgo")
            return None
        
        print(f"   ✓ Índice calculado - Rango: [{raster_indice.min():.2f}, {raster_indice.max():.2f}]")
        
        # Convertir a polígonos
        print("\n🗺️ CONVIRTIENDO A POLÍGONOS...")
        gdf_riesgo = convertir_raster_a_poligonos(raster_indice, transform, bounds, crs)
        
        if gdf_riesgo is None or gdf_riesgo.empty:
            print("\n❌ ERROR: No se pudieron generar polígonos de riesgo")
            return None
        
        print(f"   ✓ Polígonos generados: {len(gdf_riesgo)}")
        
        # Generar mapa
        print("\n🎨 GENERANDO MAPA...")
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Plotear por clase de riesgo
        for clase in ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto']:
            gdf_clase = gdf_riesgo[gdf_riesgo['clase_riesgo'] == clase]
            if not gdf_clase.empty:
                gdf_clase.plot(ax=ax, color=COLORES_RIESGO[clase], alpha=0.7, 
                              edgecolor='black', linewidth=0.3, label=clase.replace('_', ' ').title())
        
        # Agregar distrito
        gdf_distrito.boundary.plot(ax=ax, color='black', linewidth=2, linestyle='--')
        
        # Agregar ríos si existen
        if rivers_gdf is not None:
            rivers_gdf.plot(ax=ax, color='blue', linewidth=1.5, alpha=0.8, label='Red Hidrográfica')
        
        # Agregar mapa base
        try:
            ctx.add_basemap(ax, crs=gdf_distrito.crs, source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.3)
        except:
            print("   ⚠️ No se pudo agregar mapa base")
            pass
        # Configurar mapa
        ax.set_title(f"Mapa de Riesgo Consolidado - {distrito_sel}, {provincia_sel}, {departamento_sel}", 
                     fontsize=18, fontweight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax.set_xlabel("Longitud", fontsize=12)
        ax.set_ylabel("Latitud", fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Agregar elementos cartográficos
        add_north_arrow(ax)
        scalebar = ScaleBar(1, location='lower right', box_alpha=0.8, scale_loc='top')
        ax.add_artist(scalebar)
        
        # Agregar texto con información
        info_text = f"Parámetros: {parametros_disponibles}/4\n"
        info_text += f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                fontsize=9, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Guardar mapa
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(carpeta_salida, f"mapa_riesgo_consolidado_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✅ MAPA GENERADO EXITOSAMENTE")
        print(f"   📁 Ruta: {output_path}")
        
        # Guardar shapefile de riesgo
        shp_path = os.path.join(carpeta_salida, f"riesgo_consolidado_{timestamp}.shp")
        gdf_riesgo.to_file(shp_path)
        print(f"   📁 Shapefile: {shp_path}")
        
        # Guardar red de ríos si existe
        if rivers_gdf is not None:
            rivers_path = os.path.join(carpeta_salida, f"red_rios_{timestamp}.shp")
            rivers_gdf.to_file(rivers_path)
            print(f"   📁 Red de ríos: {rivers_path}")
        
        # Generar reporte estadístico
        print("\n📊 ESTADÍSTICAS DEL ANÁLISIS:")
        print("="*60)
        
        for clase in ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto']:
            gdf_clase = gdf_riesgo[gdf_riesgo['clase_riesgo'] == clase]
            if not gdf_clase.empty:
                area_km2 = gdf_clase.geometry.area.sum() / 1_000_000
                porcentaje = (area_km2 / (gdf_distrito.geometry.area.sum() / 1_000_000)) * 100
                print(f"   {clase.replace('_', ' ').title():15} : {area_km2:8.2f} km² ({porcentaje:5.2f}%)")
        
        print("="*60)
        
        # Guardar estadísticas en CSV
        stats_list = []
        for clase in ['muy_bajo', 'bajo', 'medio', 'alto', 'muy_alto']:
            gdf_clase = gdf_riesgo[gdf_riesgo['clase_riesgo'] == clase]
            if not gdf_clase.empty:
                area_km2 = gdf_clase.geometry.area.sum() / 1_000_000
                porcentaje = (area_km2 / (gdf_distrito.geometry.area.sum() / 1_000_000)) * 100
                stats_list.append({
                    'Clase_Riesgo': clase.replace('_', ' ').title(),
                    'Area_km2': area_km2,
                    'Porcentaje': porcentaje
                })
        
        df_stats = pd.DataFrame(stats_list)
        csv_path = os.path.join(carpeta_salida, f"estadisticas_{timestamp}.csv")
        df_stats.to_csv(csv_path, index=False)
        print(f"   📁 Estadísticas: {csv_path}")
        
        # Generar reporte de ríos si existe
        if rivers_stats is not None:
            print("\n🌊 ESTADÍSTICAS RED HIDROGRÁFICA:")
            print("="*60)
            print(f"   Segmentos totales    : {rivers_stats['segmentos']}")
            print(f"   Longitud total       : {rivers_stats['longitud_total_km']:.2f} km")
            print(f"   Longitud promedio    : {rivers_stats['longitud_promedio_km']:.2f} km")
            print(f"   Intensidad           : {rivers_stats['intensidad']}")
            print(f"   Umbral acumulación   : {rivers_stats['umbral']} celdas")
            print("="*60)
            
            # Guardar estadísticas de ríos
            rivers_stats_df = pd.DataFrame([rivers_stats])
            rivers_csv = os.path.join(carpeta_salida, f"estadisticas_rios_{timestamp}.csv")
            rivers_stats_df.to_csv(rivers_csv, index=False)
            print(f"   📁 Estadísticas ríos: {rivers_csv}")
        
        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80 + "\n")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL en generación de mapa: {e}")
        import traceback
        traceback.print_exc()
        return None


# FUNCIÓN AUXILIAR PARA TESTING
def test_generacion_mapa():
    """Función de prueba"""
    print("\n" + "="*80)
    print("🧪 MODO DE PRUEBA - GENERACIÓN DE MAPA DE RIESGO")
    print("="*80 + "\n")
    
    # Parámetros de prueba
    nombre_usuario = "DDAO"
    departamento = "CUSCO"
    provincia = "ANTA"
    distrito = "PUCYURA"
    ruta_dem = "/workspaces/SIG-AUTOMATIZACION/PRUEBA/DATA/DEM/dem_srtm_30m.tif"
    intensidad = "media"
    
    print(f"📋 Parámetros de prueba:")
    print(f"   Usuario       : {nombre_usuario}")
    print(f"   Departamento  : {departamento}")
    print(f"   Provincia     : {provincia}")
    print(f"   Distrito      : {distrito}")
    print(f"   DEM           : {ruta_dem}")
    print(f"   Intensidad    : {intensidad}\n")
    
    # Ejecutar
    resultado = generar_mapa_riesgo_consolidado(
        nombre_usuario=nombre_usuario,
        departamento_sel=departamento,
        provincia_sel=provincia,
        distrito_sel=distrito,
        ruta_dem=ruta_dem,
        intensidad=intensidad
    )
    
    if resultado:
        print(f"\n✅ PRUEBA EXITOSA")
        print(f"   Mapa generado: {resultado}")
        return True
    else:
        print(f"\n❌ PRUEBA FALLIDA")
        return False


# EJECUCIÓN PRINCIPAL
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*80)
    print("🗺️  SISTEMA DE ANÁLISIS DE PELIGRO MULTICRITERIO")
    print("="*80 + "\n")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Modo prueba
            test_generacion_mapa()
        else:
            # Modo con parámetros
            if len(sys.argv) >= 6:
                nombre_usuario = sys.argv[1]
                departamento = sys.argv[2]
                provincia = sys.argv[3]
                distrito = sys.argv[4]
                ruta_dem = sys.argv[5]
                intensidad = sys.argv[6] if len(sys.argv) > 6 else "media"
                
                generar_mapa_riesgo_consolidado(
                    nombre_usuario=nombre_usuario,
                    departamento_sel=departamento,
                    provincia_sel=provincia,
                    distrito_sel=distrito,
                    ruta_dem=ruta_dem,
                    intensidad=intensidad
                )
            else:
                print("❌ Error: Parámetros insuficientes")
                print("\nUso:")
                print("  python analisis_peligro_multicriterio.py <usuario> <dpto> <prov> <dist> <dem> [intensidad]")
                print("  python analisis_peligro_multicriterio.py test")
                print("\nEjemplo:")
                print("  python analisis_peligro_multicriterio.py DDAO CUSCO ANTA PUCYURA /path/dem.tif media")
    else:
        # Modo interactivo
        print("💡 Ejecutando en modo de prueba...")
        print("   Para modo con parámetros, use:")
        print("   python analisis_peligro_multicriterio.py <usuario> <dpto> <prov> <dist> <dem> [intensidad]\n")
        test_generacion_mapa()