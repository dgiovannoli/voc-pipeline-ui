import os
import json
from typing import Optional, Tuple

_API_BASE = "https://api.nal.usda.gov/fdc/v1"

# Map FDC nutrient numbers to our keys
# 203 Protein (g), 204 Fat (g), 205 Carbohydrate (g), 291 Fiber (g), 208 Energy (kcal)
NUTRIENT_NUMBER_TO_KEY = {
    203: "protein",
    204: "fat",
    205: "carbs",
    291: "fiber",
    208: "calories",
}

# Prefer data types with standardized per-100g values
PREFERRED_DATA_TYPES = ["Foundation", "SR Legacy", "Branded"]


def _safe_requests_get(url: str, params: dict, timeout: int = 10):
    try:
        import requests  # local import to avoid hard dependency during tests
    except Exception:
        return None
    try:
        resp = requests.get(url, params=params, timeout=timeout)
        if resp.status_code == 200:
            return resp
        return None
    except Exception:
        return None


def search_food_best_match(query: str) -> Optional[dict]:
    api_key = os.getenv("USDA_API_KEY") or os.getenv("FDC_API_KEY")
    if not api_key:
        return None
    url = f"{_API_BASE}/foods/search"
    params = {"api_key": api_key, "query": query, "pageSize": 5}
    resp = _safe_requests_get(url, params)
    if not resp:
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    foods = data.get("foods") or []
    if not foods:
        return None
    # Prefer by dataType order
    foods.sort(key=lambda f: (PREFERRED_DATA_TYPES.index(f.get("dataType", "Branded")) if f.get("dataType") in PREFERRED_DATA_TYPES else 999))
    return foods[0]


def _extract_macros_from_food(food: dict) -> Optional[Tuple[float, float, float, float, float]]:
    nutrients = food.get("foodNutrients") or []
    values = {"protein": None, "carbs": None, "fat": None, "fiber": None, "calories": None}
    for n in nutrients:
        try:
            num = int(n.get("nutrientNumber")) if n.get("nutrientNumber") is not None else None
        except Exception:
            num = None
        key = NUTRIENT_NUMBER_TO_KEY.get(num)
        if key:
            amount = n.get("value") or n.get("amount")
            unit = (n.get("unitName") or "").upper()
            # We expect grams for macros and KCAL for energy
            if key == "calories":
                if amount is not None and unit in {"KCAL", "KILOCALORIES", "KCALORIES", "KCALORIE"}:
                    values[key] = float(amount)
            else:
                if amount is not None and unit in {"G", "GRAM", "GRAMS"}:
                    values[key] = float(amount)
    if any(values[k] is None for k in values):
        return None
    # These values are typically per 100g for SR/Foundation; for Branded may be per serving.
    # We assume per 100g for preferred data types; callers should prefer those.
    return (
        round(values["protein"], 1),
        round(values["carbs"], 1),
        round(values["fat"], 1),
        round(values["fiber"], 1),
        round(values["calories"], 0),
    )


def get_macros_per_100g(food_name: str) -> Optional[Tuple[float, float, float, float, float]]:
    """
    Returns per-100g macros for the best USDA match, or None if unavailable.
    """
    best = search_food_best_match(food_name)
    if not best:
        return None
    macros = _extract_macros_from_food(best)
    return macros 