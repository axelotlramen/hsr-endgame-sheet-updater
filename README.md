# HSR Endgame Sheet Updater

A small Python utility that fetches Honkai: Star Rail endgame data and automatically inserts the results into a Google Sheet.

Currently supported:

- ✅ Apocalyptic Shadow (`apoc`)
- 🚧 Memory of Chaos (`moc`)
- ✅ Pure Fiction (`pf`)
- ✅ Anomaly Arbitration (`aa`)

The script retrieves a player's endgame data through the [`genshin`](https://github.com/seriaati/genshin.py) API, converts character IDs into readable names, and uploads the results to a Google Spreadsheet.

---

## Features

- Fetch endgame data from HoYoLab
- Convert character IDs into character names
- Automatically format rows
- Upload results directly into Google Sheets

Example output:

| Date       | Version | Mode                 | Side   | Notes | Character 1 | Character 2 | Character 3 | Character 4 | Score |
| ---------- | ------- | -------------------- | ------ | ----- | ----------- | ----------- | ----------- | ----------- | ----- |
| 2026-06-17 | 4.3     | Apocalyptic Shadow 4 | Side 1 |       | Tribbie     | Castorice   | Sunday      | Huohuo      | 3890  |
| 2026-06-17 | 4.3     | Apocalyptic Shadow 4 | Side 2 |       | Firefly     | Fugue       | Ruan Mei    | Gallagher   | 3553  |

---

## Requirements

- Python 3.13+
- A HoYoLab account
- HoYoLab cookies
- A Google account
- A Google Service Account

---

## Installation

### Install `uv`

If you do not already have `uv` installed, install it first from the [official site](https://docs.astral.sh/uv/getting-started/installation/).

---

### Clone the repository:

```bash
git clone <repository-yrl>
cd <repository-name>
```

---

### Install with all dependencies:

```bash
uv sync --all-groups --all-extras
```

---

## Environment Variables

Create an `.env` file and put the following:

```env
HSR_COOKIES="..."
HSR_UID="..."
SHEET_CREDENTIALS="..."
```

### `HSR_COOKIES`

These are your HoYoLab cookies. They are used by the `genshin` Python library to authenticate and access your account data.

To get the cookies, look at [this page](https://seria.is-a.dev/genshin.py/authentication/).

### `HSR_UID`

The HSR UID you want to collect the endgame for.

---

### `SHEET_CREDENTIALS`

The path to your Google Service Account credentials JSON file. To setup:

1. Create a Google Cloud project

Go to https://console.cloud.google.com/ and create a new project.

2. Enable the Google Sheets API and the Google Drive API.

3. Navigate to `APIs & Services` -> `Credentials` -> `Create Credentials` -> `Service Account` to create a service account.

4. Navigate to `Keys` -> `Add Key` -> `Create a new key` -> `JSON` and download the JSON file.

5. Place it inside this project and rename the file, for example `service_account.json`, and then set

```env
SHEET_CREDENTIALS=service_account.json
```

6. Create a Google Spreadsheet named `hsr_endgame` and a worksheet tab named `Endgame`.

7. Open the downloaded JSON file and find

```json
"client_email": "example@project.iam.gserviceaccount.com"
```

and copy the email address. In Google Sheets, share the sheets with the email address and give it **Editor** permissions. Otherwise the script will not have permission to write to the spreadsheet.

## Usage

```bash
uv run main.py MODE VERSION
```

Arguments:

| Argument  | Description        |
| --------- | ------------------ |
| `MODE`    | Endgame mode       |
| `VERSION` | HSR version number |

Available modes: `apoc, moc, pf, aa`

Example:

```bash
python main.py apoc 4.3
```

---

## Automation

A GitHub Actions workflow (`.github/workflows/update-sheet.yml`) runs `automate.py` once a day
(and can also be triggered manually via the "Run workflow" button), updating Apocalyptic Shadow,
Pure Fiction, and Anomaly Arbitration. Each run **replaces** any existing rows for the same
date/version/mode instead of duplicating them, so re-runs on the same day are safe.

To enable it, add the following secrets under the repository's
`Settings -> Secrets and variables -> Actions`:

| Secret                       | Value                                                                     |
| ----------------------------- | -------------------------------------------------------------------------- |
| `HSR_COOKIES`                 | Same value as your local `.env`'s `HSR_COOKIES`                          |
| `HSR_UID`                     | Same value as your local `.env`'s `HSR_UID`                              |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The **full contents** of your Google Service Account JSON key file       |
| `DISCORD_WEBHOOK_URL`         | *(Optional)* A Discord webhook URL to send daily status updates to       |
| `DISCORD_USER_ID`             | *(Optional)* Your Discord user ID to `@mention` when something fails     |

The schedule defaults to `12:00 UTC` daily — edit the `cron` expression in the workflow file to
land after your server's daily reset if you'd like fresher data.

### Discord notifications

If `DISCORD_WEBHOOK_URL` is set (locally in `.env` or as a GitHub secret), every run — whether or
not anything failed — posts a single daily summary embed to that webhook showing:

- The HSR version the run used
- Which modes actually had new/changed rows (e.g. `Side 1: 3553 → 3600`), and which didn't
- Any per-mode errors, inline with the rest of the summary

If a mode has nothing new, it's just reported as "No changes" — you'll get a message every day
either way, so you know the automation ran, but it won't be noisy about days with no updates.
`@mention`s (via `DISCORD_USER_ID`) only fire when something actually failed, so you know to
re-run the workflow manually.

This is entirely optional: without `DISCORD_WEBHOOK_URL` set, `automate.py` runs exactly as before.
