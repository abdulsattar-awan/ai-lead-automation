# AI Lead Automation (Google Sheets + Gemini + Gmail)

An AI system that reads incoming leads from a Google Sheet, scores each one,
writes a personalized reply, and sends it by Gmail only after approval in the Sheet.
It runs every hour on GitHub Actions, with no laptop needed.

## What it does

1. Reads leads (name, email, message) from a Google Sheet
2. Scores each lead with Gemini AI: **Hot / Warm / Cold / Spam**
3. Writes a professional AI reply for Hot and Warm leads only, and marks them **Pending**
4. The client reviews the reply in the Sheet and ticks the **Approve** checkbox
5. On the next run, approved replies are sent by Gmail and marked **Sent**
6. Skips empty rows and leads that are already scored, replied to, or sent (no duplicates)

## Reliability

- Runs every hour in the cloud with GitHub Actions
- Google service account for Sheets and a Gmail app password, so access never expires
- Request timeout, retries, and a backup Gemini model when one is busy
- Failed AI calls are marked "Unknown" instead of crashing the run

## Sheet layout

| name | email | message | AI Reply | Score | Status | Approve |
|------|-------|---------|----------|-------|--------|---------|

Status values: `Pending`, `Sent`, `Skipped`. The Approve column uses Google Sheets checkboxes.

## Tech stack

Python, Google Sheets API (service account), Gmail SMTP (app password),
Google Gemini (google-genai), GitHub Actions

## Setup

1. In Google Cloud, enable the Google Sheets API and create a service account with a JSON key. Save it as `service_account.json`
2. Share your Google Sheet with the service account email as an Editor
3. Turn on 2-Step Verification in your Google account and create a Gmail app password
4. Create a `.env` file with three lines: `GEMINI_API_KEY=...`, `GMAIL_ADDRESS=...`, `GMAIL_APP_PASSWORD=...`
5. Install libraries: `pip install -r requirements.txt`
6. Put your Sheet ID in `SHEET_ID` inside `lead_scorer.py`
7. Run: `python lead_scorer.py`

For GitHub Actions, add `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` and `SERVICE_ACCOUNT_JSON` as repository secrets.

## Author

Sattar Awan | [GitHub](https://github.com/abdulsattar-awan)