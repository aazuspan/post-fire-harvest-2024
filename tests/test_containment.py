import ee

from pfh import containment


def test_get_containment_date():
    """Run containment date for a pre- and post-MODIS test fire. Note this just tests
    functionality, not accuracy."""
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")

    # Pre-MODIS
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "OR4236212395219870830")).first()
    assert containment.get_containment_date(fire).millis().getInfo() == 561407083475

    # Post-MODIS
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "CA4099512207820120818")).first()
    assert containment.get_containment_date(fire).millis().getInfo() == 1346889600000
