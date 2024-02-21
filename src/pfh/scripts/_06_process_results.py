import ee

from pfh.scripts.config import (
    HARVEST_COLLECTION,
    MAXDIFF_COLLECTION,
    OWNER_CLASSES,
    OWNERSHIP_MAP,
    SEVERITY_COLLECTION,
    STUDY_AREA_COLLECTION,
    STUDY_FIRE_COLLECTION,
)
from pfh.utils import calculate_patch_areas, get_fire_year, get_pixel_area

ee.Initialize()


SEVERITY_CLASSES = ee.Dictionary({"Very low": 0, "Low": 1, "Moderate": 2, "High": 3})


# Pixel values corresponding to each harvest year in the harvest maps
TIMINGS = ee.List([1, 2, 3, 4, 5])
HARVEST = ee.ImageCollection(HARVEST_COLLECTION)
SEVERITY = ee.ImageCollection(SEVERITY_COLLECTION)
STUDY_FIRES = ee.FeatureCollection(STUDY_FIRE_COLLECTION)
STUDY_AREA = ee.FeatureCollection(STUDY_AREA_COLLECTION)
OWNERSHIP = ee.Image(OWNERSHIP_MAP)
MAXDIFF = ee.ImageCollection(MAXDIFF_COLLECTION)
STUDY_FIRE_YEARS = (
    STUDY_FIRES.toList(STUDY_FIRES.size()).map(get_fire_year).distinct().sort()
)
# Burned, unmasked forest pixels used in analysis
ANALYSIS_MASK = MAXDIFF.select("SWIR2").mosaic().mask()

# Exclude wilderness and NPS from ownership analysis
ANALYSIS_OWNERS = {
    k: v for k, v in OWNER_CLASSES.items() if k not in ["wilderness", "nps"]
}

OWNERS = ee.ImageCollection([
    OWNERSHIP.eq(val).set("owner", name) for name, val in ANALYSIS_OWNERS.items()
])


def calculate_stratified_area(
    harvest_mask: ee.Image,
    fire: ee.Feature,
    owner_mask: ee.Image,
    timing: ee.Number,
    severity: ee.String,
) -> ee.Feature:
    """Given a single annual image of harvest timing, a fire feature, an ownership mask,
    a timing year, and a severity class name, calculate the total area and harvested
    area in the region for that strata.
    """
    ecoregion = fire.get("ecoregion")
    state = fire.get("state")
    event_id = fire.get("Event_ID")
    year = fire.get("year")
    owner_name = owner_mask.get("owner")

    year_severity = SEVERITY.filterDate(
        ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31)
    ).first()

    # Build strata masks
    timing_mask = harvest_mask.eq(ee.Image.constant(timing))
    severity_mask = year_severity.eq(SEVERITY_CLASSES.getNumber(severity))

    analysis_mask = (
        harvest_mask.mask()
        .clip(fire.geometry())
        .updateMask(owner_mask)
        .updateMask(severity_mask)
    )
    harvest_mask = analysis_mask.updateMask(timing_mask)

    # Area for all analysis pixels in the region (i.e. burned forest pixels)
    analysis_area = get_pixel_area(analysis_mask, fire, unit="ha")
    # Area for all harvested pixels in the region
    harvest_area = get_pixel_area(harvest_mask, fire, unit="ha")

    metadata = ee.Dictionary({
        "event_id": event_id,
        "year": year,
        "ecoregion": ecoregion,
        "state": state,
        "owner": owner_name,
        "timing": timing,
        "severity": severity,
        "analysis_area": analysis_area,
        "harvest_area": harvest_area,
    })

    return ee.Feature(None, metadata)


def area_by_fire(harvest_mask: ee.Image):
    """Calculate harvested and total area for a given annual image by ecoregion."""
    year = harvest_mask.get("year")
    year_fires = STUDY_FIRES.filter(ee.Filter.eq("year", year))

    return ee.FeatureCollection(
        year_fires.map(lambda fire: area_by_ownership(harvest_mask, fire))
    ).flatten()


def area_by_ownership(harvest_mask: ee.Image, fire: ee.Feature):
    """Calculate harvested and total area for a given image by ownership in a given
    fire.
    """
    return ee.FeatureCollection(
        OWNERS.map(lambda owner: area_by_timing(harvest_mask, fire, owner))
    ).flatten()


def area_by_timing(harvest_mask: ee.Image, fire: ee.Feature, owner_mask: ee.Image):
    """Calculate harvested and total area for a given image by timing year in a given
    fire and ownership.
    """
    return ee.FeatureCollection(
        TIMINGS.map(
            lambda timing: area_by_severity(harvest_mask, fire, owner_mask, timing)
        )
    ).flatten()


def area_by_severity(
    harvest_mask: ee.Image, fire: ee.Feature, owner_mask: ee.Image, timing: ee.Number
):
    """Calculate harvested and total area for a given image by severity class in a given
    fire, ownership, and timing.
    """
    return ee.FeatureCollection(
        SEVERITY_CLASSES.keys().map(
            lambda severity: calculate_stratified_area(
                harvest_mask, fire, owner_mask, timing, severity
            )
        )
    )


def export_stratified_results():
    """Iterate over every combination of:

        1. Year
        2. Fire
        3. Ownership
        4. Timing year
        5. Severity class

    Calculate analysis area and harvested area in each strata.
    """
    results = ee.FeatureCollection(HARVEST.map(area_by_fire)).flatten()

    ee.batch.Export.table.toDrive(
        collection=results,
        description="stratified_results",
        folder="pfh",
        fileFormat="CSV",
    ).start()


def export_patch_areas():
    """Get patch areas by fire and owner.

    Owner classes are assigned based on config.OWNER_CLASSES, with a special class (99)
    for all owners combined.
    """

    def get_fire_patch_areas(
        fire: ee.Feature, by_owner: bool = False
    ) -> ee.FeatureCollection:
        """Get patch areas for a single fire.

        Parameters
        ----------
        by_owner : bool
            If True, return patch areas for each ownership class. If False, return
            patch areas for all ownership classes combined.
        """
        fire_year = get_fire_year(fire)
        fire_metadata = {
            "event_id": fire.get("Event_ID"),
            "year": fire.get("year"),
        }

        harvest_mask = (
            HARVEST.filter(ee.Filter.eq("year", fire_year))
            .first()
            .gt(0)
            .clip(fire.geometry())
            .rename("harvest")
        )

        if by_owner:
            harvest_ownership = harvest_mask.multiply(OWNERSHIP)
        else:
            # Assign an arbitrary class value to represent "all" owners
            harvest_ownership = harvest_mask.multiply(99)

        patch_areas = calculate_patch_areas(
            harvest_ownership,
            classes=list(ANALYSIS_OWNERS.values()) if by_owner else [99],
            geometry=fire.geometry(),
            scale=30,
            crs="EPSG:5070",
            retain_geometry=False,
        )

        return patch_areas.map(lambda f: f.set(fire_metadata))

    metrics_owner = STUDY_FIRES.map(
        lambda f: get_fire_patch_areas(f, by_owner=True)
    ).flatten()
    metrics_all = STUDY_FIRES.map(
        lambda f: get_fire_patch_areas(f, by_owner=False)
    ).flatten()

    metrics = metrics_owner.merge(metrics_all)

    ee.batch.Export.table.toDrive(
        collection=metrics,
        description="patch_metrics",
        folder="pfh",
        fileFormat="CSV",
    ).start()


if __name__ == "__main__":
    print("Exporting stratified harvest results...")
    export_stratified_results()

    print("Exporting patch metrics...")
    export_patch_areas()

    print(
        "Export started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
