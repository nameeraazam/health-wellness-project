import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime
from pydantic import BaseModel, ValidationError
from typing import List

genai.configure(api_key="AIzaSyBXueFVZnofGYMHzTZBnbSFn2kjIVm3Omo")


class UserProfile(BaseModel):
    name: str
    age: int
    gender: str
    weight: float
    height: float
    goal: str
    dietary_prefs: str
    fitness_level: str
    injuries: str = ""

class MealDay(BaseModel):
    day: str
    breakfast: str
    lunch: str
    dinner: str
    snacks: str

class WorkoutDay(BaseModel):
    day: str
    exercises: List[str]
    duration: str
    intensity: str


def extract_json(text: str) -> dict:
    """More robust JSON extraction"""
    try:
        try:
            return json.loads(text.strip())
        except:
            pass
        
        match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
                
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
                
        return {}
    except Exception as e:
        st.error(f"JSON extraction error: {str(e)}")
        return {}

def call_gemini(prompt: str, model_name="gemini-1.5-flash") -> str:
    """Call Gemini API with stricter instructions"""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. Do not include any other text.",
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {str(e)}")
        return ""


def generate_meal_plan(profile: UserProfile) -> List[MealDay]:
    """Generate personalized meal plan with daily structure"""
    prompt = f"""
    Create a 7-day meal plan as a JSON array. Each item should represent a day with:
    - "day": String (e.g., "Monday", "Day 1")
    - "breakfast": String description
    - "lunch": String description
    - "dinner": String description
    - "snacks": String description
    
    User profile:
    - Name: {profile.name}
    - Age: {profile.age}
    - Gender: {profile.gender}
    - Weight: {profile.weight} kg
    - Height: {profile.height} cm
    - Goal: {profile.goal}
    - Dietary preferences: {profile.dietary_prefs}
    - Fitness level: {profile.fitness_level}
    
    Make meals realistic, varied, and aligned with the user's goals.
    """
    
    response = call_gemini(prompt)
    meal_data = extract_json(response)
    
    fallback_plan = [
        MealDay(
            day="Monday",
            breakfast="Oatmeal with fruits",
            lunch="Grilled chicken salad",
            dinner="Salmon with vegetables",
            snacks="Greek yogurt"
        ),
        MealDay(
            day="Tuesday",
            breakfast="Whole grain toast with avocado",
            lunch="Quinoa bowl with vegetables",
            dinner="Vegetable stir-fry with tofu",
            snacks="Mixed nuts"
        )
    ]
    
    if not isinstance(meal_data, list):
        st.warning("Invalid meal plan format. Using default plan.")
        return fallback_plan
    
    valid_days = []
    for day_data in meal_data:
        try:
            if not all(key in day_data for key in ["day", "breakfast", "lunch", "dinner", "snacks"]):
                continue
                
            valid_days.append(MealDay(**day_data))
        except ValidationError:
            continue
    
    return valid_days if valid_days else fallback_plan

def generate_workout_plan(profile: UserProfile) -> List[WorkoutDay]:
    """Generate personalized workout plan"""
    prompt = f"""
    Create a 7-day workout plan as a JSON array. Each item should be an object with:
    - "day": String (e.g., "Monday", "Day 1")
    - "exercises": Array of strings
    - "duration": String (e.g., "45 minutes")
    - "intensity": String (e.g., "Moderate")
    
    User profile:
    - Name: {profile.name}
    - Age: {profile.age}
    - Gender: {profile.gender}
    - Weight: {profile.weight} kg
    - Height: {profile.height} cm
    - Goal: {profile.goal}
    - Fitness level: {profile.fitness_level}
    - Injuries: {profile.injuries if profile.injuries else 'None'}
    
    Make it safe and progressive.
    """
    
    response = call_gemini(prompt)
    workout_data = extract_json(response)
    
    fallback_plan = [
        WorkoutDay(
            day="Monday",
            exercises=["Cardio: 30 min jogging", "Strength: Upper body"],
            duration="60 minutes",
            intensity="Moderate"
        ),
        WorkoutDay(
            day="Tuesday",
            exercises=["Yoga: 30 min", "Core exercises"],
            duration="45 minutes",
            intensity="Light"
        )
    ]
    
    if not isinstance(workout_data, list):
        st.warning("Invalid workout plan format. Using default plan.")
        return fallback_plan
    
    valid_days = []
    for day_data in workout_data:
        try:
            if not all(key in day_data for key in ["day", "exercises", "duration", "intensity"]):
                continue
                
            if not isinstance(day_data.get("exercises"), list):
                day_data["exercises"] = [str(day_data["exercises"])]
                
            valid_days.append(WorkoutDay(**day_data))
        except ValidationError:
            continue
    
    return valid_days if valid_days else fallback_plan


def main():
    st.set_page_config(
        page_title="Health & Wellness Planner",
        page_icon="💪",
        layout="wide"
    )
    
    st.title("🌟 AI Health & Wellness Planner")
    st.caption("Your personalized fitness and nutrition companion")
    
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "meal_plan" not in st.session_state:
        st.session_state.meal_plan = None
    if "workout_plan" not in st.session_state:
        st.session_state.workout_plan = None
    if "progress" not in st.session_state:
        st.session_state.progress = []
    
    tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Meal Plan", "Workout Plan", "Progress Tracker"])
    
    with tab1:
        st.subheader("Your Profile")
        with st.form("profile_form"):
            name = st.text_input("Full Name", value="Alex")
            age = st.number_input("Age", min_value=18, max_value=100, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
            height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
            goal = st.text_area("Primary Goal", value="Lose 5kg in 2 months")
            dietary_prefs = st.text_input("Dietary Preferences", value="Vegetarian")
            fitness_level = st.selectbox("Fitness Level", ["Beginner", "Intermediate", "Advanced"])
            injuries = st.text_input("Injuries or Limitations (if any)")
            
            submitted = st.form_submit_button("Save Profile")
            if submitted:
                st.session_state.profile = UserProfile(
                    name=name,
                    age=age,
                    gender=gender,
                    weight=weight,
                    height=height,
                    goal=goal,
                    dietary_prefs=dietary_prefs,
                    fitness_level=fitness_level,
                    injuries=injuries
                )
                st.success("Profile saved successfully!")
        
        if st.session_state.profile:
            st.json(st.session_state.profile.dict())
    
    with tab2:
        st.subheader("Personalized Meal Plan")
        
        if st.session_state.profile:
            if st.button("Generate Meal Plan"):
                with st.spinner("🍳 Creating your personalized meal plan..."):
                    st.session_state.meal_plan = generate_meal_plan(st.session_state.profile)
            
            if st.session_state.meal_plan:
                st.subheader("Your 7-Day Meal Plan")
                
                for day in st.session_state.meal_plan:
                    with st.expander(f"{day.day}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Breakfast**")
                            st.write(day.breakfast)
                            
                            st.markdown("**Lunch**")
                            st.write(day.lunch)
                        
                        with col2:
                            st.markdown("**Dinner**")
                            st.write(day.dinner)
                            
                            st.markdown("**Snacks**")
                            st.write(day.snacks)
                
                if st.button("Regenerate Meal Plan"):
                    with st.spinner("🍳 Creating new meal plan..."):
                        st.session_state.meal_plan = generate_meal_plan(st.session_state.profile)
                        st.rerun()
        else:
            st.info("Please complete your profile first")
    
    with tab3:
        st.subheader("Personalized Workout Plan")
        
        if st.session_state.profile:
            if st.button("Generate Workout Plan"):
                with st.spinner("🏋️‍♂️ Creating your personalized workout plan..."):
                    st.session_state.workout_plan = generate_workout_plan(st.session_state.profile)
            
            if st.session_state.workout_plan:
                st.subheader("Your 7-Day Workout Plan")
                
                for day in st.session_state.workout_plan:
                    with st.expander(f"{day.day}: {day.duration} ({day.intensity})"):
                        for exercise in day.exercises:
                            st.write(f"- {exercise}")
                
                if st.button("Regenerate Workout Plan"):
                    with st.spinner("🏋️‍♂️ Creating new workout plan..."):
                        st.session_state.workout_plan = generate_workout_plan(st.session_state.profile)
                        st.rerun()
        else:
            st.info("Please complete your profile first")
    
    with tab4:
        st.subheader("Progress Tracker")
        
        if st.session_state.profile:
            with st.form("progress_form"):
                update = st.text_area("Your Progress Update", value="Lost 1kg this week!")
                submitted = st.form_submit_button("Log Progress")
                if submitted:
                    entry = {
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "update": update,
                        "category": "general",
                        "sentiment": "positive"
                    }
                    st.session_state.progress.append(entry)
                    st.success("Progress logged successfully!")
            
            if st.session_state.progress:
                st.subheader("Your Progress History")
                for entry in st.session_state.progress:
                    with st.container():
                        col1, col2 = st.columns([1,4])
                        with col1:
                            st.markdown(f"**{entry['date']}**")
                            st.caption(f"{entry['category'].capitalize()}")
                        with col2:
                            st.write(entry["update"])
                        st.divider()
        else:
            st.info("Please complete your profile first")
    
    st.sidebar.header("Resources")
    st.sidebar.markdown("[Nutrition Guidelines](https://www.healthline.com/nutrition)")
    st.sidebar.markdown("[Workout Library](https://www.bodybuilding.com/exercises)")
    st.sidebar.markdown("[Progress Tracking Tips](https://www.nerdfitness.com/blog/tracking-progress)")

if __name__ == "__main__":
    main()