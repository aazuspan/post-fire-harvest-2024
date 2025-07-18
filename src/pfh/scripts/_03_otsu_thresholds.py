import ee

from pfh.scripts.config import (
    MAXDIFF_COLLECTION,
    OTSU_THRESHOLDS,
    STUDY_FIRE_COLLECTION,
)
from pfh.spectral import get_otsu_threshold

if __name__ == "__main__":
    ee.Initialize()

    study_area = ee.FeatureCollection(STUDY_FIRE_COLLECTION)
    maxdiff = ee.ImageCollection(MAXDIFF_COLLECTION).mosaic()

    swir2_threshold = get_otsu_threshold(image=maxdiff, band="SWIR2", region=study_area)
    red_threshold = get_otsu_threshold(image=maxdiff, band="Red", region=study_area)

    print("Processing thresholds...")

    thresholds = ee.FeatureCollection([
        ee.Feature(None, {"band": "SWIR2", "threshold": swir2_threshold}),
        ee.Feature(None, {"band": "Red", "threshold": red_threshold}),
    ])

    print("Exporting thresholds...")
    task = ee.batch.Export.table.toAsset(
        collection=thresholds,
        description="otsu_thresholds",
        assetId=OTSU_THRESHOLDS,
    )
    task.start()

    print(
        "Export started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
