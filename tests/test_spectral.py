import ee

from pfh import spectral


def test_otsu_threshold():
    """Test functionality (not accuracy) of Otsu thresholding."""
    aoi = ee.Geometry.Point(-122.45, 37.77).buffer(100)
    assert spectral.get_otsu_threshold(ee.Image.constant(0).clip(aoi)).getInfo() == 0


def test_pif_match():
    """Test functionality (not accuracy) of PIF matching."""
    aoi = ee.Geometry.Point(-122.632141, 38.414862).buffer(100)
    source = ee.Image("LANDSAT/LC08/C02/T1_L2/LC08_044033_20180703")
    target = ee.Image("LANDSAT/LC08/C02/T1_L2/LC08_045033_20180304")

    matched = spectral.pif_match(source, target, bands=["SR_B3"], geometry=aoi)

    assert "pseudo_invariant_features" in matched.propertyNames().getInfo()
    assert matched.bandNames().getInfo() == ["SR_B3"]


def test_snic_cluster():
    """Test functionality (not accuracy) of SNIC clustering."""
    image = ee.Image("LANDSAT/LC08/C02/T1_L2/LC08_044033_20180703").select([
        "SR_B3",
        "SR_B4",
        "SR_B5",
    ])
    cluster = spectral.snic_cluster(image, cluster_bands=["SR_B3"])

    assert "SR_B4" in cluster.bandNames().getInfo()


def test_classify_harvests():
    image = ee.Image("LANDSAT/LC08/C02/T1_L2/LC08_044033_20180703").select([
        "SR_B3",
        "SR_B4",
        "SR_B5",
    ])
    image = image.addBands(ee.Image.constant(0).rename("year_of_max"))
    harvest = spectral.classify_harvests(image, bands=["SR_B3"], thresholds=[1000])

    assert "salvage_year" in harvest.bandNames().getInfo()
