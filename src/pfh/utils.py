from typing import Literal

import ee

AreaUnit = Literal["ha", "m2", "km2"]
AREA_SCALERS = {"m2": 1, "ha": 1 / 10_000, "km2": 1 / 1_000_000}


def bit_mask(image: ee.Image, bit: ee.Number) -> ee.Image:
    """Return 1 if bit is set, 0 otherwise."""
    return image.rightShift(bit).bitwiseAnd(1).eq(1)


def earlier_date(date1: ee.Date, date2: ee.Date) -> ee.Date:
    """Return the earlier of two dates."""
    min_millis = date1.millis().min(date2.millis())
    return ee.Date(min_millis)


def later_date(date1: ee.Date, date2: ee.Date) -> ee.Date:
    """Return the later of two dates."""
    max_millis = date1.millis().max(date2.millis())
    return ee.Date(max_millis)


def generate_reburn_mask(fire: ee.Feature, *, years: int = 5) -> ee.Image:
    """Build a reburn mask (0=no, 1=reburn) within n years of fire."""
    date = ee.Date(fire.get("Ig_Date"))
    year = ee.Date.fromYMD(date.get("year"), 1, 1)
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")

    reburns = mtbs.filter(
        ee.Filter.And(
            ee.Filter.gt("Ig_Date", date.millis()),
            ee.Filter.lt("Ig_Date", year.advance(years + 1, "year").millis()),
            ee.Filter.intersects(leftValue=fire.geometry(), rightField=".geo"),
        )
    )

    return ee.Image(1).clip(reburns).unmask(0).clip(fire.geometry()).rename("reburn")


def generate_forest_mask(fire: ee.Feature) -> ee.Image:
    """Build a forest mask (0=nonforest, 1=forest) for an MTBS fire feature. Non-forest
    pixels are masked.
    """
    lcms = ee.ImageCollection("USFS/GTAC/LCMS/v2021-7")
    start_date = ee.Date(fire.get("Ig_Date"))

    return (
        lcms
        # Use LULC from prior year to avoid early-season fire effects
        .filterDate(
            ee.Date.fromYMD(start_date.get("year").subtract(1), 1, 1),
            ee.Date.fromYMD(start_date.get("year"), 1, 1),
        )
        .filterBounds(fire.geometry())
        .first()
        .select("Land_Cover")
        .eq(1)
        .clip(fire.geometry())
        .rename("forest")
    )


def calculate_percent_forest(fire: ee.Feature) -> ee.Number:
    forest_mask = generate_forest_mask(fire).clip(fire)
    return (
        forest_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=fire.geometry(),
        )
        .getNumber("forest")
        .multiply(100)
        .clamp(0, 100)
    )


def calculate_severity_metric(dnbr: ee.Image, fire: ee.Feature) -> ee.Number:
    """Calculate the severity metric (Lutz et al., 2011) for a single fire."""
    dnbr = dnbr.rename("dnbr")

    # Calculate an Nx2 array of the pixel count for each dNBR value, where N is the
    # number of bins
    histogram = ee.Array(
        dnbr.reduceRegion(
            reducer=ee.Reducer.fixedHistogram(min=-200, max=1201, steps=1401),
            geometry=fire.geometry(),
            scale=30,
        ).get("dnbr")
    )

    # Calculate the total number of pixels in the fire
    n_pixels = dnbr.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=fire.geometry(),
        scale=30,
    ).getNumber("dnbr")

    def iter_severity_metric(x: ee.List, previous: ee.Dictionary):
        """Iterative one step of severity metric calculation, given a histogram bin
        and the cumulative results from previous iterations.
        """
        previous = ee.Dictionary(previous)
        prev_sum = previous.getNumber("sum")
        prev_count = previous.getNumber("count")

        count = ee.List(x).get(1)

        proportion = prev_count.divide(n_pixels)
        new_sum = prev_sum.add(proportion.divide(1401))
        new_count = prev_count.add(count)

        return ee.Dictionary({"sum": new_sum, "count": new_count})

    # We will iteratively fill this dictionary with the results of each histogram bin
    empty_result = ee.Dictionary({"sum": 0, "count": 0})
    # Calculate the severity metric
    return (
        ee.Dictionary(
            histogram.toList().iterate(
                lambda x, previous: iter_severity_metric(x, previous), empty_result
            )
        )
        .getNumber("sum")
        .multiply(-1)
        .add(1)
    )


def get_pixel_area(
    mask: ee.Image, region: ee.Feature, scale=30, unit: AreaUnit = "ha", **kwargs
) -> ee.Number:
    """Calculate the pixel area within a given mask in a given region."""
    area_scaler = AREA_SCALERS[unit]

    return (
        ee.Image.pixelArea()
        .updateMask(mask)
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=region.geometry(),
            scale=scale,
            maxPixels=1e13,
            **kwargs,
        )
        .getNumber("area")
        .multiply(area_scaler)
    )


def get_fire_year(fire: ee.Feature) -> ee.Number:
    """Get the fire year from a given MTBS fire."""
    return ee.Date(ee.Feature(fire).get("Ig_Date")).get("year")


def calculate_patch_areas(
    image: ee.Image,
    classes: tuple[int, ...] | ee.List,
    geometry: ee.Geometry | None = None,
    crs: str = "EPSG:5070",
    scale: int = 30,
    eight_connected: bool = True,
    max_error: int | ee.Number = 1,
    retain_geometry: bool = False,
) -> ee.FeatureCollection:
    """
    Calculate patch areas from a classified image.

    Parameters
    ---------
    image : ee.Image
        An image containing integer labeled classes. The background class should be
        unmasked with a value of 0.
    classes : tuple[int, ...] | ee.List
        A list of classes to include in the analysis, by value.
    geometry : ee.Geometry, optional
        A geometry to restrict analysis to. Defaults to the image geometry.
    crs : str, optional
        The CRS to use for analysis. Defaults to EPSG:5070.
    scale : int, optional
        The scale to use for analysis, in meters. Defaults to 30.
    eight_connected : bool, optional
        Whether to use 8-connected pixels for analysis. Defaults to True.
    max_error : int | ee.Number, optional
        The maximum error to allow when calculating patch areas. Defaults to 1.
    retain_geometry : bool, optional
        Whether to retain the geometry of patches in the output collection. Defaults to
        False.

    Returns
    -------
    ee.FeatureCollection
        A feature collection of patches containing class labels and areas.
    """
    geometry = geometry or image.geometry()

    patches = image.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=geometry,
        crs=crs,
        scale=scale,
        eightConnected=eight_connected,
        maxPixels=1e13,
    ).filter(ee.Filter.inList("label", classes))

    def set_patch_area(patch: ee.Feature) -> ee.Feature:
        """Calculate the area of a patch in hectares and append as a property."""
        return patch.set({"area": patch.geometry().area(max_error).divide(1e4)})

    patch_areas = patches.map(set_patch_area)
    return patch_areas.select(["label", "area"], retainGeometry=retain_geometry)
