# User Guide

## What the App Does
AI Student Mentor helps educators assess student academic risk, review the main contributing factors, and generate targeted mentoring advice.

## Getting Started
1. Open the landing page and create an account, or sign in at `/login`.
2. Go to `/dashboard` to see recent assessments.
3. Open `/assessment` to create a new student profile.

## Assessment Flow
The assessment form is split into 3 steps:
- Demographics and family context
- Academic support and background
- Lifestyle, behavior, and grades

After entering the data, click **Generate Mentoring Advice**. The app will:
- predict risk level
- estimate the final grade band
- show feature-importance summaries
- generate mentoring advice

You can optionally add a custom advice request to steer the Gemini response.

## Understanding Results
- `high`, `medium`, and `low` risk categories are shown with color-coded badges.
- Confidence indicates how strongly the model favors the chosen class.
- The feature summary highlights the main factors behind the prediction.
- The mentoring advice section gives practical next steps.

## Saving and Reusing Profiles
- Save a profile in the assessment sidebar.
- Load it later from the dashboard or history view.
- Use the history page to search, filter, sort, or delete saved assessments.

## Settings
On `/settings` you can:
- view account details
- change your password
- manage local preferences
- export assessment data

## Notes
- High-risk results can trigger an email alert if mail settings are configured.
- PDF export is available from the API and the client-side UI where wired in.
- If the app says models are unavailable, the model artifact files are missing or were not built yet.