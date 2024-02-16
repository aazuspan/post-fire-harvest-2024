import ee

from pfh.scripts.config import (
    HARVEST_COLLECTION,
    MAXDIFF_COLLECTION,
)


def create_imagecollection(collection_path) -> None:
    """Create an image collection in Earth Engine."""
    print(f"Creating empty collection `{collection_path}`...")

    try:
        ee.data.createAsset({"type": "ImageCollection"}, collection_path)
    except ee.EEException:
        raise Exception(
            f"Collection `{collection_path}` already exists! Change the asset directory"
            " or remove the collection first."
        ) from None


if __name__ == "__main__":
    ee.Initialize()

    create_imagecollection(MAXDIFF_COLLECTION)
    create_imagecollection(HARVEST_COLLECTION)
    # create_imagecollection(SEVERITY_COLLECTION)
