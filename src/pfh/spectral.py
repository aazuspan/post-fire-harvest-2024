import ee


def pif_match(
    source: ee.Image,
    target: ee.Image,
    *,
    bands: ee.List | None = None,
    percentile: int = 10,
    method: str = "sed",
    geometry: ee.Geometry | None = None,
) -> ee.Image:
    """Apply pseudo-invariant feature matching to match a source image to a target.

    Parameters
    ----------
    source : ee.Image
        The source image to match.
    target : ee.Image
        The target image to match to.
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
    ee.Image
        The matched image.
    """
    bands = source.bandNames() if bands is None else ee.List(bands)
    geometry = source.geometry() if geometry is None else geometry

    source = source.select(bands)
    target = target.select(bands)

    dist = source.spectralDistance(target, method)
    if method == "sed":
        dist = dist.sqrt()

    threshold = dist.reduceRegion(
        reducer=ee.Reducer.percentile([percentile]),
        geometry=geometry,
        scale=30,
        maxPixels=1e13,
        bestEffort=True,
        tileScale=4,
    )

    # If no valid pixels are sampled, use a threshold of 0. Note that we need to use
    # ee.Algorithms.If instead of ee.Dictionary.get with a default value because the
    # default only works if the key does not exist, not if the value is null.
    threshold = ee.Image.constant(
        ee.Algorithms.If(threshold.get("distance"), threshold.get("distance"), 0)
    )

    pif_mask = dist.lt(threshold)

    def match_band(band: str) -> ee.Image:
        """Match one source band to a target band using linear regression."""
        imgs = ee.Image.cat([
            source.updateMask(pif_mask).select([band]),
            target.updateMask(pif_mask).select([band]),
        ])

        lr = imgs.reduceRegion(
            reducer=ee.Reducer.linearFit(),
            geometry=geometry,
            scale=30,
            maxPixels=1e13,
            bestEffort=True,
            tileScale=4,
        )

        # If no valid pixels are sampled, use a scale of 1 and an offset of 0.
        scale = ee.Image.constant(ee.Algorithms.If(lr.get("scale"), lr.get("scale"), 1))
        offset = ee.Image.constant(
            ee.Algorithms.If(lr.get("offset"), lr.get("offset"), 0)
        )

        return source.select([band]).multiply(scale).add(offset)

    matched = (
        ee.ImageCollection(bands.map(match_band))
        .toBands()
        .rename(bands)
        .cast(source.bandTypes(), source.bandNames())
        .copyProperties(source, source.propertyNames())
        .set("pseudo_invariant_features", pif_mask)
    )

    return ee.Image(matched)


def get_otsu_threshold(
    image: ee.Image, *, band: str | None = None, region: ee.Geometry | None = None
) -> ee.Number:
    """Calculate an Otsu threshold for a single band of an image."""
    band = image.bandNames().getString(0) if band is None else ee.String(band)
    region = image.geometry() if region is None else region

    histogram = (
        image.select([band])
        .reduceRegion(
            reducer=ee.Reducer.histogram(255, 2),
            geometry=region,
            scale=30,
            bestEffort=True,
            tileScale=4,
        )
        .get(band.cat("_histogram"))
    )

    counts = ee.Array(ee.Dictionary(histogram).get("histogram"))
    means = ee.Array(ee.Dictionary(histogram).get("bucketMeans"))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    mean_sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    mean = mean_sum.divide(total)

    indices = ee.List.sequence(1, size)

    def get_bss(i):
        a_counts = counts.slice(0, 0, i)
        a_count = a_counts.reduce(ee.Reducer.sum(), [0]).get([0])
        a_means = means.slice(0, 0, i)
        a_mean = (
            a_means.multiply(a_counts)
            .reduce(ee.Reducer.sum(), [0])
            .get([0])
            .divide(a_count)
        )
        b_count = total.subtract(a_count)
        b_mean = mean_sum.subtract(a_count.multiply(a_mean)).divide(b_count)
        return a_count.multiply(a_mean.subtract(mean).pow(2)).add(
            b_count.multiply(b_mean.subtract(mean).pow(2))
        )

    bss = indices.map(get_bss)
    return means.sort(bss).get([-1])


def snic_cluster(image: ee.Image, cluster_bands: list[str], **snic_kwargs) -> ee.Image:
    """Apply SNIC clustering to an image. Clusters are based on the given bands, but
    applied to all bands.
    """
    cluster_bands = ee.List(cluster_bands)
    all_bands = image.bandNames()
    clusters = ee.Algorithms.Image.Segmentation.SNIC(
        image=image.select(cluster_bands), **snic_kwargs
    ).select("clusters")

    return ee.Image(
        image.addBands(clusters)
        .reduceConnectedComponents(ee.Reducer.median(), "clusters")
        .select(all_bands)
        .copyProperties(image, image.propertyNames())
    )


def classify_harvests(
    image: ee.Image,
    *,
    bands: list[str] | None = None,
    thresholds: list[float] | None = None,
    region: ee.Geometry | None = None,
) -> ee.Image:
    """Classify a single image as harvest or not based on change concensus in the given
    bands. If thresholds are not given, they are calculated using Otsu's method, and a
    region must be given.
    """
    bands = ["SWIR2", "Red"] if bands is None else bands
    bands = ee.List(bands)

    if thresholds is None:
        thresholds = bands.map(
            lambda b: get_otsu_threshold(image, band=b, region=region)
        )

    change = image.select(bands).gt(thresholds)
    consensus = change.reduce(ee.Reducer.bitwiseAnd())
    year_of_harvest = consensus.multiply(image.select("year_of_max").add(1))

    return ee.Image(
        year_of_harvest.rename("salvage_year").copyProperties(
            image, image.propertyNames()
        )
    )
