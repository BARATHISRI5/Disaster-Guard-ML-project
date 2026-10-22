"""
DisasterGuard — Image Preprocessing Module

Cloud masking, NDWI calculation, patch extraction, and SAR normalization
for satellite imagery preprocessing.
"""

import numpy as np


def apply_cloud_mask_qa60(image_array, qa60_band):
    """
    Apply cloud masking using Sentinel-2 QA60 band.
    Bits 10 (opaque clouds) and 11 (cirrus) are masked out.
    """
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    cloud_free = np.bitwise_and(qa60_band.astype(int), cloud_bit) == 0
    cirrus_free = np.bitwise_and(qa60_band.astype(int), cirrus_bit) == 0
    mask = cloud_free & cirrus_free
    if image_array.ndim == 3:
        mask = np.expand_dims(mask, axis=-1)
        mask = np.repeat(mask, image_array.shape[-1], axis=-1)
    return np.where(mask, image_array, np.nan)


def calculate_ndwi(green_band, nir_band):
    """
    Calculate Normalized Difference Water Index.
    NDWI = (Green - NIR) / (Green + NIR)
    Values > 0 indicate water bodies; higher = more water.
    """
    green = green_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = green + nir
    denominator = np.where(denominator == 0, 1e-10, denominator)
    ndwi = (green - nir) / denominator
    return np.clip(ndwi, -1.0, 1.0)


def calculate_ndvi(red_band, nir_band):
    """Calculate Normalized Difference Vegetation Index (for reference/comparison)."""
    red = red_band.astype(np.float32)
    nir = nir_band.astype(np.float32)
    denominator = nir + red
    denominator = np.where(denominator == 0, 1e-10, denominator)
    return np.clip((nir - red) / denominator, -1.0, 1.0)


def normalize_sar(sar_db):
    """Normalize SAR backscatter values from dB to 0-1 range using log scaling."""
    sar = np.clip(sar_db, -30, 0)
    return (sar + 30) / 30


def create_patches(image, patch_size=256, stride=128):
    """
    Tile a large image into overlapping patches.
    Returns list of (patch, row_start, col_start) tuples.
    """
    h, w = image.shape[:2]
    patches = []
    for i in range(0, h - patch_size + 1, stride):
        for j in range(0, w - patch_size + 1, stride):
            patch = image[i:i+patch_size, j:j+patch_size]
            if not np.isnan(patch).any():
                patches.append((patch, i, j))
    return patches


def normalize_image(image, method="minmax"):
    """Normalize image to 0-1 range."""
    if method == "minmax":
        mn, mx = np.nanmin(image), np.nanmax(image)
        if mx - mn == 0:
            return np.zeros_like(image)
        return (image - mn) / (mx - mn)
    elif method == "standard":
        mean, std = np.nanmean(image), np.nanstd(image)
        if std == 0:
            return np.zeros_like(image)
        return (image - mean) / std
    return image


def detect_water_expansion(ndwi_pre, ndwi_post, threshold=0.1):
    """
    Detect water body expansion by comparing pre/post NDWI images.
    Returns binary mask where water has expanded.
    """
    water_pre = ndwi_pre > 0.0
    water_post = ndwi_post > 0.0
    expansion = water_post & ~water_pre
    significant = (ndwi_post - ndwi_pre) > threshold
    return expansion & significant


def preprocess_for_cnn(image, target_size=(256, 256)):
    """Resize and normalize an image patch for CNN input."""
    from PIL import Image as PILImage
    if image.shape[:2] != target_size:
        pil_img = PILImage.fromarray((image * 255).astype(np.uint8))
        pil_img = pil_img.resize(target_size, PILImage.BILINEAR)
        image = np.array(pil_img).astype(np.float32) / 255.0
    if image.ndim == 2:
        image = np.expand_dims(image, axis=-1)
    return image


def generate_mock_ndwi_timeseries(num_days=30, flood_start=20):
    """Generate mock NDWI time series showing water level change for demo."""
    ndwi_values = np.random.uniform(-0.2, 0.1, num_days)
    for i in range(flood_start, num_days):
        ndwi_values[i] = min(0.8, ndwi_values[flood_start-1] + 0.05 * (i - flood_start + 1))
        ndwi_values[i] += np.random.uniform(-0.02, 0.02)
    return ndwi_values
