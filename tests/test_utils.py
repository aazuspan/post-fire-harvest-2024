import ee
import pytest

from pfh import utils


def test_minimum_date():
    date1 = ee.Date("2019-01-01")
    date2 = ee.Date("2019-01-02")
    assert utils.earlier_date(date1, date2).getInfo() == date1.getInfo()


def test_bit_mask():
    assert utils.bit_mask(ee.Number(16), 4).getInfo() == 1
    assert utils.bit_mask(ee.Number(16), 3).getInfo() == 0


def test_percent_forest():
    mtbs = ee.FeatureCollection("USFS/GTAC/MTBS/burned_area_boundaries/v1")
    fire = mtbs.filter(ee.Filter.eq("Event_ID", "CA3785712008620130817")).first()
    pct_forest = utils.calculate_percent_forest(fire).getInfo()

    assert pct_forest == pytest.approx(89.13, 0.1)
