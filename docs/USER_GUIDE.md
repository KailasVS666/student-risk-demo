# User Guide - AI Student Mentor

## Table of Contents
1. [Getting Started](#getting-started)
2. [Creating an Account](#creating-an-account)
3. [Dashboard Overview](#dashboard-overview)
4. [Conducting an Assessment](#conducting-an-assessment)
5. [Understanding Results](#understanding-results)
6. [Managing History](#managing-history)
7. [Settings & Preferences](#settings--preferences)
8. [FAQ](#faq)

---

## Getting Started

Welcome to **AI Student Mentor**, an AI-powered early warning system designed to help educators identify at-risk students and provide personalized mentoring advice.

### What You Need
- A modern web browser (Chrome, Firefox, Safari, Edge)
- Email address for account creation
- Student data (demographics, academics, behavioral factors)

### Key Features
- **Risk Prediction**: ML-powered assessment with 85%+ accuracy
- **SHAP Explainability**: Understand which factors influence predictions
- **AI Mentoring Advice**: Personalized strategies from Google Gemini 2.0
- **Profile Management**: Save and track student assessments
- **History Tracking**: View past assessments with search and filters

---

## Creating an Account

### Sign Up Process
1. Navigate to the landing page or go to `/signup`
2. Enter your email address
3. Create a secure password (minimum 6 characters)
4. Confirm your password
5. Click "Sign Up"

### Sign In
1. Go to `/login`
2. Enter your registered email and password
3. Click "Login"

**Demo Credentials** (for testing):
- Email: `demo@example.com`
- Password: `demo123`

---

## Dashboard Overview

After logging in, you'll land on your **Dashboard** (`/dashboard`), which shows:

### Stats Cards
- **Total Assessments**: Number of student profiles you've created
- **Average Risk**: Overall risk level across all assessments
- **Last Activity**: Date of your most recent assessment

### Recent Profiles
- Quick access to your 5 most recent student profiles
- **View** button: Loads the profile into the assessment form
- **Delete** button: Permanently removes the profile

### Quick Actions
- **New Assessment**: Navigate to the assessment form
- **View All History**: See complete assessment history with filters

---

## Conducting an Assessment

### Step 1: Navigate to Assessment
Click "New Assessment" from the dashboard or navigate to `/assessment`

### Step 2: Complete the Form
The assessment form has **3 steps**:

#### Demographics & Family (Step 1)
- **School**: Gabriel Pereira or Mousinho da Silveira
- **Sex**: Male or Female
- **Age**: 15-22 years
- **Address**: Urban or Rural
- **Family Size**: Greater than 3 or 3 or less
- **Parent's Status**: Together or Apart
- **Family Relationship**: Quality rating (1-5)

#### Academics & Support (Step 2)
- **Mother's Education**: 0 (None) to 4 (Higher Education)
- **Father's Education**: 0 (None) to 4 (Higher Education)
- **Mother's Job**: Teacher, Health, Services, At Home, Other
- **Father's Job**: Teacher, Health, Services, At Home, Other
- **Study Time**: Weekly hours (1: <2hrs, 4: >10hrs)
- **Reason for School**: Home, Reputation, Course, Other
- **Guardian**: Mother, Father, Other
- **School Support**: Yes/No
- **Family Support**: Yes/No
- **Paid Classes**: Yes/No
- **Wants Higher Ed**: Yes/No

#### Lifestyle & Grades (Step 3)
- **Activities**: Extra-curricular participation (Yes/No)
- **Nursery**: Attended nursery school (Yes/No)
- **Internet Access**: Yes/No
- **Romantic Relationship**: Yes/No
- **Travel Time**: Commute time (1: <15min, 4: >1hr)
- **Free Time**: After school (1-5)
- **Going Out**: Social frequency (1-5)
- **Workday Alcohol**: Consumption level (1-5)
- **Weekend Alcohol**: Consumption level (1-5)
- **Health Status**: Overall health (1-5)
- **Absences**: Number of school absences (0-93)
- **Past Failures**: Number of class failures (0-4)
- **First Grade (G1)**: First period grade (0-20)
- **Second Grade (G2)**: Second period grade (0-20)

### Step 3: Save Profile
- Enter a unique **Profile Name** in the sidebar
- Click "Save Profile" to store in Firebase

### Step 4: Generate Analysis
- (Optional) Add a **Custom Advice Request** for specific guidance
- Click "Generate Mentoring Advice"
- Wait for AI analysis (typically 5-10 seconds)

---

## Understanding Results

### Risk Level Badge
Shows the predicted risk level:
- **Low Risk** (Green): Grades ≥ 14/20 average
- **Medium Risk** (Yellow): Grades 10-13/20 average
- **High Risk** (Red): Grades < 10/20 average

### Confidence Score
Displays the model's confidence in its prediction (0-100%)

### Class Probabilities Chart
Pie chart showing probability distribution across Low, Medium, and High risk levels

### Grades Comparison Chart
Bar chart comparing G1 and G2 grades to the passing threshold

### Personalized Mentoring Advice
AI-generated guidance from Google Gemini 2.0 Flash, including:
- Targeted intervention strategies
- Study techniques
- Family engagement recommendations
- Resource suggestions

### SHAP Explainability Chart
- **Feature Importance**: Which factors most influenced the prediction
- **Sensitive Features Toggle**: Hide/show demographic attributes (age, sex) for fairness
- **Impact Values**: Positive (increases risk) vs. Negative (decreases risk)

### SHAP Summary
Text explanation of the top 3 factors affecting the prediction

---

## Managing History

### Accessing History
Navigate to `/history` to view all past assessments

### Search & Filter
- **Search Bar**: Find profiles by name
- **Risk Filter Dropdown**: Filter by Low, Medium, or High risk
- **Sort Options**:
  - Newest First
  - Oldest First
  - Name (A-Z)

### Profile Actions
- **View Details**: Load profile data back into the assessment form
- **Delete**: Permanently remove profile (requires confirmation)

### Stats Summary
Bottom section shows:
- Total Assessments
- High Risk Count
- Low Risk Count

---

## Settings & Preferences

Navigate to `/settings` to manage your account

### Account Information
- View your email address (read-only)
- See account creation date

### Change Password
1. Enter your current password
2. Enter new password (min 6 characters)
3. Confirm new password
4. Click "Update Password"

### Preferences
- **Email Notifications**: Receive assessment updates
- **Auto-save Assessments**: Automatically save profile data
- **Show Detailed Explanations**: Display SHAP and technical details

### Export Data
- Click "Export to JSON" to download all your assessment data
- File includes: User email, timestamps, all profile data

### Danger Zone
- **Delete Account**: Permanently removes your account and all data
- Requires typing "DELETE" to confirm
- **Cannot be undone**

---

## FAQ

### Q: How accurate is the risk prediction?
**A:** The model achieves 85%+ accuracy on test data. Use it as one tool among many, not as the sole decision-maker.

### Q: What happens if I delete a profile?
**A:** Deletion is permanent and cannot be undone. The profile is removed from Firebase Firestore.

### Q: Can I edit an existing profile?
**A:** Yes! Load the profile using "Load Profile" in the assessment sidebar, make changes, and save with the same or a new name.

### Q: How is my data stored?
**A:** All data is stored in Firebase Firestore, encrypted in transit and at rest. Only you can access your profiles.

### Q: What if I forget my password?
**A:** Currently, use the demo account or create a new account. Password reset functionality is coming soon.

### Q: Why are some features hidden in SHAP charts?
**A:** Sensitive demographic attributes (age, sex) are hidden by default to promote fairness. Toggle the checkbox to show them if needed.

### Q: What AI models power this system?
**A:**
- **LightGBM**: Gradient boosting model for risk prediction
- **SHAP**: Explainability framework for interpretable AI
- **Google Gemini 2.0 Flash**: Generative AI for mentoring advice

### Q: Is this system free?
**A:** Yes! It uses free-tier services:
- Firebase Spark Plan (Auth + Firestore)
- Google Gemini API (1,500 requests/day)

### Q: Can I use this for multiple schools?
**A:** Yes! The model was trained on data from Portuguese secondary schools but can generalize to similar educational contexts.

### Q: How often should I reassess students?
**A:** We recommend reassessing every grading period (quarterly or semester) to track progress and adjust interventions.

---

## Need Help?

Visit the **About** page (`/about`) for:
- Project mission and technology stack
- How the system works
- Model information
- Additional FAQs

For technical issues or feature requests, visit the [GitHub repository](https://github.com/yourusername/student-risk-demo).

---

**Last Updated:** October 2024  
**Version:** 1.0.0
