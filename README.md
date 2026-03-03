# Automated Monthly Social Media Reporting Tool

An automated Python tool that collects monthly metrics from **Facebook, Instagram, TikTok, LinkedIn, and YouTube**, generates Excel and PDF reports, pushes a summary to a Google Sheet, and sends an email notification — all orchestrated by GitHub Actions on the 1st of every month.

---

## Table of Contents

1. [Features](#features)  
2. [Project Structure](#project-structure)  
3. [Quick Start (local)](#quick-start-local)  
4. [Environment Variables & API Credentials](#environment-variables--api-credentials)  
5. [Repository Secrets (GitHub Actions)](#repository-secrets-github-actions)  
6. [Google Sheets Integration](#google-sheets-integration)  
7. [Database Options (SQLite / PostgreSQL)](#database-options-sqlite--postgresql)  
8. [Running Locally](#running-locally)  
9. [GitHub Actions Workflow](#github-actions-workflow)  
10. [Output Artifacts](#output-artifacts)  

---

## Features

- Collects page/account metrics from Facebook, Instagram, TikTok, LinkedIn, and YouTube.
- Stores metrics in SQLite (default) or PostgreSQL.
- Generates a styled **Excel (.xlsx)** and **PDF (.pdf)** monthly report.
- Pushes the monthly summary to a **Google Sheet**.
- Sends an email with both files attached via SMTP.
- Scheduled via GitHub Actions cron (`0 0 1 * *`) – runs at **08:00 GMT+8** on the 1st of each month.
- Supports `--run-once` CLI flag for CI and manual execution.
- Exponential back-off on all API calls.

---

## Project Structure

```
.
├── .github/workflows/monthly_report.yml  # GitHub Actions workflow
├── collectors/
│   ├── facebook.py
│   ├── instagram.py
│   ├── tiktok.py
│   ├── linkedin.py
│   └── youtube.py
├── processors/
│   └── aggregator.py
├── reporters/
│   ├── excel_report.py
│   └── pdf_report.py
├── notifiers/
│   └── email_sender.py
├── storage/
│   └── db.py
├── dashboards/
│   └── google_sheets.py
├── utils/
│   └── helpers.py
├── data/               # Created at runtime – holds metrics.db
├── reports/            # Created at runtime – holds generated reports
├── config.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start (local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/kx15/social-media-reports.git
cd social-media-reports

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure credentials
cp .env.example .env
# Edit .env and fill in your API credentials (see section below)

# 5. Run the report once
python main.py --run-once
```

---

## Environment Variables & API Credentials

Copy `.env.example` to `.env` and supply the real values. **Never commit `.env` to source control.**

### Meta (Facebook & Instagram)

1. Go to [developers.facebook.com](https://developers.facebook.com) and create an app.
2. Add the **Pages API** and **Instagram Graph API** products.
3. Generate a long-lived Page Access Token.
4. Find your **Page ID** in the Facebook Page settings.
5. Find the **Instagram Business Account ID** via the Graph API explorer (`/me/accounts` → `instagram_business_account`).

```
META_ACCESS_TOKEN=<long-lived-page-access-token>
FB_PAGE_ID=<your-facebook-page-id>
IG_ACCOUNT_ID=<your-instagram-business-account-id>
```

### TikTok

1. Apply for the [TikTok for Business API](https://business-api.tiktok.com/).
2. Create an app and obtain an **Access Token**.
3. Find your **Advertiser ID** in the TikTok Ads Manager.

```
TIKTOK_ACCESS_TOKEN=<tiktok-access-token>
TIKTOK_ADVERTISER_ID=<advertiser-id>
```

### LinkedIn

1. Go to [linkedin.com/developers](https://www.linkedin.com/developers/) and create an app.
2. Request the **Marketing Developer Platform** product to enable org analytics.
3. Generate a token with `r_organization_social` and `r_organization_admin` scopes.
4. Find your **Organization ID** in the LinkedIn Company Page URL.

```
LINKEDIN_ACCESS_TOKEN=<bearer-token>
LINKEDIN_ORG_ID=<your-organization-id>
```

### YouTube

1. Enable the **YouTube Data API v3** and **YouTube Analytics API** in [Google Cloud Console](https://console.cloud.google.com).
2. Create an **API Key** (for public data) or an **OAuth 2.0 Client** (for analytics).
3. Find your **Channel ID** in YouTube Studio → Settings → Channel.

```
YOUTUBE_API_KEY=<api-key>
YOUTUBE_CHANNEL_ID=<channel-id>
```

### SMTP / Email

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=you@example.com
EMAIL_PASSWORD=<app-password>          # Gmail: create an App Password
EMAIL_RECIPIENTS=a@example.com,b@example.com
```

---

## Repository Secrets (GitHub Actions)

Go to **Settings → Secrets and variables → Actions → New repository secret** and add each secret below.

| Secret name | Expected format / notes |
|---|---|
| `META_ACCESS_TOKEN` | Long-lived Facebook Page Access Token string |
| `FB_PAGE_ID` | Numeric Facebook Page ID string |
| `IG_ACCOUNT_ID` | Numeric Instagram Business Account ID string |
| `TIKTOK_ACCESS_TOKEN` | TikTok for Business API access token string |
| `TIKTOK_ADVERTISER_ID` | Numeric TikTok Advertiser ID string |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth 2.0 bearer token string |
| `LINKEDIN_ORG_ID` | Numeric LinkedIn Organization ID string |
| `YOUTUBE_API_KEY` | Google Cloud API key string |
| `YOUTUBE_CHANNEL_ID` | YouTube channel ID (starts with `UC…`) |
| `SMTP_SERVER` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | e.g. `587` |
| `EMAIL_USER` | Sender email address |
| `EMAIL_PASSWORD` | SMTP password or app password |
| `EMAIL_RECIPIENTS` | Comma-separated recipient email addresses |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service-account JSON or its base64-encoded form (see below) |
| `SHEET_ID` | Google Sheet ID (from the spreadsheet URL) |
| `DATABASE_URL` | *(optional)* PostgreSQL DSN, e.g. `postgresql://user:pass@host/db`. Omit for SQLite. |

---

## Google Sheets Integration

The tool can write monthly summaries to a Google Sheet.

### Setup

1. In [Google Cloud Console](https://console.cloud.google.com):
   - Enable the **Google Sheets API** and **Google Drive API**.
   - Create a **Service Account** and download the JSON key.
2. Share your target Google Sheet with the service account's email (found in the JSON key).
3. Set the `SHEET_ID` to the ID portion of the sheet URL:  
   `https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`

### Providing the Service Account JSON

**Option A – Raw JSON** (simpler for testing):
```
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

**Option B – Base64-encoded** (recommended for secrets, avoids escaping issues):
```bash
base64 -w 0 service_account.json  # prints a single line
```
Paste that line as the value of `GOOGLE_SERVICE_ACCOUNT_JSON`.

The tool automatically detects which format is used.

---

## Database Options (SQLite / PostgreSQL)

### SQLite (default)

No configuration needed. A file `data/metrics.db` is created automatically on first run.

To inspect metrics:
```bash
sqlite3 data/metrics.db "SELECT * FROM metrics;"
```

### PostgreSQL

Set the `DATABASE_URL` environment variable (or repository secret):
```
DATABASE_URL=postgresql://user:password@localhost:5432/social_reports
```

Create the database manually before the first run:
```sql
CREATE DATABASE social_reports;
```

The schema is created automatically by `init_db()`.

---

## Running Locally

### Run once (same as GitHub Actions)
```bash
python main.py --run-once
```

### Scheduled mode (runs continuously, executes at 08:00 on the 1st of each month)
```bash
python main.py
```

---

## GitHub Actions Workflow

The workflow is defined in `.github/workflows/monthly_report.yml`.

- **Automatic trigger:** `0 0 1 * *` (UTC) — 08:00 GMT+8 on the 1st of every month.
- **Manual trigger:** Go to **Actions → Monthly Social Media Report → Run workflow**.

To manually trigger via GitHub CLI:
```bash
gh workflow run monthly_report.yml
```

---

## Output Artifacts

After each successful workflow run, the following files are uploaded as workflow artifacts:

| Artifact | Contents |
|---|---|
| `excel-report` | `reports/social_report_YYYY_MM.xlsx` |
| `pdf-report` | `reports/social_report_YYYY_MM.pdf` |
| `metrics-db` | `data/metrics.db` (SQLite database) |

Download them from **Actions → [run] → Artifacts**.
