from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import re

from nutrition_db import lookup_macros, canonicalize_food_name, DEFAULT_WHITE_FISH


@dataclass
class MealComponent:
    name: str
    grams: float

    def macros(self) -> Tuple[float, float, float, float, float]:
        return lookup_macros(self.name, self.grams)


@dataclass
class Meal:
    components: List[MealComponent] = field(default_factory=list)

    def total_macros(self) -> Dict[str, float]:
        totals = {"protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0, "calories": 0.0}
        for c in self.components:
            p, cb, f, fi, kcal = c.macros()
            totals["protein"] += p
            totals["carbs"] += cb
            totals["fat"] += f
            totals["fiber"] += fi
            totals["calories"] += kcal
        # round for presentation
        return {k: (round(v, 1) if k != "calories" else round(v, 0)) for k, v in totals.items()}

    def copy(self) -> "Meal":
        return Meal(components=[MealComponent(c.name, c.grams) for c in self.components])

    def find_first_matching(self, predicate) -> Optional[int]:
        for idx, c in enumerate(self.components):
            if predicate(c):
                return idx
        return None


@dataclass
class DailyProgress:
    protein_g: float
    calories_kcal: float

    def apply_delta(self, delta_macros: Dict[str, float]) -> "DailyProgress":
        return DailyProgress(
            protein_g=round(self.protein_g + delta_macros.get("protein", 0.0), 1),
            calories_kcal=round(self.calories_kcal + delta_macros.get("calories", 0.0), 0),
        )


def compute_delta(new_meal: Meal, old_meal: Meal) -> Dict[str, float]:
    old_totals = old_meal.total_macros()
    new_totals = new_meal.total_macros()
    return {k: round(new_totals[k] - old_totals[k], 1 if k != "calories" else 0) for k in new_totals}


def extract_weight_grams(text: str) -> Optional[float]:
    match = re.search(r"(\d+)\s*g\b", text.lower())
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def infer_species(raw_text: str) -> Optional[str]:
    text = raw_text.lower()
    if "halibut" in text:
        return "halibut"
    if "tilapia" in text:
        return "tilapia"
    if "cod" in text:
        return "cod"
    if "white fish" in text or "whitefish" in text:
        return DEFAULT_WHITE_FISH
    return None


def infer_target_component(meal: Meal, raw_text: str) -> Optional[int]:
    text = raw_text.lower()
    # Direct mention
    if "chicken" in text:
        return meal.find_first_matching(lambda c: "chicken" in c.name.lower())
    if "beef" in text:
        return meal.find_first_matching(lambda c: "beef" in c.name.lower())
    # Implicit: if user says "not chicken" and meal contains chicken
    if "not chicken" in text:
        idx = meal.find_first_matching(lambda c: "chicken" in c.name.lower())
        if idx is not None:
            return idx
    # Fallback: if meal has exactly one protein (chicken/beef/fish), choose chicken first
    protein_idx = meal.find_first_matching(lambda c: any(x in c.name.lower() for x in ["chicken", "beef", "halibut", "cod", "tilapia"]))
    return protein_idx


@dataclass
class ProposedEdit:
    target_index: int
    new_name: str
    new_grams: float


def propose_replace_component(user_text: str, meal: Meal) -> Optional[ProposedEdit]:
    idx = infer_target_component(meal, user_text)
    if idx is None:
        return None
    species = infer_species(user_text)
    if species is None:
        # If user rejects chicken but no species given and mentions white fish, default to cod
        if ("white fish" in user_text.lower() or "whitefish" in user_text.lower()):
            species = DEFAULT_WHITE_FISH
    if species is None:
        # If user text says it's not chicken but doesn't specify, we still need confirmation later
        return None

    grams = extract_weight_grams(user_text)
    if grams is None:
        grams = meal.components[idx].grams  # retain original weight by default

    return ProposedEdit(target_index=idx, new_name=species, new_grams=grams)


def apply_replace(meal: Meal, edit: ProposedEdit) -> Meal:
    new_meal = meal.copy()
    target = new_meal.components[edit.target_index]
    new_meal.components[edit.target_index] = MealComponent(name=canonicalize_food_name(edit.new_name), grams=edit.new_grams)
    return new_meal


def render_confirmation(meal: Meal, edit: ProposedEdit) -> str:
    old = meal.components[edit.target_index]
    new_name = canonicalize_food_name(edit.new_name)
    return (
        f"Got it. Replace '{old.name} ({int(old.grams)}g)' with '{new_name} ({int(edit.new_grams)}g)' and keep beef ({int(next((c.grams for c in meal.components if 'beef' in c.name.lower()), 0))}g), cucumber ({int(next((c.grams for c in meal.components if 'cucumber' in c.name.lower()), 0))}g), and rice ({int(next((c.grams for c in meal.components if 'rice' in c.name.lower()), 0))}g) as-is?\n\n"
        "Reply Y to confirm, or specify weight (e.g., 'halibut 120g')."
    )


def render_meal(meal: Meal) -> str:
    lines = ["📋 Meal Components"]
    for c in meal.components:
        lines.append(f"• {c.name} ({int(c.grams)}g)")
    return "\n".join(lines)


def render_macros(meal: Meal, delta: Optional[Dict[str, float]] = None) -> str:
    t = meal.total_macros()
    lines = ["🧮 Estimated Macros",
             f"• Protein: {t['protein']}g" + (f"  (Δ {delta['protein']:+.1f}g)" if delta else ""),
             f"• Carbs: {t['carbs']}g" + (f"  (Δ {delta['carbs']:+.1f}g)" if delta else ""),
             f"• Fat: {t['fat']}g" + (f"  (Δ {delta['fat']:+.1f}g)" if delta else ""),
             f"• Fiber: {t['fiber']}g" + (f"  (Δ {delta['fiber']:+.1f}g)" if delta else ""),
             f"• Calories: {int(t['calories'])} kcal" + (f" (Δ {int(delta['calories']):+d} kcal)" if delta else "")]
    return "\n".join(lines)


def render_progress(progress: DailyProgress) -> str:
    # Progress bar mocked as simple string; in-app you would compute percentage of goal
    return f"📊 Your Progress\n██████████ 100% 🎯 On track! • {progress.protein_g}g protein • {int(progress.calories_kcal)} cal"


def handle_user_message(user_text: str, meal: Meal, progress: DailyProgress) -> Tuple[str, Meal, DailyProgress]:
    """
    Minimal orchestrator to demonstrate improved UX:
    - Propose replace edits when species is specified
    - Confirm and apply on 'Y' or when weight is specified in reply
    - Keep other components intact; recompute macros and update progress by delta only
    """
    # Step 1: Do we have a pending proposed edit? For demo simplicity, propose and require immediate confirmation.
    proposal = propose_replace_component(user_text, meal)
    if proposal is not None:
        return render_confirmation(meal, proposal), meal, progress

    # Step 2: If the user confirms with Y and we can infer last proposal context (not implemented statefully here),
    # support direct commands like "halibut 120g" by parsing species + weight.
    species = infer_species(user_text)
    if species:
        grams = extract_weight_grams(user_text) or meal.find_first_matching(lambda c: "chicken" in c.name.lower())
        if isinstance(grams, int):  # we misused variable; fix by extracting chicken grams
            idx = grams
            grams = meal.components[idx].grams
        idx = infer_target_component(meal, user_text)
        if idx is not None:
            edit = ProposedEdit(target_index=idx, new_name=species, new_grams=grams)
            new_meal = apply_replace(meal, edit)
            delta = compute_delta(new_meal, meal)
            new_progress = progress.apply_delta(delta)
            reply = (
                "Updated meal (chicken → {species}, {grams}g):\n\n".format(species=canonicalize_food_name(species), grams=int(grams))
                + render_meal(new_meal)
                + "\n\n"
                + render_macros(new_meal, delta)
                + "\n\nDaily progress updated by the meal delta.\nType \"Summary\" for your full daily breakdown, or \"edit rice 100g\" to adjust portions."
            )
            return reply, new_meal, new_progress

    # Step 3: Basic acknowledgments
    lower = user_text.lower().strip()
    if lower in {"y", "yes"}:
        # In a real app, we'd apply the last proposal; here we confirm but require explicit species message
        return ("Confirmed. Please specify the item and weight (e.g., 'halibut 100g') to apply.", meal, progress)

    # Fallback: No action
    return ("No changes made. If you want to proceed, say something like 'replace chicken with halibut 100g'.", meal, progress) 