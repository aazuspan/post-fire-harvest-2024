import ee

from pfh import composites, spectral
from pfh.scripts.config import (
    MAXDIFF_COLLECTION,
    STUDY_FIRE_COLLECTION,
)


def generate_fire_maxdiff(fire: ee.Feature) -> ee.Image:
    """Generate a maximum spectral difference and timing composite for a single fire."""
    pairs = composites.get_landsat_composites(fire, mask_forest=True)

    # Check if any start or end composites was created without valid input images
    pair_imgs = ee.ImageCollection([
        pair[img] for pair in pairs for img in ["start", "end"]
    ])
    missing_img = ee.Number(pair_imgs.aggregate_min("num_images")).eq(0)

    pairs = composites.match_pairs(
        pairs=pairs,
        method="sed",
        percentile=80,
        bands=["SWIR2", "Green", "Red"],
        geometry=fire.geometry(),
    )
    maxdiff = composites.max_difference(pairs, timing_band="SWIR2")
    clustered = spectral.snic_cluster(maxdiff, cluster_bands=ee.List(["SWIR2", "Red"]))

    return ee.Algorithms.If(missing_img, None, clustered)


def generate_maxdiffs(fires: ee.FeatureCollection) -> None:
    """Generate maximum spectral difference and timing composites from a collection of
    MTBS study fires. One composite will be exported per year.
    """
    fire_years = (
        fires.aggregate_array("Ig_Date")
        .map(lambda dt: ee.Date(dt).get("year"))
        .distinct()
        .sort()
        .getInfo()
    )
    for year in fire_years:
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = start_date.advance(1, "year")

        year_fires = fires.filter(
            ee.Filter.And(
                ee.Filter.gte("Ig_Date", start_date.millis()),
                ee.Filter.lt("Ig_Date", end_date.millis()),
            )
        )
        year_maxdiffs = ee.ImageCollection(
            year_fires.map(generate_fire_maxdiff, dropNulls=True)
        )

        metadata = {
            "year": year,
            "system:time_start": start_date.millis(),
            "system:time_end": end_date.millis(),
        }
        maxdiff = year_maxdiffs.mosaic().set(metadata)

        # Export to asset
        asset_id = f"{MAXDIFF_COLLECTION}/{year}"
        print(f"Exporting {asset_id}...")

        task = ee.batch.Export.image.toAsset(
            image=maxdiff,
            description=f"maxdiff_{year}",
            assetId=asset_id,
            region=year_fires.geometry().bounds(),
            scale=30,
            crs="EPSG:5070",
            maxPixels=1e13,
        )

        task.start()


if __name__ == "__main__":
    ee.Initialize()
    # Calculate maxdiff for all candidate fires with valid pixels
    fires = ee.FeatureCollection(STUDY_FIRE_COLLECTION).filter(
        ee.Filter.gt("percent_forest", 0)
    )
    generate_maxdiffs(fires)
    print(
        "Exports started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
