import streamlit as st
import pandas as pd
import random

# ---------------- Load Meals Dataset ----------------
@st.cache_data
def load_meals():
    df = pd.read_csv(r"C:\Users\alvit\OneDrive\Documents\Streamlit\indian_women_meals_600_cleaned.csv")
    # Normalize column names: lowercase, remove spaces
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

meals_df = load_meals()

# ---------------- BMR & TDEE Calculation ----------------
def calculate_bmr_tdee(age, weight, height, activity):
    bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    activity_multipliers = {
        "Sedentary": 1.2,
        "Light": 1.375,
        "Moderate": 1.55,
        "Active": 1.725,
        "Very Active": 1.9,
    }
    tdee = bmr * activity_multipliers[activity]
    return round(bmr), round(tdee)

# ---------------- Calorie Target ----------------
def get_target_calories(tdee, goal):
    if goal == "Weight Loss":
        return tdee - 500
    elif goal == "Muscle Gain":
        return tdee + 300
    return tdee  # Toning / Maintenance

# ---------------- Single Day Meal Selection ----------------
def select_meals_for_day(day, target_calories, diet, goal):
    meal_distribution = {"Breakfast": 0.25, "Lunch": 0.35, "Dinner": 0.30, "Snack": 0.10}
    meal_type_map = {
        "Weight Loss": "Deficit",
        "Toning": "Balanced",
        "Maintenance": "Balanced",
        "Muscle Gain": "Surplus",
    }

    selected_meals = {}
    total_nutrition = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0, "fiber": 0}

    for meal_time, fraction in meal_distribution.items():
        target_meal_calories = target_calories * fraction

        # Filter meals
        available = meals_df[
            (meals_df["meal_time"].str.capitalize() == meal_time)
            & (meals_df["diet_type"].str.lower() == diet.lower())
        ]

        preferred = available[available["meal_type"] == meal_type_map[goal]]
        if preferred.empty:
            preferred = available
        if preferred.empty:
            continue

        # Pick closest meal to target calories
        preferred["diff"] = (preferred["calories"] - target_meal_calories).abs()
        top_choices = preferred.sort_values("diff").head(3)
        selected = top_choices.sample(1, random_state=day).iloc[0]

        selected_meals[meal_time] = selected.to_dict()

        # Update nutrition totals
        total_nutrition["calories"] += selected["calories"]
        total_nutrition["protein"] += selected["protein"]
        total_nutrition["carbs"] += selected["carbs"]
        total_nutrition["fats"] += selected["fats"]
        total_nutrition["fiber"] += selected.get("fiber", 0)

    return selected_meals, total_nutrition

# ---------------- Full 30-Day Plan ----------------
def generate_plan(days, target_calories, diet, goal):
    plan = []
    for day in range(1, days + 1):
        meals, nutrition = select_meals_for_day(day, target_calories, diet, goal)
        plan.append({"day": day, "meals": meals, "nutrition": nutrition})
    return plan

# ---------------- Streamlit UI ----------------
st.title("🍲 Aarogyam – 30-Day Meal Plan Generator for Women")
st.write("Personalized Indian meal plans for 30 days")

with st.sidebar:
    st.header("👤 User Profile")
    name = st.text_input("Name", "Anjali")
    age = st.number_input("Age", 20, 70, 28)
    weight = st.number_input("Weight (kg)", 40, 100, 58)
    height = st.number_input("Height (cm)", 140, 180, 162)
    activity = st.selectbox("Activity Level", ["Sedentary", "Light", "Moderate", "Active", "Very Active"])
    goal = st.selectbox("Goal", ["Weight Loss", "Maintenance", "Toning", "Muscle Gain"])
    diet = st.radio("Diet Preference", ["Vegetarian", "Non-Vegetarian"])
    generate = st.button("Generate 30-Day Plan")

if generate:
    bmr, tdee = calculate_bmr_tdee(age, weight, height, activity)
    target_calories = get_target_calories(tdee, goal)

    st.subheader(f"📊 Daily Targets for {name}")
    st.write(f"*BMR:* {bmr} cal | *TDEE:* {tdee} cal | *Target:* {target_calories} cal/day")

    plan = generate_plan(30, target_calories, diet, goal)

    selected_day = st.slider("Select Day", 1, 30, 1)
    day_plan = plan[selected_day - 1]

    st.subheader(f"🥗 Day {selected_day} Plan")
    for meal_time, meal in day_plan["meals"].items():
        st.markdown(f"{meal_time} ({meal['calories']} cal): **{meal['meal_name']}**")

    st.markdown("### Nutrition Summary")
    st.write(day_plan["nutrition"])

    # Export option
    df_export = pd.DataFrame(plan)
    st.download_button(
        "⬇ Download Full Plan (CSV)",
        df_export.to_csv(index=False),
        "meal_plan.csv",
        "text/csv"
    )
