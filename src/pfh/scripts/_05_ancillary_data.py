import ee

from pfh import composites, landsat
from pfh.scripts.config import (
    MAXDIFF_COLLECTION,
    OWNER_CLASSES,
    OWNERSHIP_MAP,
    SEVERITY_COLLECTION,
    STUDY_AREA_COLLECTION,
    STUDY_FIRE_COLLECTION,
    VALIDATION_PLOTS,
)


def export_ownership_map() -> None:
    """Export a classified ownership raster based on GAP data."""
    gap = ee.FeatureCollection("USGS/GAP/PAD-US/v20/fee")
    wdpa = ee.FeatureCollection("WCMC/WDPA/current/polygons")
    # https://catalog.data.gov/dataset/tiger-line-shapefile-2019-nation-u-s-current-tribal-census-tract-national
    tribal = ee.FeatureCollection("projects/salvage-2023/assets/tribal_ownership")

    wilderness = wdpa.filter(ee.Filter.eq("DESIG", "Wilderness"))
    fed = gap.filter(ee.Filter.eq("Mang_Type", "FED"))
    nps = gap.filter(ee.Filter.eq("Mang_Name", "NPS"))
    blm = gap.filter(ee.Filter.eq("Mang_Name", "BLM"))
    usfs = gap.filter(ee.Filter.eq("Mang_Name", "USFS"))

    # Paint with increasingly specific classes
    owner_mask = (
        (
            ee.Image(OWNER_CLASSES["private"])
            .paint(gap, OWNER_CLASSES["nonfed_public"])
            .paint(fed, OWNER_CLASSES["other_fed"])
            .paint(nps, OWNER_CLASSES["nps"])
            .paint(blm, OWNER_CLASSES["blm"])
            .paint(usfs, OWNER_CLASSES["usfs"])
            .paint(tribal, OWNER_CLASSES["tribal"])
            # Overwrite USFS with wilderness class
            .paint(wilderness, OWNER_CLASSES["wilderness"])
        )
        .byte()
        .rename("owner")
    )

    study_region = ee.FeatureCollection(STUDY_AREA_COLLECTION)

    task = ee.batch.Export.image.toAsset(
        # Avoid clipping to the study region to prevent cutting off portions of fires
        image=owner_mask,
        description="ownership_map",
        assetId=OWNERSHIP_MAP,
        region=study_region.geometry().bounds(),
        scale=30,
        crs="EPSG:5070",
        maxPixels=1e13,
        pyramidingPolicy={"owner": "mode"},
    )
    task.start()


def export_severity_maps() -> None:
    """Export annual NBR maps for all study years (imm. and ext. assessments)."""

    def apply_scale_and_offset(img: ee.Image) -> ee.Image:
        """Apply scale and offset to Landsat imagery."""
        return img.multiply(0.0000275).add(-0.2)

    def get_severity(fire: ee.Feature) -> ee.Image:
        """Get burn severity based on 1-year pre-fire and immediate post-fire
        imagery."""
        pairs = composites.get_landsat_composites(fire=fire, years=1, mask_forest=False)
        year = ee.Date(fire.get("Ig_Date")).get("year")
        start = ee.Date.fromYMD(year, 6, 20)
        end = ee.Date.fromYMD(year, 9, 20)
        fire_mask = ee.Image(1).clip(fire.geometry())

        imgs = landsat.load_landsat()
        postfire = pairs[0]["start"]
        prefire = (
            imgs.filterBounds(fire.geometry())
            .filterDate(start.advance(-1, "year"), end.advance(-1, "year"))
            .map(landsat.quality_mask)
            .median()
            .updateMask(fire_mask)
        )

        prefire = apply_scale_and_offset(prefire)
        postfire = apply_scale_and_offset(postfire)

        pre_nbr = prefire.normalizedDifference(["NIR", "SWIR2"]).multiply(1_000)
        post_nbr = postfire.normalizedDifference(["NIR", "SWIR2"]).multiply(1_000)
        dnbr = pre_nbr.subtract(post_nbr)
        rdnbr = dnbr.divide(pre_nbr.divide(1_000).abs().sqrt())
        return rdnbr.gt([166.5, 235.5, 649]).reduce(ee.Reducer.sum()).rename("severity")

    study_fires = ee.FeatureCollection(STUDY_FIRE_COLLECTION)
    years = (
        study_fires.aggregate_array("Ig_Date")
        .map(lambda d: ee.Date(d).get("year"))
        .distinct()
        .sort()
        .getInfo()
    )

    for year in years:
        print(f"Exporting severity map for {year}")
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = start_date.advance(1, "year")

        year_fires = study_fires.filter(
            ee.Filter.And(
                ee.Filter.gte("Ig_Date", start_date.millis()),
                ee.Filter.lt("Ig_Date", end_date.millis()),
            )
        )

        severity = (
            ee.ImageCollection(year_fires.map(get_severity))
            .mosaic()
            .set({
                "system:time_start": start_date.millis(),
                "system:time_end": end_date.millis(),
            })
        )

        task = ee.batch.Export.image.toAsset(
            image=severity.uint8(),
            description=f"severity_{year}",
            assetId=f"{SEVERITY_COLLECTION}/{year}",
            region=year_fires.geometry().bounds(),
            scale=30,
            crs="EPSG:5070",
            maxPixels=1e13,
        )
        task.start()


def export_validation_plots() -> None:
    """Generate and export validation plots, stratified by spectral change.

    Note: Study fires were adjusted slightly after validation plots were generated and
    interpreted (5 fires were excluded as out-of-bounds), so this will NOT generate the
    exact set of plots from the paper. This should have no impact on results, but is
    mentioned in the interest of reproducibility.
    """
    maxdiff = ee.ImageCollection(MAXDIFF_COLLECTION)
    study_fires = ee.FeatureCollection(STUDY_FIRE_COLLECTION)

    states = ee.FeatureCollection("TIGER/2018/States")
    california = ee.Feature(states.filter(ee.Filter.eq("NAME", "California")).first())
    oregon = ee.Feature(states.filter(ee.Filter.eq("NAME", "Oregon")).first())
    washington = ee.Feature(states.filter(ee.Filter.eq("NAME", "Washington")).first())

    def add_year_band(img):
        year = ee.Image(img.date().get("year")).rename("fire_year").uint16()
        return img.addBands(year.updateMask(img.select(0).mask()))

    maxdiff = maxdiff.map(add_year_band)

    # Filter data so we can get NAIP 1 year pre-fire and 5 years post-fire
    # First available NAIP: 2003 (CA), 2004 (OR), 2006 (WA)
    # Last available NAIP: 2022 (CA), 2022 (OR), 2019 (WA)
    ca_diff = maxdiff.filterDate(f"{2003 + 1}", f"{2022 - 5}").mosaic().clip(california)
    or_diff = maxdiff.filterDate(f"{2004 + 1}", f"{2022 - 5}").mosaic().clip(oregon)
    wa_diff = maxdiff.filterDate(f"{2006 + 1}", f"{2019 - 5}").mosaic().clip(washington)

    img = ee.ImageCollection([ca_diff, or_diff, wa_diff]).mosaic()
    strata = img.select("SWIR2").gt(1500).rename("strata")
    img = img.addBands(strata)

    # Allocate samples based on the SWIR2 change strata
    samples = img.stratifiedSample(
        numPoints=300,
        classBand="strata",
        region=study_fires,
        scale=30,
        seed=0,
        geometries=True,
    )

    # Shuffle so that strata aren't in order, then assign a sequential ID
    samples = samples.toList(samples.size()).shuffle(42)
    samples = ee.FeatureCollection(
        ee.List.sequence(0, samples.size().subtract(1)).map(
            lambda i: ee.Feature(samples.get(i)).set({"id": i})
        )
    )

    task = ee.batch.Export.table.toAsset(
        collection=samples,
        description="validation_plots",
        assetId=VALIDATION_PLOTS + "_v2",
    )
    task.start()


if __name__ == "__main__":
    ee.Initialize()

    print("Exporting validation plots...")
    export_validation_plots()

    print("Exporting ownership map...")
    export_ownership_map()

    print("Exporting severity maps...")
    export_severity_maps()

    print(
        "Exports started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
