# 🎓 SmartAttend AI

### AI-Powered College Attendance Management and Risk Prediction System

SmartAttend AI is a smart web-based attendance management system designed for colleges. It allows students to securely mark their own attendance during a fixed time window and provides administrators with attendance reports, attendance percentage analysis, risk prediction, and AI-powered insights.

The system combines **Streamlit, SQLite, Python, Hugging Face Transformers, and PyTorch** to create an interactive and intelligent attendance management platform.

---

## 📌 About the Project

Traditional attendance systems can be time-consuming and may require manual entry and calculation.

**SmartAttend AI** simplifies the process by allowing students to mark their own attendance using their **Roll Number and Name**.

The system automatically:

- Verifies student details
- Opens attendance only during the permitted time
- Prevents duplicate attendance
- Automatically identifies absent students after the attendance window
- Calculates attendance percentages
- Identifies students below the minimum attendance requirement
- Provides attendance risk analysis
- Generates AI-powered attendance insights
- Provides an admin dashboard for monitoring attendance

---

## 🎯 Project Objectives

- Reduce manual attendance work
- Provide a simple student attendance portal
- Prevent duplicate attendance entries
- Automatically calculate present and absent students
- Monitor students with low attendance
- Provide AI-assisted attendance analysis
- Maintain attendance records using SQLite
- Generate daily attendance reports
- Improve attendance monitoring for faculty and administrators

---

<img width="1365" height="628" alt="image" src="https://github.com/user-attachments/assets/cf3ce0e7-df05-4f50-bcbe-79aa32947087" />


## ✨ Key Features

### 🎓 Student Portal

Students can mark their attendance using:

- Roll Number
- Student Name

The system verifies the entered details against the registered student database.

---

### ⏰ Time-Based Attendance

Attendance is available only during the configured attendance window.

**Attendance Time:**

> 🕐 1:00 PM – 1:15 PM

Students cannot mark attendance before or after the permitted time.

---

### 🔐 Duplicate Attendance Prevention

Each student can mark attendance only once for a particular session.

If a student tries to mark attendance again, the system displays:

> **Attendance already marked for this session.**

---

### 📋 Automatic Absent Detection

Students do not need to manually select "Absent".

After the attendance window closes, students who have not marked themselves present are automatically considered absent.

---

### 📊 Admin Dashboard

The admin dashboard provides:

- Total number of students
- Present students
- Absent students
- Attendance percentage
- Daily attendance report
- Complete attendance history
- Student-wise attendance analysis
- Low-attendance student identification

---

### ⚠️ Attendance Risk Analysis

The system analyzes attendance percentages and identifies students who may be at risk.

Students with attendance below the required percentage are highlighted for attention.

**Minimum Attendance Requirement:**

> **75%**

---

<img width="1073" height="695" alt="image" src="https://github.com/user-attachments/assets/905f420d-9b52-431a-b8b4-040afd98114a" />


### 🤖 AI-Powered Insights

SmartAttend AI uses Hugging Face Transformers to provide intelligent attendance-related insights.

The AI component can help with queries such as:

- Which students are below 75% attendance?
- Who needs immediate attention?
- Which students have low attendance?
- What is the overall attendance situation?
- Which students are at attendance risk?

The AI is used for **analysis and insights**, while attendance rules are handled using deterministic application logic.

---

### 🗄️ SQLite Database

SmartAttend AI uses **SQLite** for persistent data storage.

The database is automatically created when the application starts.

### Database Tables

#### `students`

Stores registered student information.

#### `attendance`

Stores daily attendance records.

#### `session_reports`

Stores generated attendance reports.

The database file is:

```text
attendance.db
