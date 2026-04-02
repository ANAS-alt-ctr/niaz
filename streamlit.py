import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import socket
import time
import sys

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

if not is_port_in_use(8000):
    subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"])
    time.sleep(3) # Wait for backend to boot

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Fraud System", layout="wide")

st.title("Fraud Detection System")

menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Add Progress", "Top Students", "Fraud Records"]
)

# =========================
# HELPERS
# =========================
def normalize(val):
    try:
        val = float(val)
        if val > 1:
            val = val / 100
        return round(val * 100, 2)
    except:
        return 0


def load_data():
    try:
        res = requests.get(f"{API_URL}/fraud")
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except requests.exceptions.RequestException as e:
        print(f"API Connection Error: {e}")
    return pd.DataFrame()


# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    df = load_data()

    if df.empty:
        st.warning("No fraud data available")
    else:

        df["similarity"] = df.get("similarity", df.get("similiarity", 0))
        df["similarity"] = df["similarity"].apply(normalize)

        # ================= KPI =================
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Records", len(df))
        col2.metric("Unique Students", df["studentId"].nunique())
        col3.metric("Max Similarity %", round(df["similarity"].max(), 2))
        col4.metric("Avg Similarity %", round(df["similarity"].mean(), 2))

        st.divider()

        # ================= DISTRIBUTION =================
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Similarity Distribution")

            fig, ax = plt.subplots()
            ax.hist(df["similarity"], bins=10, edgecolor="black")
            ax.set_xlabel("Similarity %")
            ax.set_ylabel("Frequency")

            st.pyplot(fig)

        # ================= TOP STUDENTS =================
        with col2:
            st.subheader("Top Fraud Students")

            top_students = df["studentId"].value_counts().head(10)

            fig2, ax2 = plt.subplots()
            top_students.plot(kind="bar", ax=ax2)
            ax2.set_xlabel("Student ID")
            ax2.set_ylabel("Fraud Count")

            st.pyplot(fig2)

        st.divider()

        # ================= INSIGHT =================
        st.subheader("System Insight")

        avg = df["similarity"].mean()
        maxv = df["similarity"].max()

        if avg > 80:
            st.error("High risk system: abnormal similarity detected")
        elif avg > 50:
            st.warning("Moderate risk detected")
        else:
            st.success("System stable")


# =========================
# ADD PROGRESS
# =========================
elif menu == "Add Progress":

    st.subheader("Add Student Progress")

    student_id = st.text_input("Student ID")
    bootcamp_id = st.text_input("Bootcamp ID")

    yesterday = st.text_area("Yesterday Work")
    today = st.text_area("Today Plan")

    blockers = st.text_input("Blockers")
    github = st.text_input("GitHub Link")

    hours = st.number_input("Hours Worked", 0)
    need_mentor = st.selectbox("Need Mentor?", [True, False])

    grade = st.text_input("Grade")
    mentor = st.text_input("Mentor")
    feedback = st.text_area("Feedback")

    if st.button("Submit"):

        payload = {
            "student_id": student_id,
            "bootcamp_id": bootcamp_id,
            "yesterdayWork": yesterday,
            "todayPlan": today,
            "blockers": blockers,
            "githubLink": github,
            "hoursWorked": hours,
            "needMentor": need_mentor,
            "grade": grade,
            "mentor": mentor,
            "feedback": feedback
        }

        try:
            res = requests.post(f"{API_URL}/add_update", json=payload)

            if res.status_code == 200:
                data = res.json()

                st.success("Progress Submitted Successfully")

                score = float(data.get("max_score", 0))
                percent = round(score * 100, 2)

                if percent >= 75:
                    st.error(f"Fraud Detected: {percent}%")
                elif percent >= 50:
                    st.warning(f"Risk Detected: {percent}%")
                else:
                    st.success(f"Safe: {percent}%")

                st.write("Matched Work:", data.get("matched"))
                st.write("Matched Date:", data.get("matched_date"))

            else:
                st.error("API Error")
        except requests.exceptions.RequestException as e:
            st.error(f"Cannot connect to the backend server: {e}")


# =========================
# TOP STUDENTS
# =========================
elif menu == "Top Students":

    df = load_data()

    if df.empty:
        st.warning("No data available")
    else:

        if "studentId" in df:

            top = df["studentId"].value_counts().head(3).reset_index()
            top.columns = ["Student ID", "Fraud Count"]

            st.subheader("Top Fraud Students")

            for i, row in top.iterrows():
                st.markdown(f"""
                Rank {i+1}
                - Student ID: {row['Student ID']}
                - Fraud Cases: {row['Fraud Count']}
                """)

            st.bar_chart(top.set_index("Student ID"))


# =========================
# FRAUD RECORDS
# =========================
elif menu == "Fraud Records":

    df = load_data()

    if df.empty:
        st.warning("No records found")
    else:

        df["similarity"] = df.get("similarity", df.get("similiarity", 0))
        df["similarity"] = df["similarity"].apply(normalize)

        st.subheader("Fraud Records Table")

        st.dataframe(df, use_container_width=True)