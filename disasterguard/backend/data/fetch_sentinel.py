"""
DisasterGuard — Google Earth Engine Data Fetching Module

Fetches Sentinel-1 SAR, Sentinel-2 optical, and MODIS surface reflectance
data for Tamil Nadu coastal districts. Supports mock data mode for offline demos.
"""

import os
import numpy as np
from datetime import datetime, timedelta

DISTRICT_BOUNDS = {
    "Chennai": [80.0, 12.85, 80.35, 13.25],
    "Thoothukudi": [77.9, 8.5, 78.5, 9.0],
    "Tirunelveli": [77.1, 8.15, 77.9, 9.0],
    "Nagapattinam": [79.5, 10.6, 79.95, 11.1],
    "Cuddalore": [79.3, 11.3, 79.85, 11.8],
    "Ramanathapuram": [78.6, 9.2, 79.5, 9.8],
    "Kanyakumari": [77.0, 8.0, 77.6, 8.4],
    "Villupuram": [79.1, 11.7, 79.7, 12.2],
}

FLOOD_EVENTS = {
    "Chennai_2015": {"start": "2015-11-15", "end": "2015-12-15", "district": "Chennai"},
    "TN_2021_Nov": {"start": "2021-11-01", "end": "2021-12-01", "district": "Chennai"},
    "Thoothukudi_2021": {"start": "2021-12-15", "end": "2022-01-10", "district": "Thoothukudi"},
    "Nagapattinam_2018": {"start": "2018-11-10", "end": "2018-12-05", "district": "Nagapattinam"},
}


def initialize_gee(service_account_email=None, key_path=None):
    """Initialize Google Earth Engine with service account or interactive auth."""
    try:
        import ee
        if service_account_email and key_path:
            credentials = ee.ServiceAccountCredentials(service_account_email, key_path)
            ee.Initialize(credentials)
        else:
            ee.Authenticate()
            ee.Initialize()
        print("✅ Google Earth Engine initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️  GEE initialization failed: {e}. Running in mock data mode.")
        return False


def fetch_sentinel1_sar(district, start_date, end_date, export_to_drive=False):
    """Fetch Sentinel-1 GRD SAR imagery (VV/VH polarization) — cloud-penetrating."""
    try:
        import ee
        bounds = DISTRICT_BOUNDS.get(district)
        if not bounds:
            raise ValueError(f"Unknown district: {district}")
        aoi = ee.Geometry.Rectangle(bounds)
        collection = (
            ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(aoi).filterDate(start_date, end_date)
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .select(["VV", "VH"])
        )
        count = collection.size().getInfo()
        print(f"📡 Found {count} Sentinel-1 SAR images for {district}")
        if export_to_drive and count > 0:
            composite = collection.mean().clip(aoi)
            task = ee.batch.Export.image.toDrive(
                image=composite, description=f"S1_SAR_{district}_{start_date}",
                folder="DisasterGuard_SAR", region=aoi, scale=10, maxPixels=1e9,
                fileFormat="GeoTIFF")
            task.start()
        return {"count": count, "district": district, "date_range": [start_date, end_date],
                "bands": ["VV", "VH"], "resolution_m": 10}
    except ImportError:
        return _mock_sentinel1_sar(district, start_date, end_date)


def fetch_sentinel2_optical(district, start_date, end_date, max_cloud_pct=20, export_to_drive=False):
    """Fetch Sentinel-2 L2A optical imagery with cloud masking (QA60 band)."""
    try:
        import ee
        bounds = DISTRICT_BOUNDS.get(district)
        if not bounds:
            raise ValueError(f"Unknown district: {district}")
        aoi = ee.Geometry.Rectangle(bounds)

        def mask_clouds_s2(image):
            qa = image.select("QA60")
            cloud_bit_mask, cirrus_bit_mask = 1 << 10, 1 << 11
            mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
            return image.updateMask(mask).divide(10000)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi).filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
            .map(mask_clouds_s2)
            .select(["B2", "B3", "B4", "B8", "B11", "B12"])
        )
        count = collection.size().getInfo()
        print(f"🛰️  Found {count} Sentinel-2 images for {district}")
        if export_to_drive and count > 0:
            composite = collection.median().clip(aoi)
            ndwi = composite.normalizedDifference(["B3", "B8"]).rename("NDWI")
            task = ee.batch.Export.image.toDrive(
                image=composite.addBands(ndwi), description=f"S2_{district}_{start_date}",
                folder="DisasterGuard_Optical", region=aoi, scale=10, maxPixels=1e9,
                fileFormat="GeoTIFF")
            task.start()
        return {"count": count, "district": district, "date_range": [start_date, end_date],
                "bands": ["B2", "B3", "B4", "B8", "B11", "B12"], "resolution_m": 10}
    except ImportError:
        return _mock_sentinel2_optical(district, start_date, end_date)


def fetch_modis_surface_reflectance(district, start_date, end_date):
    """Fetch MODIS daily surface reflectance (MOD09GA) for rapid flood/fire detection."""
    try:
        import ee
        bounds = DISTRICT_BOUNDS.get(district)
        if not bounds:
            raise ValueError(f"Unknown district: {district}")
        aoi = ee.Geometry.Rectangle(bounds)

        def mask_modis_quality(image):
            qa = image.select("state_1km")
            return image.updateMask(qa.bitwiseAnd(3).eq(0))

        collection = (
            ee.ImageCollection("MODIS/061/MOD09GA")
            .filterBounds(aoi).filterDate(start_date, end_date)
            .map(mask_modis_quality)
            .select(["sur_refl_b01", "sur_refl_b02", "sur_refl_b03", "sur_refl_b04", "sur_refl_b06"])
        )
        count = collection.size().getInfo()
        print(f"🌍 Found {count} MODIS images for {district}")
        return {"count": count, "district": district, "date_range": [start_date, end_date],
                "bands": ["Red", "NIR", "Blue", "Green", "SWIR"], "resolution_m": 500}
    except ImportError:
        return _mock_modis_data(district, start_date, end_date)


# ---- Mock Data Functions ----

def _mock_sentinel1_sar(district, start_date, end_date):
    print(f"🔧 [MOCK] Generating synthetic SAR data for {district}")
    return {"data": np.random.uniform(-25, 0, (256, 256, 2)).astype(np.float32),
            "count": 12, "district": district, "date_range": [start_date, end_date],
            "bands": ["VV", "VH"], "resolution_m": 10, "mock": True}

def _mock_sentinel2_optical(district, start_date, end_date):
    print(f"🔧 [MOCK] Generating synthetic optical data for {district}")
    return {"data": np.random.uniform(0, 1, (256, 256, 6)).astype(np.float32),
            "count": 8, "district": district, "date_range": [start_date, end_date],
            "bands": ["B2", "B3", "B4", "B8", "B11", "B12"], "resolution_m": 10, "mock": True}

def _mock_modis_data(district, start_date, end_date):
    print(f"🔧 [MOCK] Generating synthetic MODIS data for {district}")
    return {"data": np.random.uniform(0, 5000, (256, 256, 5)).astype(np.float32),
            "count": 30, "district": district, "date_range": [start_date, end_date],
            "bands": ["Red", "NIR", "Blue", "Green", "SWIR"], "resolution_m": 500, "mock": True}


def generate_mock_patches(num_patches=100, patch_size=256, num_flood=50):
    """Generate synthetic flood/no-flood image patches for CNN training demo."""
    patches, labels = [], []
    for i in range(num_patches):
        if i < num_flood:
            patch = np.random.uniform(0, 0.3, (patch_size, patch_size, 3)).astype(np.float32)
            patch[:, :, 2] = np.random.uniform(0.3, 0.7, (patch_size, patch_size))
            cx, cy = np.random.randint(50, 200, 2)
            r = np.random.randint(30, 80)
            y, x = np.ogrid[-cx:patch_size-cx, -cy:patch_size-cy]
            patch[x*x + y*y <= r*r] = [0.05, 0.1, 0.4]
            labels.append(1)
        else:
            patch = np.random.uniform(0.2, 0.7, (patch_size, patch_size, 3)).astype(np.float32)
            patch[:, :, 1] = np.random.uniform(0.3, 0.8, (patch_size, patch_size))
            labels.append(0)
        patches.append(patch)
    return np.array(patches), np.array(labels)
