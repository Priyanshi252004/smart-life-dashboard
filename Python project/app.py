import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from pathlib import Path

# --- Load CSS ---
css_file = Path("style.css").read_text()
st.markdown(f"<style>{css_file}</style>", unsafe_allow_html=True)

# ---------------- Classes ----------------
class Student:
    def __init__(self, name, roll, marks):
        self.name = name
        self.roll = roll
        self._marks = marks

    def get_marks(self):
        return self._marks

    def get_grade(self):
        avg = np.mean(self._marks)
        if avg >= 90:
            return "A"
        elif avg >= 75:
            return "B"
        elif avg >= 50:
            return "C"
        else:
            return "F"

class GraduateStudent(Student):
    def get_grade(self):
        avg = np.mean(self._marks)
        return "Pass" if avg >= 40 else "Fail"

class StudentManager:
    def __init__(self):
        self.students = []

    def add_student(self, student):
        self.students.append(student)

    def to_dataframe(self):
        if not self.students:
            return pd.DataFrame(columns=["Name", "Roll", "Marks", "Grade"])
        return pd.DataFrame({
            "Name": [s.name for s in self.students],
            "Roll": [s.roll for s in self.students],
            "Marks": [s.get_marks() for s in self.students],
            "Grade": [s.get_grade() for s in self.students]
        })

class Analyzer(ABC):
    @abstractmethod
    def analyze(self, df):
        pass

class PerformanceAnalyzer(Analyzer):
    def analyze(self, df):
        if df.empty:
            return {}
        stats = {}
        all_marks = np.concatenate(df["Marks"].values)
        stats["Average Marks"] = float(np.mean(all_marks))
        stats["Highest Marks"] = int(np.max(all_marks))
        stats["Lowest Marks"] = int(np.min(all_marks))
        return stats

# ---------------- Streamlit App ----------------
def main():
    st.set_page_config(page_title="Student Dashboard", layout="wide")
    st.title("🎓 Student Performance Dashboard")

    if "manager" not in st.session_state:
        st.session_state.manager = StudentManager()
    manager = st.session_state.manager
    analyzer = PerformanceAnalyzer()

    # Sidebar for adding students
    st.sidebar.header("➕ Add Student")
    with st.sidebar.form("student_form"):
        name = st.text_input("Name")
        roll = st.text_input("Roll No")
        marks = st.text_input("Marks (comma separated)")
        st_type = st.radio("Student Type", ["Normal", "Graduate"])
        submit = st.form_submit_button("Add Student")

        if submit:
            try:
                marks_list = [int(m.strip()) for m in marks.split(",")]
                student = GraduateStudent(name, roll, marks_list) if st_type == "Graduate" else Student(name, roll, marks_list)
                manager.add_student(student)
                st.sidebar.success(f"✅ Added {name} ({st_type}) successfully!")
            except:
                st.sidebar.error("⚠️ Enter valid marks (e.g., 80,90,85)")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Records", "📊 Analysis", "📈 Visualizations", "💾 Save/Load"]
    )

    # Records Tab
    with tab1:
        df = manager.to_dataframe()
        st.write("### 📋 Student Records")
        if df.empty:
            st.info("No records available.")
        else:
            st.dataframe(df)

    # Analysis Tab
    with tab2:
        df = manager.to_dataframe()
        if not df.empty:
            stats = analyzer.analyze(df)
            st.write("### 📊 Performance Analysis")
            st.json(stats)
        else:
            st.info("No students available for analysis.")

    # Visualizations Tab
    with tab3:
        df = manager.to_dataframe()
        if not df.empty:
            expanded_df = df.join(df["Marks"].apply(pd.Series).rename(
                columns=lambda x: f"Sub{x+1}"
            ))
            expanded_df.drop(columns="Marks", inplace=True)

            st.write("#### 📊 Bar Chart - Subject Marks")
            st.bar_chart(expanded_df.set_index("Name"))

            st.write("#### 🥧 Pie Chart - Grade Distribution")
            grade_counts = df["Grade"].value_counts()
            st.pyplot(grade_counts.plot.pie(autopct="%1.1f%%").figure)
            plt.clf()

            st.write("#### 📈 Line Chart - Average Trend")
            st.line_chart(expanded_df[["Sub1", "Sub2", "Sub3"]].mean().to_frame())
        else:
            st.info("No students available for visualization.")

    # Save/Load Tab
    with tab4:
        df = manager.to_dataframe()
        if not df.empty:
            st.download_button(
                "💾 Download Records as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="student_records.csv",
                mime="text/csv"
            )
        uploaded = st.file_uploader("📂 Upload CSV", type="csv")
        if uploaded is not None:
            data = pd.read_csv(uploaded)
            for _, row in data.iterrows():
                marks_list = eval(row["Marks"]) if isinstance(row["Marks"], str) else row["Marks"]
                student = Student(row["Name"], row["Roll"], marks_list)
                manager.add_student(student)
            st.success("✅ CSV loaded successfully!")

if __name__ == "__main__":
    main()
