import ee

from pfh import utils


def prep_OLI(image: ee.Image) -> ee.Image:
    """Prepare an OLI image for analysis."""
    return image.select(
        [
            "SR_B2",
            "SR_B3",
            "SR_B4",
            "SR_B5",
            "SR_B6",
            "SR_B7",
            "ST_B10",
            "QA_PIXEL",
            "QA_RADSAT",
        ],
        [
            "Blue",
            "Green",
            "Red",
            "NIR",
            "SWIR1",
            "SWIR2",
            "TIR",
            "QA_PIXEL",
            "QA_RADSAT",
        ],
    ).uint16()


def prep_ETM(image: ee.Image) -> ee.Image:
    """Prepare an ETM image for analysis."""
    return image.select(
        [
            "SR_B1",
            "SR_B2",
            "SR_B3",
            "SR_B4",
            "SR_B5",
            "SR_B7",
            "ST_B6",
            "QA_PIXEL",
            "QA_RADSAT",
        ],
        [
            "Blue",
            "Green",
            "Red",
            "NIR",
            "SWIR1",
            "SWIR2",
            "TIR",
            "QA_PIXEL",
            "QA_RADSAT",
        ],
    ).uint16()


def load_landsat() -> ee.ImageCollection:
    oliL9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2").map(prep_OLI)
    oliL8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").map(prep_OLI)
    etm = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2").map(prep_ETM)
    tm = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").map(prep_ETM)

    return tm.merge(etm).merge(oliL8).merge(oliL9).sort("system:time_start")


def quality_mask(image: ee.Image) -> ee.Image:
    """Apply quality masking to a Landsat Collection 2 Image."""
    qa = image.select("QA_PIXEL")
    cirrus = utils.bit_mask(qa, 2)
    cloud_shadow = utils.bit_mask(qa, 4)
    snow = utils.bit_mask(qa, 5)
    clear = utils.bit_mask(qa, 6)
    saturated = image.select("QA_RADSAT").gt(0)

    return image.updateMask(
        clear.And(snow.eq(0))
        .And(cirrus.eq(0))
        .And(cloud_shadow.eq(0))
        .And(saturated.eq(0))
    )
