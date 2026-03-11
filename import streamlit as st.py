import streamlit as st
from PIL import Image
import datetime
import base64
from openai import OpenAI

# --- INITIAL SETUP ---
st.set_page_config(page_title="AI Calorie Tracker", layout="centered")

# Enter your OpenAI Key here or set it in Streamlit Secrets
api_key = st.text_input("Enter OpenAI API Key", type="password")
client = OpenAI(api_key=api_key) if api_key else None

st.title("🍎 AI Calorie Scanner")

if "history" not in st.session_state:
    st.session_state.history = []

# --- FUNCTION TO ANALYZE IMAGE ---
def analyze_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify this food and give estimated Calories, Protein, Carbs, and Fat. Format as JSON: {'item': 'name', 'calories': 0, 'p': 0, 'c': 0, 'f': 0}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ],
            }
        ],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📸 Scan", "📝 Manual", "📊 History"])

with tab1:
    img_file = st.camera_input("Take a photo")
    if img_file and client:
        if st.button("Analyze Meal"):
            res = analyze_image(img_file.getvalue())
            entry = {
                "time": datetime.datetime.now().strftime("%I:%M %p"),
                "item": res['item'],
                "cal": res['calories'],
                "macros": f"P:{res['p']}g C:{res['c']}g F:{res['f']}g"
            }
            st.session_state.history.append(entry)
            st.success(f"Added {res['item']} ({res['calories']} kcal)")

with tab2:
    with st.form("manual"):
        name = st.text_input("Food Name")
        cals = st.number_input("Calories", min_value=0)
        if st.form_submit_button("Add"):
            st.session_state.history.append({"time": "Manual", "item": name, "cal": cals, "macros": "N/A"})

with tab3:
    total = sum(i['cal'] for i in st.session_state.history)
    st.metric("Total Calories Today", f"{total} kcal")
    st.table(st.session_state.history)