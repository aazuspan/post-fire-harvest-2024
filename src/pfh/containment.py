import ee

from pfh.landsat import load_landsat
from pfh.utils import bit_mask, earlier_date, later_date


def get_modis_hotspots(image: ee.Image) -> ee.Image:
    """Get a hotspot date mask from a MOD14A1 or MYD14A1 image."""
    # Low, moderate, or high confidence fire classes
    fire_classes = ee.Image.constant([7, 8, 9])
    hotspots = image.select("FireMask").eq(fire_classes).reduce(ee.Reducer.sum()).gt(0)

    return hotspots.multiply(image.date().millis()).rename("hotspot_date").long()


def get_landsat_hotspots(image: ee.Image) -> ee.Image:
    """Get a hotspot date mask from a Landsat Collection 2 image. This is based on
    saturation of the SWIR2 band, excluding pixels with aerosol saturation that
    can occur due to dense cloud cover.
    """
    qa = image.select("QA_RADSAT")
    saturated_swir2 = bit_mask(qa, 6)
    unsaturated_aerosol = bit_mask(qa, 0).eq(0)

    return (
        saturated_swir2.And(unsaturated_aerosol)
        .multiply(image.date().millis())
        .rename("hotspot_date")
        .long()
    )


def get_containment_date(fire: ee.Feature) -> ee.Date:
    """Estimate containment date (more accurately, date of last detected hotspot) for an
    MTBS fire (USFS/GTAC/MTBS/burned_area_boundaries/v1).
    """

    def get_last_hotspot_date(collection: ee.ImageCollection, fn: callable) -> ee.Date:
        """Get the date of the last hotspot in a collection."""
        hotspot_dates = (
            collection.filterBounds(fire.geometry())
            .filterDate(start_date, end_date)
            .map(fn)
        )

        last_hotspot = ee.Image(
            ee.Algorithms.If(
                # Unmasking will fail if there are no images
                hotspot_dates.size().eq(0),
                ee.Image(0).rename("hotspot_date"),
                # hotspot_date will be null if there are no valid pixels, so fill with 0
                hotspot_dates.max().unmask(0),
            )
        )

        last_millis = last_hotspot.reduceRegion(
            reducer=ee.Reducer.max(),
            geometry=fire.geometry(),
            scale=30,
            tileScale=4,
        ).getNumber("hotspot_date")

        # If no hotspots are detected, return the end date as a "null" value
        return ee.Date(ee.Algorithms.If(last_millis.eq(0), end_date, last_millis))

    start_date = ee.Date(fire.get("Ig_Date"))
    year = start_date.get("year")
    # If the ignition date is after the cutoff, use an empty date range
    end_date = later_date(
        start_date.advance(1, "second"), ee.Date.fromYMD(year, 11, 15)
    )

    landsat = load_landsat()
    modis = ee.ImageCollection("MODIS/006/MOD14A1").merge(
        ee.ImageCollection("MODIS/006/MYD14A1")
    )

    landsat_containment = get_last_hotspot_date(landsat, get_landsat_hotspots)
    modis_containment = get_last_hotspot_date(modis, get_modis_hotspots)

    # Take the earliest containment date from MODIS and Landsat if available, otherwise
    # use Landsat. Using the earliest date reduces false positives from both sources.
    containment = ee.Date(
        ee.Algorithms.If(
            year.lt(2000),
            landsat_containment,
            earlier_date(landsat_containment, modis_containment),
        )
    )

    # If no hotspots are detected, they defaulted to end date. In that case, use the
    # start date + 10 days. This most commonly occurs with pre-MODIS fires that were
    # contained before the first Landsat acquisition.
    return ee.Date(
        ee.Algorithms.If(
            containment.millis().eq(end_date.millis()),
            start_date.advance(10, "day"),
            containment,
        )
    )
