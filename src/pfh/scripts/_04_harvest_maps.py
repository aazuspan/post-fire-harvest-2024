import ee

from pfh.scripts.config import (
    HARVEST_COLLECTION,
    MAXDIFF_COLLECTION,
    OTSU_THRESHOLDS,
    STUDY_FIRE_COLLECTION,
)
from pfh.spectral import classify_harvests

if __name__ == "__main__":
    ee.Initialize()

    thresholds = ee.FeatureCollection(OTSU_THRESHOLDS)
    swir2_threshold = (
        thresholds.filter(ee.Filter.eq("band", "SWIR2")).first().getNumber("threshold")
    )
    red_threshold = (
        thresholds.filter(ee.Filter.eq("band", "Red")).first().getNumber("threshold")
    )

    study_fires = ee.FeatureCollection(STUDY_FIRE_COLLECTION)
    maxdiffs = ee.ImageCollection(MAXDIFF_COLLECTION)
    thresholds = ee.Image.constant([swir2_threshold, red_threshold])

    harvests = maxdiffs.map(
        lambda x: classify_harvests(x, bands=["SWIR2", "Red"], thresholds=thresholds)
    )
    years = harvests.aggregate_array("year").getInfo()

    for year in years:
        asset_id = f"{HARVEST_COLLECTION}/{year}"
        harvest_year = harvests.filter(ee.Filter.eq("year", year)).first().byte()

        region = (
            study_fires.filter(
                ee.Filter.And(
                    ee.Filter.gte("Ig_Date", ee.Date.fromYMD(year, 1, 1)),
                    ee.Filter.lt("Ig_Date", ee.Date.fromYMD(year + 1, 1, 1)),
                )
            )
            .geometry()
            .bounds()
        )
        print(f"Exporting {asset_id}...")

        task = ee.batch.Export.image.toAsset(
            image=harvest_year,
            description=f"harvest_{year}",
            assetId=asset_id,
            region=region,
            scale=30,
            crs="EPSG:5070",
            maxPixels=1e13,
        )

        task.start()

    print(
        "Exports started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
