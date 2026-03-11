import streamlit as st
from PIL import Image
import datetime
import base64
import json
import pandas as pd
from groq import Groq

# --- INITIAL SETUP ---
st.set_page_config(page_title="Groq AI Calorie Tracker", layout="centered")

# Sidebar for API Key
with st.sidebar:
    st.header("Configuration")
    groq_key = st.text_input("Enter Groq API Key", type="password")

if not groq_key:
    st.warning("Please enter your Groq API Key in the sidebar.")
    st.stop()

client = Groq(api_key=groq_key)

# Initialize Session History
if "history" not in st.session_state:
    st.session_state.history = []

# --- AI ANALYSIS LOGIC (GROQ VISION) ---
def analyze_with_groq(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Specific prompt for 100g ingredient breakdown
    prompt = """
    Identify the food/drink in this image. 
    1. Break it down into core ingredients (e.g., if tea: milk, sugar, tea powder).
    2. Provide Calories per 100g for each ingredient.
    3. Estimate the grams of each ingredient used in this serving.
    Return ONLY a JSON object:
    {
      "food_name": "Name",
      "ingredients": [
        {"name": "Ingredient Name", "cal_100g": 0, "est_grams": 0}
      ]
    }
    """
    
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview", # Use a Groq vision model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

# --- UI TABS ---
st.title("⚡ Groq AI Food Scanner")
tab1, tab2, tab3 = st.tabs(["📸 Scan Food", "📝 Manual Entry", "📊 History"])

# --- TAB 1: SCAN ---
with tab1:
    img_file = st.camera_input("Take a photo")
    if img_file:
        if st.button("Get Ingredient Chart"):
            with st.spinner("Groq is thinking..."):
                try:
                    res = analyze_with_groq(img_file.getvalue())
                    st.success(f"Result: {res['food_name']}")
                    
                    # Process Data
                    df = pd.DataFrame(res['ingredients'])
                    df['total_calories'] = (df['cal_100g'] * df['est_grams'] / 100).round(1)
                    
                    # 1. Bar Chart for 100g values
                    st.subheader("Calories per 100g (Standard)")
                    st.bar_chart(data=df, x="name", y="cal_100g")
                    
                    # 2. Proper Table Breakdown
                    st.subheader("Ingredient Chart")
                    st.table(df)
                    
                    total_serving = df['total_calories'].sum()
                    st.metric("Total Serving Calories", f"{total_serving} kcal")
                    
                    # Save to history with Date/Time
                    st.session_state.history.append({
                        "Date/Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Food": res['food_name'],
                        "Calories": total_serving
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 2: MANUAL ENTRY ---
with tab2:
    with st.form("manual"):
        name = st.text_input("What did you eat?")
        cals = st.number_input("Estimated Calories", min_value=0)
        if st.form_submit_button("Save Entry"):
            st.session_state.history.append({
                "Date/Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Food": name,
                "Calories": cals
            })
            st.success("Log updated!")

# --- TAB 3: HISTORY ---
with tab3:
    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)
        st.dataframe(history_df, use_container_width=True)
        
        day_total = history_df['Calories'].sum()
        st.metric("Total Calories Consumed", f"{day_total} kcal")
        
        if st.button("Clear Records"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("Scan food to see your history here.")
