from typing import Any

import ee

from pfh import containment, landsat, spectral, utils

LandsatPair = dict[str, Any]
PostfireLandsatPairs = list[LandsatPair]


def pair_difference(pair: LandsatPair) -> ee.Image:
    """Calculate spectral differences between a pair of images."""
    pre = pair["start"]
    post = pair["end"]

    return post.subtract(pre)


def max_difference(
    pairs: PostfireLandsatPairs, *, timing_band: str = "SWIR2"
) -> ee.Image:
    """Calculate the maximum spectral difference between all pairs of images. Use the
    timing_band to determine when the largest spectral change occurred.
    """
    diffs = [pair_difference(pair) for pair in pairs]
    for i, diff in enumerate(diffs):
        diffs[i] = diff.addBands(ee.Image.constant(i).rename("year").int())

    diffs = ee.ImageCollection(diffs)
    bands = diffs.first().bandNames().removeAll([timing_band, "year"])

    return ee.Image.cat([
        diffs.select([timing_band, "year"])
        .reduce(ee.Reducer.max(numInputs=2))
        .rename([timing_band, "year_of_max"]),
        diffs.select(bands).reduce(ee.Reducer.max()).rename(bands),
    ]).int()


def match_pairs(
    pairs: PostfireLandsatPairs,
    *,
    bands: ee.List | None = None,
    percentile: int = 10,
    method: str = "sed",
    geometry: ee.Geometry | None = None,
) -> PostfireLandsatPairs:
    """Apply PIF matching to all pairs of images, returning a new set of pairs.

    Parameters
    ----------
    pairs: List[LandsatPairs]
        The pairs to match.
    bands : ee.List, optional
        The bands to match. If none is given, all source bands are used.
    percentile : int, optional
        The percentile (0-100) of spectral distance to use as a threshold for change
        detection.
    method : str, optional
        The method to use for spectral distance (see ee.Image.spectralDistance).
    geometry : ee.Geometry, optional
        The geometry to use for change detection. If none is given, the source image
        geometry is used.

    Returns
    -------
    List[LandsatPairs]
        The original pairs with the start image replaced with a matched image.
    """
    matched_pairs = []

    for pair in pairs:
        matched_pair = {**pair}
        matched_pair["start"] = spectral.pif_match(
            source=matched_pair["start"],
            target=matched_pair["end"],
            bands=bands,
            percentile=percentile,
            method=method,
            geometry=geometry,
        )
        matched_pair["end"] = matched_pair["end"].select(
            matched_pair["start"].bandNames()
        )
        matched_pairs.append(matched_pair)

    return matched_pairs


def get_landsat_composites(
    fire: ee.Feature, *, years: int = 5, mask_forest: bool = True
) -> PostfireLandsatPairs:
    """Build a list of Landsat pairs over n post-fire years for a single MTBS fire."""
    start_date = ee.Date(fire.get("Ig_Date"))

    last_burned = containment.get_containment_date(fire)
    # Grab up to 2 months after the last burned date
    end_date = utils.earlier_date(
        last_burned.advance(2, "month"),
        ee.Date.fromYMD(start_date.get("year"), 11, 15),
    )
    # Prevent last burned date from ocurring after the end of the date window
    # (effectively creating a 1 second date range and preventing any pixel coverage),
    # and offset by 1 day and 1 second to avoid empty date ranges
    last_burned = utils.earlier_date(
        last_burned, end_date.advance(-1, "second").advance(-1, "day")
    )

    forest_mask = utils.generate_forest_mask(fire)
    reburn_mask = utils.generate_reburn_mask(fire, years=years)
    keep_mask = forest_mask.And(reburn_mask.Not()) if mask_forest else reburn_mask.Not()

    imgs = (
        landsat.load_landsat()
        .filterBounds(fire.geometry())
        .map(landsat.quality_mask)
        .map(lambda x: x.updateMask(keep_mask))
    )

    pairs = []
    for i in range(years):
        # First year based on containment date
        if i == 0:
            # Advance last burned day by 1 day to avoid grabbing the last saturated
            # image
            pre_date_range = ee.DateRange(last_burned.advance(1, "day"), end_date)
            post_date_range = ee.DateRange(
                last_burned.advance(1, "day").advance(1, "year"),
                end_date.advance(1, "year"),
            )
        else:
            year = start_date.get("year").add(i)
            pre_date_range = ee.DateRange(
                ee.Date.fromYMD(year, 6, 15), ee.Date.fromYMD(year, 9, 15)
            )
            post_date_range = ee.DateRange(
                ee.Date.fromYMD(year.add(1), 6, 15),
                ee.Date.fromYMD(year.add(1), 9, 15),
            )

        pre = (
            imgs.filterDate(pre_date_range)
            .median()
            .set(
                "system:time_start",
                pre_date_range.start(),
                "system:time_end",
                pre_date_range.end(),
                "num_images",
                imgs.filterDate(pre_date_range).size(),
            )
        )
        post = (
            imgs.filterDate(post_date_range)
            .median()
            .set(
                "system:time_start",
                post_date_range.start(),
                "system:time_end",
                post_date_range.end(),
                "num_images",
                imgs.filterDate(post_date_range).size(),
            )
        )

        pair: LandsatPair = dict(
            start=pre, end=post, year=i, event_id=fire.get("Event_ID")
        )
        pairs.append(pair)

    return pairs
