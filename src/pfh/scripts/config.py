ASSET_DIRECTORY = "projects/salvage-2023/assets"


# Manually created assets
STUDY_AREA_COLLECTION = f"{ASSET_DIRECTORY}/study_regions"


# Generated assets
CANDIDATE_FIRE_COLLECTION = f"{ASSET_DIRECTORY}/candidate_fires"
STUDY_FIRE_COLLECTION = f"{ASSET_DIRECTORY}/study_fires"
MAXDIFF_COLLECTION = f"{ASSET_DIRECTORY}/maxdiff"
HARVEST_COLLECTION = f"{ASSET_DIRECTORY}/salvage"
SEVERITY_COLLECTION = f"{ASSET_DIRECTORY}/severity"
VALIDATION_PLOTS = f"{ASSET_DIRECTORY}/validation"
INTERPRETATIONS = f"{ASSET_DIRECTORY}/interpretations"
OWNERSHIP_MAP = f"{ASSET_DIRECTORY}/ownership"
OTSU_THRESHOLDS = f"{ASSET_DIRECTORY}/otsu_thresholds"

SEVERITY_CLASSES = {
    0: "Very low / unburned",
    1: "Low",
    2: "Moderate",
    3: "High",
}

OWNER_CLASSES = {
    "private": 1,
    "usfs": 2,  # Excluding wilderness
    "blm": 3,
    "nps": 4,
    "wilderness": 5,
    "other_fed": 6,  # Not BLM, USFS, or NPS
    "nonfed_public": 7,  # State, local, etc.
    "tribal": 8,
}

# Crosswalk individual owner names to groups
OWNER_GROUPS = {
    "blm": "Federal",
    "usfs": "Federal",
    "other_fed": "Federal",
    "private": "Private",
    "nonfed_public": "Other",
    "tribal": "Other",
    "all": "All owners",
}
