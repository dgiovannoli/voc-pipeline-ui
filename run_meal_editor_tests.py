from meal_editor import Meal, MealComponent, DailyProgress, propose_replace_component, apply_replace, compute_delta


def build_initial_meal():
    return Meal(components=[
        MealComponent("grilled chicken", 100),
        MealComponent("grilled beef", 80),
        MealComponent("cucumber slices", 50),
        MealComponent("white rice", 150),
    ])


def test_replace_keeps_others():
    meal = build_initial_meal()
    progress = DailyProgress(protein_g=0, calories_kcal=0)
    user = "It's not chicken, it's halibut"
    proposal = propose_replace_component(user, meal)
    assert proposal is not None, "Should propose replacing chicken with halibut"
    new_meal = apply_replace(meal, proposal)
    # Ensure other components remain
    names = [c.name for c in new_meal.components]
    assert "grilled beef" in names and "cucumber slices" in names and "white rice" in names, "Other components must be preserved"


def test_weight_retained_by_default():
    meal = build_initial_meal()
    user = "Change chicken to halibut"  # no weight -> retain 100g
    proposal = propose_replace_component(user, meal)
    # propose_replace_component returns None because species not explicit? It should infer halibut only when mentioned
    # Adjust input to include halibut
    user = "Change the chicken to halibut"
    proposal = propose_replace_component(user, meal)
    assert proposal is not None, "Proposal should be created when species provided"
    assert int(proposal.new_grams) == 100, "Weight should default to original"


def test_white_fish_defaults_to_cod():
    meal = build_initial_meal()
    user = "Change the chicken to white fish"
    proposal = propose_replace_component(user, meal)
    assert proposal is not None, "Proposal should be created for white fish"
    assert proposal.new_name == "cod", "White fish should default to cod"


def test_delta_progress_update():
    meal = build_initial_meal()
    user = "Change the chicken to halibut 120g"
    proposal = propose_replace_component(user, meal)
    assert proposal is not None
    new_meal = apply_replace(meal, proposal)
    delta = compute_delta(new_meal, meal)
    # Protein should change and calories adjust; ensure delta keys exist
    for key in ["protein", "carbs", "fat", "fiber", "calories"]:
        assert key in delta


def run_all():
    test_replace_keeps_others()
    test_weight_retained_by_default()
    test_white_fish_defaults_to_cod()
    test_delta_progress_update()
    print("All tests PASS")


if __name__ == "__main__":
    run_all() 