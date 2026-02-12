import streamlit as st
import google.generativeai as genai
import json
import datetime
import pandas as pd
import plotly.express as px
import random
import time

# --- 1. CONFIGURATION ---
api_key = st.secrets["GOOGLE_API_KEY"]" 

# Configure AI
genai.configure(api_key=api_key)

# TRY using the older 'gemini-pro' which is often more stable
try:
    model = genai.GenerativeModel('gemini-pro')
except:
    model = None

st.set_page_config(page_title="Taleemabad Smart Planner", page_icon="🎓", layout="wide")

# --- CUSTOM CSS (FINAL UI FIX) ---
st.markdown("""
<style>
    /* 1. Main Backgrounds */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    section[data-testid="stSidebar"] {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    
    /* 2. Fix Input Text Visibility */
    .stTextInput input, .stDateInput input, .stTimeInput input {
        color: #FFFFFF !important;
        background-color: #262730 !important;
    }
    
    /* 3. Fix the Container of Inputs */
    div[data-baseweb="input"] {
        background-color: #262730 !important;
        border: 1px solid #444;
    }
    
    /* 4. Fix Dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: white !important;
    }
    
    /* 5. Force Labels to White */
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* 6. FIX: The "White Layout" around the button */
    [data-testid="stForm"] {
        background-color: transparent !important;
        border: none;
    }
    
    /* 7. Button Styling - FORCED RED */
    div.stButton > button {
        background-color: #FF4B4B !important;
        color: white !important;
        border: 1px solid #FF4B4B !important;
        font-weight: bold;
        width: 100%;
        padding: 10px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #FF2B2B !important;
        border: 1px solid #FF2B2B !important;
        color: white !important;
    }

    /* 8. Metric Cards */
    div[data-testid="stMetricValue"] {
        color: #00FFCC !important; 
    }
    div[data-testid="stMetricLabel"] {
        color: #AAAAAA !important; 
    }

    /* 9. Fix Expander Backgrounds */
    .streamlit-expanderHeader {
        background-color: #262730 !important;
        color: white !important;
    }
    
    /* 10. Checkbox text fix */
    .stCheckbox label p {
        color: #FFFFFF !important;
    }
    /* 11. Fix Top Header (White Bar) */
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }
    
    /* 12. Fix Menu Button Visibility */
    .stMainMenu {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR INPUTS ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3407/3407026.png", width=80)
    st.title("🎓 Smart Scheduler")
    
    with st.form("user_input"):
        subjects = st.text_input("📚 Subjects (comma separated)", "Math, Physics, Computer Science")
        exam_date = st.date_input("📅 Exam Date", datetime.date.today() + datetime.timedelta(days=7))
        hours = st.slider("⏰ Daily Hours", 1, 12, 5)
        level = st.select_slider("🧠 Knowledge Level", options=["Beginner", "Intermediate", "Advanced"])
        weak_areas = st.text_input("⚠️ Weak Topic (Priority)", "Calculus")
        
        # Added type='primary' to help Streamlit recognize it needs color
        submitted = st.form_submit_button("🚀 Generate Plan", type="primary")

# --- 3. THE "HYBRID" BRAIN ---
def get_study_plan(subjects, days, hours, level, weak_areas):
    subj_list = [s.strip() for s in subjects.split(',')]
    weak_list = [w.strip() for w in weak_areas.split(',')] if weak_areas else []
    
    # 1. ACADEMIC TECHNIQUES DATABASE
    study_techniques = [
        "Feynman Technique: Explain it to a 5-year-old",
        "Blurting: Write everything from memory, then correct",
        "SQ3R: Survey, Question, Read, Recite, Review",
        "Active Recall: Test yourself constantly",
        "Leitner Box: Spaced repetition with flashcards",
        "Pomodoro 2.0: 50m focus / 10m break",
        "Interleaving: Switch topics to keep brain alert"
    ]
    
    # 2. WELLNESS & BREAKS (No Repetition Logic)
    all_breaks = [
        "NSDR (Non-Sleep Deep Rest): 10m guided rest",
        "Optical Reset: Look at horizon for 20s",
        "Box Breathing: 4-4-4-4 pattern for stress",
        "Hydration & Stretch: Drink water + touch toes",
        "Binaural Beats: 40Hz waves for focus",
        "Cognitive Shuffle: Random word visualization",
        "Nature Walk: 10m outside without phone",
        "Cold Water Splash: Reset the vagus nerve",
        "5-4-3-2-1 Grounding: Engage all senses",
        "Power Nap: Strictly 20 mins"
    ]
    # Shuffle to ensure randomness, then cycle through them
    random.shuffle(all_breaks)
    
    # 3. GENERIC TOPIC MAP (For Fallback)
    # This prevents "Physics" (Subject) appearing next to "Motion" (Topic)
    subject_topics = {
        "Math": ["Algebra", "Geometry", "Trigonometry", "Calculus", "Statistics"],
        "Physics": ["Motion", "Forces", "Energy", "Waves", "Electricity"],
        "Chemistry": ["Atomic Structure", "Bonding", "Reactions", "Acids/Bases"],
        "Biology": ["Cell Biology", "Genetics", "Ecology", "Human Anatomy"],
        "Computer Science": ["Loops", "Arrays", "Functions", "OOP", "Algorithms"],
        "History": ["Ancient Civilizations", "World Wars", "Cold War", "Industrial Rev"],
        "English": ["Grammar", "Creative Writing", "Literature Analysis", "Poetry"],
        "Geography": ["Plate Tectonics", "Climate Change", "Population", "Rivers"]
    }

    final_data = {}

    # METHOD A: Try the Real AI
    try:
        # Strict Prompting for Topic Hierarchy
        prompt = f"""
        Act as an elite academic coach. Create a customized {days}-day study plan.
        
        INPUTS:
        - Subjects: {", ".join(subj_list)}
        - Weak Areas (Prioritize): {", ".join(weak_list)}
        - Daily Hours: {hours}
        
        CRITICAL RULES:
        1. "FOCUS" COLUMN MUST BE A MICRO-TOPIC (e.g. "Kinematics"), NEVER A BROAD SUBJECT (e.g. "Physics"). 
           - Bad: "Physics"
           - Good: "Thermodynamics"
        2. BREAKS MUST BE UNIQUE. Do not repeat the same break technique twice.
        3. TASKS must be actionable study methods (e.g. "Use Feynman technique on...").
        
        OUTPUT JSON:
        {{
            "burnout_tip": "Advice string",
            "schedule": [
                {{
                    "day": "Day 1",
                    "focus": "Micro-Topic Name",
                    "tasks": ["Task 1", "Task 2"],
                    "break": "Unique Break Name"
                }}
            ]
        }}
        Generate strictly for {days} days.
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        if len(data.get('schedule', [])) < days:
            raise ValueError("Incomplete schedule")
        
        final_data = data

    except Exception as e:
        # METHOD B: Fallback Simulation (Topic-Aware)
        generated_schedule = []
        
        if hours > 8: burnout_tip = "⚠️ High Load: Use 'NSDR' explicitly."
        elif hours > 4: burnout_tip = "✅ Optimal Flow: Use 'Interleaving'."
        else: burnout_tip = "🌱 Steady Pace: Focus on 'Deep Work'."

        primary_focus = weak_list[0] if weak_list else (subj_list[0] if subj_list else "General")

        # LOGIC: If user has many weak areas (e.g. >2), use them for Practice days too.
        # This prevents random topics like "Forces" appearing when user only wants "Motion".
        use_only_weak_for_practice = len(weak_list) >= 2

        for i in range(days):
            day_num = i + 1
            is_deep_dive_day = (day_num % 2 != 0)
            
            # 1. Determine Topic
            if is_deep_dive_day:
                # ODD DAYS: Strict Deep Dive into Weak Areas
                # Cycle strictly through the weak list
                topic_name = weak_list[(i // 2) % len(weak_list)] if weak_list else primary_focus
                mode = "Deep Dive"
            else:
                # EVEN DAYS: Practice / Review
                if use_only_weak_for_practice:
                    # If user gave us plenty of topics, stick to them!
                    # We pick a different one from the deep dive day to keep it fresh
                    # Offset by 1 to ensure we don't pick the same as yesterday if possible
                    topic_name = weak_list[(i + 1) % len(weak_list)]
                    mode = "Practice"
                else:
                    # If user only gave 1 (or 0) weak topics, we MUST add variety from the Subject List
                    subj_name = subj_list[i % len(subj_list)]
                    found_key = next((k for k in subject_topics if k.lower() in subj_name.lower()), None)
                    if found_key:
                        # Pick a random sub-topic (e.g. Algebra) because we need variety
                        topic_name = random.choice(subject_topics[found_key])
                    else:
                        topic_name = f"{subj_name} Concepts"
                    mode = "Practice"
            
            # 2. Generate Tasks
            if "Deep Dive" in mode:
                tech = study_techniques[i % len(study_techniques)]
                tasks = [
                    f"**{tech}**: Master the core logic of {topic_name}.",
                    f"**Derivation**: Re-derive key formulas for {topic_name} from scratch.",
                    f"**Hard Problems**: Attempt 3 challenging {topic_name} questions."
                ]
            else:
                tasks = [
                    f"**Quick Review**: Skim notes for {topic_name}.",
                    f"**Flashcards**: Do 15 mins of active recall for {topic_name}.",
                    f"**Quiz**: Complete a short online quiz on {topic_name}."
                ]
            
            # 3. Unique Break Selection
            break_activity = all_breaks[i % len(all_breaks)]

            generated_schedule.append({
                "day": f"Day {day_num}",
                "focus": topic_name,
                "tasks": tasks,
                "break": break_activity
            })
            
        final_data = {
            "burnout_tip": burnout_tip,
            "schedule": generated_schedule
        }

    # --- POST-PROCESSING: Calculate Analytics from the Schedule ---
    # This ensures the chart matches the ACTUAL generated days, not just the inputs
    topic_counts = {}
    for day in final_data.get('schedule', []):
        # clean up focus string to get just the main topic if AI adds fluff
        raw_focus = day['focus'].replace("Deep Dive:", "").replace("Review:", "").replace("Practice:", "").strip()
        topic_counts[raw_focus] = topic_counts.get(raw_focus, 0) + 1
        
    final_data['analytics'] = topic_counts
    
    return final_data

# --- 4. MAIN DASHBOARD ---
if submitted:
    days_left = (exam_date - datetime.date.today()).days
    
    if days_left < 1:
        st.error("Please select a future date!")
    else:
        with st.spinner("🤖 AI is architecting your roadmap..."):
            time.sleep(1.5) 
            data = get_study_plan(subjects, days_left, hours, level, weak_areas)
        
        # VISUALIZATION
        st.title("Your Strategic Roadmap")
        c1, c2, c3 = st.columns(3)
        c1.metric("⏳ Days Left", days_left)
        c2.metric("🎯 Intensity", "Adaptive")
        c3.metric("🧠 Mental Health", "Active", data.get('burnout_tip', 'Take breaks'))
        
        col_chart, col_plan = st.columns([1, 2])
        
        with col_chart:
            st.subheader("📊 Focus Distribution")
            chart_data = data.get('analytics', {})
            # Normalize to dataframe
            df = pd.DataFrame([
                {"Topic": k, "Days": v} for k, v in chart_data.items()
            ])
            
            fig = px.pie(df, values='Days', names='Topic', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            
            # --- FIX: Move Legend to Bottom so Chart gets Bigger ---
            fig.update_traces(textinfo='label+percent') 
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                legend=dict(
                    orientation="h",   
                    yanchor="bottom",
                    y=-0.3,            
                    xanchor="center",
                    x=0.5,
                    font=dict(color="white") 
                ),
                margin=dict(l=20, r=20, t=30, b=80) 
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"💡 System prioritized **{weak_areas}** automatically.")

        with col_plan:
            st.subheader(f"📅 Action Plan ({days_left} Days)")
            for day in data.get('schedule', []):
                with st.expander(f"**{day['day']}** | Focus: {day['focus']}", expanded=True):
                    st.markdown("#### 📝 Study Tasks")
                    for task in day['tasks']:
                        st.checkbox(task, key=f"{day['day']}_{task}")
                    
                    st.markdown("---")
                    st.markdown("#### 🧘 Recovery Phase")

                    st.success(f"**Technique:** {day.get('break', 'Rest')}")

