import math
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import os
from qgis.utils import iface

from qgis.PyQt.QtWidgets import QFileDialog

from qgis.core import QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform

def latlon_to_quadkey(lat, lon, zoom=9):
    sin_lat = math.sin(math.radians(lat))
    x = (lon + 180.0) / 360.0
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))
    
    map_size = 256 * (2 ** zoom)
    pixel_x = int(x * map_size)
    pixel_y = int(y * map_size)
    tile_x = pixel_x // 256
    tile_y = pixel_y // 256
    
    quadkey = ""
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (tile_x & mask) != 0:
            digit += 1
        if (tile_y & mask) != 0:
            digit += 2
        quadkey += str(digit)
    return int(quadkey)

def get_screen_center():
    canvas = iface.mapCanvas()
    point = iface.mapCanvas().extent().center()
    crsSrc = canvas.mapSettings().destinationCrs()  # QGIS CRS
    crsDest = QgsCoordinateReferenceSystem(4326)  # WGS84
    coordTransform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
    point = coordTransform.transform(point)
    print(f"Center: {point}")
    return point

def load_buildings():
    quadKey = latlon_to_quadkey(get_screen_center().y(), get_screen_center().x())
    csv_path = r"C:\Users\brych\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\microsoft_buildings_downloader\MicrosoftBuildings\dataset-links.csv"
    # csv_path = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"
    # if not os.path.exists(csv_path):
    #     print(f"Path {csv_path} does not exist")
    #     return
    dataset_links = pd.read_csv(csv_path)
    print(f"Quadkey: {quadKey}")
    links = dataset_links[dataset_links.QuadKey == quadKey]
    print(f"Greece links: {links}")
    if links.empty:
        print("No links found")
        return

    filename, _ = QFileDialog.getSaveFileName(None, "Save GeoJSON", "", "GeoJSON Files (*.geojson)")
    if not filename:
        return
    i = 1
    for _, row in links.iterrows():
        df = pd.read_json(row.Url, lines=True)
        df['geometry'] = df['geometry'].apply(shape)
        gdf = gpd.GeoDataFrame(df, crs=4326)
        cur_filename = filename.replace(".geojson", f"_{i}.geojson")
        gdf.to_file(cur_filename, driver="GeoJSON")
        json_layer = QgsVectorLayer(cur_filename, "buildings", "ogr")
        QgsProject.instance().addMapLayer(json_layer)
        i += 1
    return


load_buildings()


