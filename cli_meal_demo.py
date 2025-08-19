from meal_editor import Meal, MealComponent, DailyProgress, handle_user_message, propose_replace_component, apply_replace, compute_delta, render_meal, render_macros, render_progress, render_confirmation


def build_initial_meal() -> Meal:
    return Meal(components=[
        MealComponent("grilled chicken", 100),
        MealComponent("grilled beef", 80),
        MealComponent("cucumber slices", 50),
        MealComponent("white rice", 150),
    ])


def simulate_sequence():
    meal = build_initial_meal()
    progress = DailyProgress(protein_g=320.4, calories_kcal=7839)

    print("Initial meal:")
    print(render_meal(meal))
    print(render_macros(meal))
    print(render_progress(progress))
    print("\n---\n")

    # User: It's not chicken, it's halibut
    user = "It's not chicken, it's halibut"
    reply, meal, progress = handle_user_message(user, meal, progress)
    print("User:", user)
    print("Assistant:\n" + reply)

    # Simulate confirmation
    proposal = propose_replace_component(user, meal)
    if proposal:
        print("\nConfirming with 'Y'...")
        # Apply proposed edit
        new_meal = apply_replace(meal, proposal)
        delta = compute_delta(new_meal, meal)
        progress = progress.apply_delta(delta)
        meal = new_meal
        print(render_meal(meal))
        print(render_macros(meal, delta))
        print(render_progress(progress))

    print("\n---\n")

    # User: Change the chicken to white fish (no weight -> keep 100g; default to cod)
    meal = build_initial_meal()  # reset to initial to show scenario 2 independently
    user = "Change the chicken to white fish"
    reply, meal_after, progress2 = handle_user_message(user, meal, progress)
    print("User:", user)
    print("Assistant:\n" + reply)

    # Provide explicit weight follow-up
    followup = "white fish 100g"
    reply, meal_after, progress2 = handle_user_message(followup, meal, progress)
    print("User:", followup)
    print("Assistant:\n" + reply)


if __name__ == "__main__":
    simulate_sequence() 