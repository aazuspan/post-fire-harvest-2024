import ee

from pfh.composites import get_landsat_composites
from pfh.scripts.config import (
    CANDIDATE_FIRE_COLLECTION,
    STUDY_AREA_COLLECTION,
    STUDY_FIRE_COLLECTION,
)
from pfh.utils import calculate_percent_forest


def get_study_fires(
    candidate_fires: ee.FeatureCollection,
    min_percent_forest=70,
    min_ha=1_000,
    max_containment_month=9,
) -> ee.FeatureCollection:
    """Apply filtering to select a subset of study fires from a collection of candidate
    fires. Remove fires with low pixel coverage, low percent forest, or late containment
    dates. Metadata must be calculated for candidate fires prior to filtering.
    """
    min_acres = min_ha * 2.47105

    filt = ee.Filter.And(
        ee.Filter.gt("percent_forest", min_percent_forest),
        ee.Filter.gt("BurnBndAc", min_acres),
    )

    def filter_late_containment_fires(
        f: ee.Feature, max_month=max_containment_month
    ) -> ee.Feature:
        """Filter out fires with late containment dates by returning None."""
        return ee.Algorithms.If(
            ee.Date(f.get("containment_date")).get("month").gt(max_month), None, f
        )

    return (
        candidate_fires.filter(filt)
        .map(filter_late_containment_fires, dropNulls=True)
        .map(lambda f: f.set("year", ee.Date(f.get("Ig_Date")).get("year")))
    )


def get_nearest_ecoregion(fire: ee.Feature) -> ee.String:
    """Identify the nearest ecoregion to each fire centroid.

    This is necessary to account for the fact that some centroids can fall outside of
    an ecoregion.
    """
    study_regions = ee.FeatureCollection(STUDY_AREA_COLLECTION)

    centroid = fire.geometry().centroid()
    ecoregion_dists = study_regions.map(
        lambda r: r.set("distance", r.distance(centroid))
    )
    return ecoregion_dists.sort("distance").first().getString("NA_L3NAME")


def get_nearest_state(fire: ee.Feature) -> ee.String:
    """Identify the nearest state to each fire centroid.

    This is necessary to account for the fact that some centroids can fall outside of
    an state.
    """
    states = ee.FeatureCollection("TIGER/2018/States")
    orcawa = states.filter(ee.Filter.inList("STUSPS", ["OR", "CA", "WA"]))

    centroid = fire.geometry().centroid()
    state_dists = orcawa.map(lambda r: r.set("distance", r.distance(centroid)))
    return state_dists.sort("distance").first().getString("STUSPS")


def get_fire_metadata(fire: ee.Feature) -> ee.Feature:
    """Generate metadata for a single MTBS fire to use for study fire filtering."""
    percent_forest = calculate_percent_forest(fire)
    image_pairs = get_landsat_composites(fire, years=5, mask_forest=False)[0]

    return fire.set({
        "ignition_date": ee.Date(fire.get("Ig_Date")).millis(),
        # We added a day when building the composite, so subtract a day to get the
        # actual date of last hotspot
        "containment_date": (
            ee.Date(image_pairs["start"].get("system:time_start"))
            .advance(-1, "day")
            .millis()
        ),
        "end_date": ee.Date(image_pairs["start"].get("system:time_end")).millis(),
        "percent_forest": percent_forest,
        "ecoregion": get_nearest_ecoregion(fire),
        "state": get_nearest_state(fire),
    })


if __name__ == "__main__":
    ee.Initialize()
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")
    wdpa = ee.FeatureCollection("WCMC/WDPA/current/polygons")
    fee = ee.FeatureCollection("USGS/GAP/PAD-US/v20/fee")
    wilderness = wdpa.filter(ee.Filter.eq("DESIG", "Wilderness"))
    nps = fee.filter(ee.Filter.eq("Mang_Name", "NPS"))

    candidate_fires = mtbs.filter(
        ee.Filter.And(
            ee.Filter.eq("Incid_Type", "Wildfire"),
            ee.Filter.gt("Ig_Date", ee.Date("1986-01-01").millis()),
            ee.Filter.lt("Ig_Date", ee.Date("2018-01-01").millis()),
            ee.Filter.bounds(ee.FeatureCollection(STUDY_AREA_COLLECTION)),
        )
    )

    def remove_unmanaged_ownerships(fire: ee.Feature) -> ee.Feature:
        """Remove wilderness and NPS ownerships from a fire geometry."""
        fire_wilderness = wilderness.filterBounds(fire.geometry()).union().first()
        fire_nps = nps.filterBounds(fire.geometry()).union().first()

        managed_fire_extent = fire.difference(fire_wilderness).difference(fire_nps)

        # If the resulting fire contains less than one 30m pixel, drop it
        return ee.Feature(
            ee.Algorithms.If(
                managed_fire_extent.area().gt(900), managed_fire_extent, None
            )
        )

    # Exclude any unmanaged areas
    candidate_fires = candidate_fires.map(remove_unmanaged_ownerships, dropNulls=True)
    fires_with_metadata = candidate_fires.map(get_fire_metadata)

    # Only exclude late-season fires
    study_fires = get_study_fires(
        fires_with_metadata,
        min_ha=0,
        min_percent_forest=0,
        max_containment_month=9,
    )

    print("Exporting candidate fires...")
    ee.batch.Export.table.toAsset(
        collection=fires_with_metadata,
        description="candidate_fires",
        assetId=CANDIDATE_FIRE_COLLECTION + "_managed",
    ).start()

    print("Exporting study fires...")
    ee.batch.Export.table.toAsset(
        collection=study_fires,
        description="study_fires",
        assetId=STUDY_FIRE_COLLECTION + "_managed",
    ).start()
    print(
        "Export started. Check the Tasks tab in the Code Editor to monitor progress."
        " https://code.earthengine.google.com/tasks"
    )
