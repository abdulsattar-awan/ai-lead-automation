# AI Lead Automation (Google Sheets + Gemini + Gmail)

An AI system that reads incoming leads from a Google Sheet, scores each one,
writes a personalized reply, and sends it by Gmail only after approval in the Sheet.

## What it does

1. Reads leads (name, email, message) from a Google Sheet
2. Scores each lead with Gemini AI: **Hot / Warm / Cold / Spam**
3. Writes a professional AI reply for Hot and Warm leads only, and marks them **Pending**
4. The client reviews the reply in the Sheet and ticks the **Approve** checkbox
5. On the next run, approved replies are sent through the Gmail API and marked **Sent**
6. Skips empty rows and leads that are already scored, replied to, or sent (no duplicates)

No terminal input is needed: everything is controlled from the Google Sheet.

## Reliability

- Request timeout, so the script never hangs
- Automatic retry with fallback to a second Gemini model when one is busy
- Failed AI calls are marked "Unknown" instead of crashing the run

## Sheet layout

| name | email | message | AI Reply | Score | Status | Approve |
|------|-------|---------|----------|-------|--------|---------|

Status values: `Pending` (waiting for approval), `Sent`, `Skipped`.
The Approve column uses Google Sheets checkboxes (Insert > Checkbox).

## Tech stack

Python, Google Sheets API, Gmail API, Google Gemini (google-genai), OAuth 2.0

## Setup

1. Enable the Google Sheets API and Gmail API in Google Cloud Console
2. Download your OAuth client file as `credentials.json`
3. Create a `.env` file with: `GEMINI_API_KEY=your_key`
4. Install libraries:
   `pip install google-api-python-client google-auth-oauthlib google-genai python-dotenv`
5. Put your Sheet ID in `SHEET_ID` inside `lead_scorer.py`
6. Run: `python lead_scorer.py`

## Author

Sattar Awan | [GitHub](https://github.com/abdulsattar-awan)