# HSR Endgame Sheet Updater

A small Python utility that fetches Honkai: Star Rail endgame data and automatically inserts the results into a Google Sheet.

Currently supported:

- ✅ Apocalyptic Shadow (`apoc`)
- ✅ Pure Fiction (`pf`)
- ✅ Anomaly Arbitration (`aa`)
- 🚧 Memory of Chaos (`moc`, not implemented yet)

The script fetches a player's endgame data through the [`genshin`](https://github.com/seriaati/genshin.py) API, converts character IDs into readable names, and uploads the results to a Google Spreadsheet. It can be run manually for a single mode, or on a daily schedule via GitHub Actions (see [Automation](#automation)).

---

## Project layout

- `main.py`, `automate.py`, `weekly_usage.py`: the three entry points (run manually with `uv run <file>.py`).
- `lib/`: all supporting code (the Google Sheets/HoYoLab clients, Discord notifier, pydantic models, etc.), kept out of the root so it's clear at a glance which files are meant to be run directly.
- `data/`: generated CSVs (see [Weekly character usage report](#weekly-character-usage-report)).

---

## Features

- Fetches endgame data from HoYoLab
- Converts character IDs into character names
- Formats rows automatically
- Uploads results directly into Google Sheets
- Replaces (instead of duplicating) rows when re-run for a date, version, and mode already recorded
- Can send an optional Discord notification after each run (see [Discord notifications](#discord-notifications))

Example output:

| Date       | Version | Mode                 | Side   | Notes | Character 1 | Character 2 | Character 3 | Character 4 | Score |
| ---------- | ------- | -------------------- | ------ | ----- | ------------ | ------------ | ------------ | ------------ | ----- |
| 2026-06-17 | 4.3     | Apocalyptic Shadow 4 | Side 1 |       | Tribbie      | Castorice    | Sunday       | Huohuo       | 3890  |
| 2026-06-17 | 4.3     | Apocalyptic Shadow 4 | Side 2 |       | Firefly      | Fugue        | Ruan Mei     | Gallagher    | 3553  |

---

## Requirements

- Python 3.13+
- A HoYoLab account with HoYoLab cookies
- A Google account with a Google Service Account

---

## Installation

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.

2. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

3. Install dependencies:

   ```bash
   uv sync --all-groups --all-extras
   ```

---

## Environment variables

Create a `.env` file in the project root with the following:

```env
HSR_COOKIES="..."
HSR_UID="..."
SHEET_CREDENTIALS="..."
```

### `HSR_COOKIES`

Your HoYoLab cookies. Used by the `genshin` library to authenticate and access your account data. See [this page](https://seria.is-a.dev/genshin.py/authentication/) for how to get them.

### `HSR_UID`

The HSR UID you want to collect endgame data for.

### `SHEET_CREDENTIALS`

The path to your Google Service Account credentials JSON file. To set this up:

1. Create a Google Cloud project at https://console.cloud.google.com/.
2. Enable the Google Sheets API and the Google Drive API.
3. Go to `APIs & Services` -> `Credentials` -> `Create Credentials` -> `Service Account` and create a service account.
4. Go to `Keys` -> `Add Key` -> `Create new key` -> `JSON` and download the key file.
5. Place the file in this project (for example, name it `service_account.json`), then set:

   ```env
   SHEET_CREDENTIALS=service_account.json
   ```

6. Create a Google Spreadsheet named `hsr_endgame` with a worksheet tab named `Endgame`.
7. Open the downloaded JSON file and find the `client_email` field (something like `example@project.iam.gserviceaccount.com`). Share the spreadsheet with that email address and give it **Editor** permissions (otherwise the script won't be able to write to it).

---

## Usage

```bash
uv run main.py MODE VERSION
```

| Argument  | Description         |
| --------- | -------------------- |
| `MODE`    | Endgame mode (`apoc`, `pf`, `aa`, or `moc`) |
| `VERSION` | HSR version number (for example, `4.3`) |

Example:

```bash
uv run main.py apoc 4.3
```

---

## Automation

A GitHub Actions workflow (`.github/workflows/update-sheet.yml`) runs `automate.py` once a day (and can also be triggered manually from the "Run workflow" button in the Actions tab), updating Apocalyptic Shadow, Pure Fiction, and Anomaly Arbitration in one go. Each run replaces any existing rows for the same date, version, and mode instead of duplicating them, so re-running on the same day is safe.

To enable the workflow, add the following secrets under the repository's `Settings -> Secrets and variables -> Actions`:

| Secret                       | Value                                                                   |
| ----------------------------- | ------------------------------------------------------------------------ |
| `HSR_COOKIES`                 | Same value as your local `.env`'s `HSR_COOKIES`                        |
| `HSR_UID`                     | Same value as your local `.env`'s `HSR_UID`                            |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The full contents of your Google Service Account JSON key file (not a path, the whole file) |
| `DISCORD_WEBHOOK_URL`         | Optional. A Discord webhook URL to send daily status updates to        |
| `DISCORD_USER_ID`             | Optional. Your Discord user ID, to `@mention` when something fails     |

The first three secrets are required for the workflow to run at all. The last two are optional (see below).

The schedule defaults to `12:00 UTC` daily. Edit the `cron` expression in the workflow file if you'd like it to land closer to your server's daily reset.

### Discord notifications

If `DISCORD_WEBHOOK_URL` is set (locally in `.env`, or as a GitHub secret), every run posts one daily summary embed to that webhook, whether or not anything failed. The summary includes:

- The HSR version the run used
- Which modes had new or changed rows (for example, `Side 1: 3553 → 3600`), and which didn't
- Any per-mode errors, shown inline alongside the rest of the summary

If a mode has nothing new, it's simply reported as "No changes" (you'll still get a message every day, so you know the automation ran, but it won't be noisy about quiet days). `@mention`s (via `DISCORD_USER_ID`) only happen when something actually failed, so you know to re-run the workflow manually.

This is entirely optional: without `DISCORD_WEBHOOK_URL` set, `automate.py` runs exactly as it would otherwise, just without sending any notifications.

---

## Weekly character usage report

A second GitHub Actions workflow (`.github/workflows/weekly-usage.yml`) runs `weekly_usage.py` every Tuesday (and can also be triggered manually from the Actions tab), reading the whole sheet and generating two CSVs under `data/`:

- **`data/usage_overall.csv`**: one row per character, with how many times they've been used since patch 2.0, since patch 3.0, and since patch 4.0.
- **`data/usage_by_endgame.csv`**: one row per character per endgame (Anomaly Arbitration and Anomaly Arbitration: King are counted separately), with usage count and average score for the same three windows.

The workflow commits the refreshed CSVs back to the repo only when they actually changed, so the CSVs double as a version history of usage over time. It reuses the same `GOOGLE_SERVICE_ACCOUNT_JSON`, `DISCORD_WEBHOOK_URL`, and `DISCORD_USER_ID` secrets as the daily workflow (no new secrets to add); it doesn't need `HSR_COOKIES`/`HSR_UID` since it only reads the already-populated sheet, not HoYoLab.

Like the daily summary, this posts a Discord message every run, whether or not anything changed (so a quiet week still confirms the workflow ran). The message has two parts:

1. **What changed**, scoped to only the current patch (`Uses Since 4.0` / `Avg Score Since 4.0`, not the older 2.0/3.0 windows), shown as a small monospace table, for example:

   ```
   Unit      Uses Since 4.0
   -------   --------------
   Feixiao   8 → 9
   Phainon   0 → 2
   ```

2. **A top-10 leaderboard** of the most-used characters since the current patch (across all endgames, from `data/usage_overall.csv`), sent every run regardless of whether anything changed.

"The current patch" is always `PATCH_THRESHOLDS[-1]` in `weekly_usage.py` (currently `4.0`). When patch 5.0 releases, just add `5.0` to that tuple and everything (the CSV columns, the diff table, and the leaderboard) shifts to treat it as current, with no other code changes needed.

For this workflow's auto-commit step to work, the repository needs to allow GitHub Actions to push commits: under `Settings -> Actions -> General -> Workflow permissions`, select **Read and write permissions**.

`aggregate_endgame.py` is a separate, gitignored, personal scratch script unrelated to this workflow; it's not run as part of the pipeline.
