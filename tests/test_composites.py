import ee

from pfh import composites


def test_get_landsat_composites():
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "OR4236212395219870830")).first()
    pairs = composites.get_landsat_composites(fire, years=5)

    assert len(pairs) == 5


def test_maxdiff():
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "OR4236212395219870830")).first()
    pairs = composites.get_landsat_composites(fire, years=5)
    maxdiff = composites.max_difference(pairs)

    assert "year_of_max" in maxdiff.bandNames().getInfo()


def test_match_pairs():
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "OR4236212395219870830")).first()
    pairs = composites.get_landsat_composites(fire, years=3)
    matched = composites.match_pairs(
        pairs, bands=["NIR"], method="sed", geometry=fire.geometry()
    )

    assert len(matched) == 3
    assert matched[0]["start"].bandNames().getInfo() == ["NIR"]
    assert matched[0]["end"].bandNames().getInfo() == ["NIR"]
