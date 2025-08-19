from typing import Dict, Tuple

# Macros per 100 grams: (protein_g, carbs_g, fat_g, fiber_g, calories_kcal)
NUTRITION_PER_100G: Dict[str, Tuple[float, float, float, float, float]] = {
    # Proteins
    "grilled chicken": (31.0, 0.0, 3.6, 0.0, 165.0),  # cooked, skinless breast
    "grilled beef": (26.0, 0.0, 10.0, 0.0, 217.0),     # 90% lean ground beef grilled
    "halibut": (27.0, 0.0, 2.5, 0.0, 140.0),          # cooked
    "cod": (23.0, 0.0, 0.9, 0.0, 105.0),              # cooked, Atlantic cod
    "tilapia": (26.0, 0.0, 2.7, 0.0, 129.0),          # cooked

    # Vegetables
    "cucumber slices": (0.7, 3.6, 0.1, 0.5, 15.0),

    # Grains (cooked)
    "white rice": (2.7, 28.0, 0.3, 0.4, 130.0),
}

# Synonyms map user input to canonical keys used in NUTRITION_PER_100G
SYNONYMS: Dict[str, str] = {
    "chicken": "grilled chicken",
    "chicken breast": "grilled chicken",
    "grilled chicken breast": "grilled chicken",
    "beef": "grilled beef",
    "ground beef": "grilled beef",
    "cucumber": "cucumber slices",
    "rice": "white rice",
    "white fish": "cod",  # default species when unspecified
}

DEFAULT_WHITE_FISH: str = "cod"


def canonicalize_food_name(raw_name: str) -> str:
    name = (raw_name or "").strip().lower()
    if name in NUTRITION_PER_100G:
        return name
    if name in SYNONYMS:
        return SYNONYMS[name]
    # Attempt partial matches against synonyms and canonical list
    for key in SYNONYMS:
        if key in name:
            return SYNONYMS[key]
    for key in NUTRITION_PER_100G:
        if key in name:
            return key
    return name  # unknown; will raise on lookup


def lookup_macros(food_name: str, grams: float) -> Tuple[float, float, float, float, float]:
    """
    Return macros for the given food and grams.
    Raises KeyError if the food cannot be resolved to a known item.
    """
    canonical = canonicalize_food_name(food_name)
    if canonical not in NUTRITION_PER_100G:
        raise KeyError(f"Unknown food item: {food_name}")
    protein, carbs, fat, fiber, kcal = NUTRITION_PER_100G[canonical]
    factor = max(0.0, grams) / 100.0
    return (
        round(protein * factor, 1),
        round(carbs * factor, 1),
        round(fat * factor, 1),
        round(fiber * factor, 1),
        round(kcal * factor, 0),
    ) 