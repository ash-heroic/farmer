import streamlit as st
from langchain_ibm import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# Page config
st.set_page_config(page_title="🩺 Health Assistant", layout="wide", page_icon="🩺")

# Custom CSS for violet and pink theme
st.markdown("""
    <style>
        body {
            background-color: #f5e6fa;
            font-family: Arial, sans-serif;
        }
        .main {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease-in-out;
        }
        .card {
            background-color: #ffffff;
            padding: 15px 20px;
            border-left: 5px solid #8e44ad;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            animation: fadeIn 0.5s ease-in-out;
        }
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(10px);}
            to {opacity: 1; transform: translateY(0);}
        }
        .chat-bubble-user {
            background-color: #dcd6f7;
            padding: 10px;
            border-radius: 10px;
            max-width: 70%;
            align-self: flex-end;
            margin: 5px 0;
        }
        .chat-bubble-bot {
            background-color: #f2d7d5;
            padding: 10px;
            border-radius: 10px;
            max-width: 70%;
            align-self: flex-start;
            margin: 5px 0;
        }
        .navbar {
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 10px 0;
            background: linear-gradient(to right, #8e44ad, #ec7063);
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .nav-button {
            background-color: #ffffff;
            color: #8e44ad;
            border: none;
            padding: 10px 16px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .nav-button:hover {
            background-color: #f9ebf7;
        }
        .fade-enter {
            opacity: 0;
            transform: translateY(10px);
        }
        .fade-enter-active {
            opacity: 1;
            transform: translateY(0);
            transition: all 0.3s ease;
        }
        .metric-box {
            padding: 10px;
            border-radius: 8px;
            background-color: #f2e2f9;
            margin: 5px;
            text-align: center;
        }
        .positive {
            color: green;
        }
        .negative {
            color: red;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_section" not in st.session_state:
    st.session_state.current_section = "profile"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "symptoms_history" not in st.session_state:
    st.session_state.symptoms_history = []
if "treatment_plan" not in st.session_state:
    st.session_state.treatment_plan = {}
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "profile_data" not in st.session_state:
    st.session_state.profile_data = {}

# Load Watsonx credentials from secrets
try:
    credentials = {
        "url": st.secrets["WATSONX_URL"],
        "apikey": st.secrets["WATSONX_APIKEY"]
    }
    project_id = st.secrets["WATSONX_PROJECT_ID"]

    llm = WatsonxLLM(
        model_id="ibm/granite-13b-instruct-latest",
        url=credentials.get("url"),
        apikey=credentials.get("apikey"),
        project_id=project_id,
        params={
            GenParams.DECODING_METHOD: "greedy",
            GenParams.TEMPERATURE: 0.7,
            GenParams.MIN_NEW_TOKENS: 5,
            GenParams.MAX_NEW_TOKENS: 500,
            GenParams.STOP_SEQUENCES: ["Human:", "Observation"],
        },
    )
except KeyError:
    st.warning("⚠️ Watsonx credentials missing.")
    st.stop()
except Exception as e:
    st.error(f"🚨 Error initializing LLM: {str(e)}")
    st.stop()

# Function to export PDF including user profile
def export_health_report():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Add Title
    pdf.cell(0, 10, txt="HealthAI - Personalized Health Report", ln=True, align='C')
    pdf.ln(10)

    # Add User Info
    if "profile_data" in st.session_state and st.session_state.profile_data:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="User Information", ln=True)
        pdf.set_font("Arial", '', 12)
        for key, value in st.session_state.profile_data.items():
            pdf.cell(0, 10, txt=f"{key.capitalize()}: {value}", ln=True)

    # Add Metrics (Example)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="Recent Health Metrics", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt="Avg Heart Rate: 72 bpm", ln=True)
    pdf.cell(0, 10, txt="Avg Glucose: 90 mg/dL", ln=True)
    pdf.output("health_report.pdf")
    return open("health_report.pdf", "rb").read()

# Top Navigation Buttons
def render_navbar():
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(9)
    with col1:
        if st.button("🏠 Home", key="btn_home", use_container_width=True):
            st.session_state.current_section = "home"
    with col2:
        if st.button("🧾 Profile", key="btn_profile", use_container_width=True):
            st.session_state.current_section = "profile"
    with col3:
        if st.button("🧠 Symptoms", key="btn_symptoms", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "symptoms"
    with col4:
        if st.button("🤖 Chat", key="btn_chat", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "chat"
    with col5:
        if st.button("🫀 Diseases", key="btn_diseases", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "diseases"
    with col6:
        if st.button("📈 Reports", key="btn_reports", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "reports"
    with col7:
        if st.button("💊 Treatments", key="btn_treatments", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "treatments"
    with col8:
        if st.button("⚙️ Settings", key="btn_settings", use_container_width=True):
            st.session_state.current_section = "settings"
    with col9:
        if st.button("📄 Export PDF", key="btn_export", use_container_width=True, disabled=not st.session_state.profile_complete):
            st.session_state.current_section = "export_pdf"
    st.markdown('</div>', unsafe_allow_html=True)

# Header
st.markdown('<h1 style="text-align:center; color:#8e44ad;">🩺 HealthAI - Intelligent Healthcare Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:16px;">Powered by IBM Granite Models and Streamlit</p>', unsafe_allow_html=True)

# Show navigation bar only if profile is complete
if st.session_state.profile_complete:
    render_navbar()

# Functions
def save_profile(name, age, gender, height, weight):
    st.session_state.profile_data = {
        "name": name,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "bmi": round(weight / ((height / 100) ** 2), 1)
    }
    st.session_state.profile_complete = True
    st.success("✅ Profile saved successfully!")

def reset_profile():
    st.session_state.profile_complete = False
    st.session_state.profile_data = {}
    st.session_state.symptoms_history = []
    st.session_state.messages = []
    st.session_state.treatment_plan = {}
    st.session_state.glucose_log = []
    st.session_state.bp_log = []
    st.session_state.asthma_log = []
    st.success("🔄 Profile reset. Please refill your details.")

# ------------------------------ USER PROFILE ------------------------------
if st.session_state.current_section == "profile":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🧾 Complete Your Profile</h2>', unsafe_allow_html=True)
    name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    height = st.number_input("Height (cm)", min_value=50, max_value=250)
    weight = st.number_input("Weight (kg)", min_value=10, max_value=300)

    if st.button("Save Profile"):
        if name and age > 0 and height > 0 and weight > 0:
            save_profile(name, age, gender, height, weight)
        else:
            st.error("❌ Please fill in all fields.")

    if st.session_state.profile_complete:
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("🔄 Reset Profile"):
            reset_profile()
            st.rerun()

    st.markdown('</div>')

# If profile not completed, stop further access
elif not st.session_state.profile_complete:
    st.info("ℹ️ Please complete your profile before continuing.")
    if st.button("Go to Profile"):
        st.session_state.current_section = "profile"
    st.stop()

# ------------------------------ HOME PAGE ------------------------------
elif st.session_state.current_section == "home":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🩺 Welcome to HealthAI</h2>', unsafe_allow_html=True)
    st.markdown('''
        <ul>
            <li>💬 AI-Powered Symptom Checker</li>
            <li>🩸 Real-Time Disease Prediction</li>
            <li>💊 Personalized Treatment Planner</li>
            <li>🫀 Chronic Disease Logs</li>
            <li>📈 Progress Reports powered by AI</li>
        </ul>
    ''', unsafe_allow_html=True)
    st.markdown('</div>')

# ------------------------------ SYMPTOM CHECKER ------------------------------
elif st.session_state.current_section == "symptoms":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🧠 AI Symptom Checker</h2>', unsafe_allow_html=True)
    symptoms = st.text_area("Describe your symptoms:")
    if st.button("Check Symptoms"):
        with st.spinner("Analyzing..."):
            prompt = f"""
            Based on these symptoms: '{symptoms}', provide a list of possible conditions,
            their likelihood percentages, and next steps like when to see a doctor or self-care measures.
            Format the output strictly as JSON like this:
            {{
                "possible_conditions": [
                    {{"condition": "Common Cold", "likelihood_percent": 60, "notes": "Mild symptoms"}},
                    ...
                ],
                "next_steps": ["Rest", "Hydration", "Consult a doctor if fever persists"]
            }}
            """
            response = llm.invoke(prompt)
            try:
                result = eval(response.strip())  # assuming structured format
                st.session_state.symptoms_history.append({"input": symptoms, "response": result})
                st.json(result)
            except:
                st.error("Invalid response format from AI.")
    st.markdown("### 📜 Symptom History")
    for item in st.session_state.symptoms_history:
        st.markdown(f"**Q:** {item['input']}")
        st.json(item['response'])
        st.divider()
    st.markdown('</div>')

# ------------------------------ CHATBOT ------------------------------
elif st.session_state.current_section == "chat":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🤖 AI Chatbot</h2>', unsafe_allow_html=True)
    user_input = st.text_input("Ask anything about health...")
    if st.button("Send") and user_input:
        st.session_state.messages.append(("user", user_input))
        with st.spinner("Thinking..."):
            ai_response = llm.invoke(user_input)
            st.session_state.messages.append(("assistant", ai_response))
    for role, msg in st.session_state.messages:
        bubble_class = "chat-bubble-user" if role == "user" else "chat-bubble-bot"
        st.markdown(f'<div class="{bubble_class}"><b>{role}:</b> {msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>')

# ------------------------------ TREATMENTS ------------------------------
elif st.session_state.current_section == "treatments":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>💊 Personalized Treatment Planner</h2>', unsafe_allow_html=True)
    condition = st.text_input("Condition / Diagnosis")
    patient_details = st.text_area("Patient Details (Age, Gender, Comorbidities)")
    if st.button("Generate Treatment Plan"):
        with st.spinner("Generating plan..."):
            prompt = f"""
            Create a personalized treatment plan for a patient with:
            Condition: {condition}
            Details: {patient_details}
            Include medications, lifestyle changes, follow-up care, and duration.
            Format as JSON.
            """
            response = llm.invoke(prompt)
            try:
                plan = eval(response.strip())
                st.session_state.treatment_plan = plan
                st.json(plan)
            except:
                st.error("Failed to parse treatment plan.")
    st.markdown('</div>')

# ------------------------------ REPORTS ------------------------------
elif st.session_state.current_section == "reports":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>📈 Progress Reports</h2>', unsafe_allow_html=True)
    days = st.slider("Days of Trend", 1, 30, value=7)
    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    heart_rates = [random.randint(60, 100) for _ in range(days)]
    glucose_levels = [round(random.uniform(70, 140), 1) for _ in range(days)]
    blood_pressure = [(random.randint(110, 130), random.randint(70, 90)) for _ in range(days)]

    df = pd.DataFrame({
        "Date": dates,
        "Heart Rate": heart_rates,
        "Glucose Level": glucose_levels,
        "Systolic BP": [bp[0] for bp in blood_pressure],
        "Diastolic BP": [bp[1] for bp in blood_pressure]
    })

    st.line_chart(df.set_index("Date")[["Heart Rate", "Glucose Level"]])
    st.line_chart(df.set_index("Date")[["Systolic BP", "Diastolic BP"]])

    avg_hr = round(sum(heart_rates) / len(heart_rates))
    avg_gluc = round(sum(glucose_levels) / len(glucose_levels))
    st.markdown(f"<div class='metric-box'>Avg Heart Rate: {avg_hr} bpm <span class='positive'>▲+1</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'>Avg Glucose: {avg_gluc} mg/dL <span class='negative'>▼-2</span></div>", unsafe_allow_html=True)

    if st.button("Generate AI Report Summary"):
        summary = llm.invoke(f"Provide insights based on these health trends: {df.describe().to_string()}. Give actionable advice.")
        st.markdown(f"📊 **AI Analysis:**\n{summary}")

    if st.button("📄 Export Report as PDF"):
        st.download_button(
            label="⬇️ Download PDF Report",
            data=export_health_report(),
            file_name="health_report.pdf",
            mime="application/pdf"
        )

    st.markdown('</div>')

# ------------------------------ DISEASE MANAGEMENT ------------------------------
elif st.session_state.current_section == "diseases":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🫀 Chronic Disease Logs</h2>', unsafe_allow_html=True)
    condition = st.selectbox("Condition", ["Diabetes", "Hypertension", "Asthma"])

    if condition == "Diabetes":
        glucose = st.number_input("Blood Glucose Level (mg/dL)", min_value=40, max_value=400, step=5)
        if st.button("Log Glucose"):
            st.session_state.glucose_log = st.session_state.get("glucose_log", []) + [glucose]
            st.success(f"Logged: {glucose} mg/dL")
            prompt = f"My blood sugar is {glucose}. Is it normal? What should I do?"
            try:
                advice = llm.invoke(prompt)
            except:
                advice = "AI is currently unavailable for advice."
            st.markdown(f"🤖 **AI Advice:**\n{advice}")
        if "glucose_log" in st.session_state and len(st.session_state.glucose_log) > 0:
            df_glucose = pd.DataFrame({
                "Date": [datetime.now() - timedelta(days=i) for i in range(len(st.session_state.glucose_log))],
                "Glucose Level (mg/dL)": st.session_state.glucose_log
            })
            st.line_chart(df_glucose.set_index("Date")["Glucose Level (mg/dL)"])

    elif condition == "Hypertension":
        systolic = st.number_input("Systolic (mmHg)", min_value=90, max_value=200, value=120)
        diastolic = st.number_input("Diastolic (mmHg)", min_value=60, max_value=130, value=80)
        if st.button("Log BP"):
            st.session_state.bp_log = st.session_state.get("bp_log", []) + [(systolic, diastolic)]
            st.success(f"Logged: {systolic}/{diastolic} mmHg")
            prompt = f"My blood pressure is {systolic}/{diastolic} mmHg. What does that mean?"
            try:
                advice = llm.invoke(prompt)
            except:
                advice = "AI is currently unavailable for advice."
            st.markdown(f"🤖 **AI Advice:**\n{advice}")
        if "bp_log" in st.session_state and len(st.session_state.bp_log) > 0:
            bp_data = pd.DataFrame(st.session_state.bp_log, columns=["Systolic", "Diastolic"])
            bp_data["Date"] = [datetime.now() - timedelta(days=i) for i in range(len(bp_data))]
            st.line_chart(bp_data.set_index("Date")[["Systolic", "Diastolic"]])

    elif condition == "Asthma":
        triggers = st.text_area("Triggers Today (e.g., pollen, dust)")
        severity = st.slider("Severity (1-10)", 1, 10)
        if st.button("Log Asthma Episode"):
            st.session_state.asthma_log = st.session_state.get("asthma_log", []) + [{"triggers": triggers, "severity": severity}]
            st.success("Episode logged successfully.")
            prompt = f"What are some ways to avoid asthma triggers like {triggers}?"
            try:
                advice = llm.invoke(prompt)
            except:
                advice = "AI is currently unavailable for advice."
            st.markdown(f"🤖 **AI Advice:**\n{advice}")
        if "asthma_log" in st.session_state and len(st.session_state.asthma_log) > 0:
            asthma_df = pd.DataFrame(st.session_state.asthma_log)
            asthma_df["Date"] = [datetime.now() - timedelta(days=i) for i in range(len(asthma_df))]
            st.line_chart(asthma_df.set_index("Date")["severity"])

    st.markdown('</div>')

# ------------------------------ SETTINGS (Optional Placeholder) ------------------------------
elif st.session_state.current_section == "settings":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>⚙️ Settings</h2>', unsafe_allow_html=True)
    st.write("You can configure preferences here.")
    st.markdown('</div>')

# ------------------------------ EXPORT PDF ------------------------------
elif st.session_state.current_section == "export_pdf":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>📄 Your PDF Report is Ready!</h2>', unsafe_allow_html=True)
    if st.button("⬇️ Download PDF Report"):
        st.download_button(
            label="⬇️ Download PDF",
            data=export_health_report(),
            file_name="health_report.pdf",
            mime="application/pdf"
        )
    st.markdown('</div>')

# Footer
st.markdown("---")
st.markdown("© 2025 MyHospital Health Assistant | Built with ❤️ using Streamlit & Watsonx")

# Debug Mode
with st.expander("🔧 Debug Mode"):
    st.write("Session State:", st.session_state)
