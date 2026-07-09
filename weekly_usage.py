import asyncio
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from lib import AutomationLogger, GoogleSheetsClient, UsageChange, notifier_from_env

DATA_DIR = Path("data")
OVERALL_CSV = DATA_DIR / "usage_overall.csv"
BY_ENDGAME_CSV = DATA_DIR / "usage_by_endgame.csv"

# Add the new patch here when it drops - everything (diffing, the top-10 leaderboard, and the
# Discord labels) automatically shifts to treat the newest entry as "the current patch."
PATCH_THRESHOLDS = (2.0, 3.0, 4.0)
CURRENT_THRESHOLD = PATCH_THRESHOLDS[-1]

MEMBER_COLUMNS = ["Member 1", "Member 2", "Member 3", "Member 4"]
TOP_UNITS_COUNT = 10

# Sheet rows keep whichever "Endgame Type" label was current when they were written (e.g. older
# Apocalyptic Shadow rows predate the "Starward" node and are still stored as "Apocalyptic Shadow
# 4"), but usage counting should treat them as the same endgame. This grouping is local to the
# weekly usage report - it doesn't rename anything in the sheet or in lib/enums.py's HSRMode.
ENDGAME_TYPE_ALIASES: dict[str, list[str]] = {
    "Apocalyptic Shadow": ["Apocalyptic Shadow 4", "Apocalyptic Shadow 4 Starward"],
    "Pure Fiction": ["Pure Fiction 4", "Pure Fiction 4 Starward"],
    "Memory of Chaos": ["Memory of Chaos 4", "Memory of Chaos 4 Starward"],
}
_ENDGAME_TYPE_LOOKUP = {
    raw: canonical for canonical, raws in ENDGAME_TYPE_ALIASES.items() for raw in raws
}


def _load_dataframe() -> pd.DataFrame:
    header, *rows = GoogleSheetsClient().get_all_rows()
    df = pd.DataFrame(rows, columns=header)
    df["Patch"] = pd.to_numeric(df["Patch"], errors="coerce")
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    df["Endgame Type"] = df["Endgame Type"].replace(_ENDGAME_TYPE_LOOKUP)
    return df


def _melt_units(df: pd.DataFrame) -> pd.DataFrame:
    """One row per character appearance across the Member columns."""
    long_df = df.melt(
        id_vars=["Endgame Type", "Score"], value_vars=MEMBER_COLUMNS, value_name="Unit"
    )
    return long_df[long_df["Unit"] != ""]


def build_overall_usage(df: pd.DataFrame) -> pd.DataFrame:
    """Unit, plus how many times each has been used since patch 2.0/3.0/4.0."""
    columns = []
    for threshold in PATCH_THRESHOLDS:
        subset = _melt_units(df[df["Patch"] >= threshold])
        columns.append(subset["Unit"].value_counts().rename(f"Uses Since {threshold}"))

    result = pd.concat(columns, axis=1).fillna(0).astype(int)
    result.index.name = "Unit"
    return result.reset_index().sort_values("Unit").reset_index(drop=True)


def build_per_endgame_usage(df: pd.DataFrame) -> pd.DataFrame:
    """Endgame Type + Unit, plus usage count and average score since 2.0/3.0/4.0."""
    per_threshold = []
    for threshold in PATCH_THRESHOLDS:
        subset = _melt_units(df[df["Patch"] >= threshold])
        grouped = subset.groupby(["Endgame Type", "Unit"])
        counts = grouped.size().rename(f"Uses Since {threshold}")
        avg_scores = grouped["Score"].mean().rename(f"Avg Score Since {threshold}")
        per_threshold.append(pd.concat([counts, avg_scores], axis=1))

    result = pd.concat(per_threshold, axis=1)
    for threshold in PATCH_THRESHOLDS:
        uses_col = f"Uses Since {threshold}"
        result[uses_col] = result[uses_col].fillna(0).astype(int)
        result[f"Avg Score Since {threshold}"] = result[
            f"Avg Score Since {threshold}"
        ].round(2)

    return (
        result.reset_index()
        .sort_values(["Endgame Type", "Unit"])
        .reset_index(drop=True)
    )


def _current_patch_changes(
    key_cols: list[str], previous: pd.DataFrame | None, current: pd.DataFrame
) -> list[UsageChange]:
    """Only the usage/average-score changes for CURRENT_THRESHOLD (the most recent patch)."""
    uses_col = f"Uses Since {CURRENT_THRESHOLD}"
    avg_col = f"Avg Score Since {CURRENT_THRESHOLD}"
    has_avg_col = avg_col in current.columns

    previous_indexed = previous.set_index(key_cols) if previous is not None else None
    current_indexed = current.set_index(key_cols)

    changes = []
    for key, row in current_indexed.iterrows():
        label = key if isinstance(key, str) else " / ".join(str(part) for part in key)
        new_uses = int(row[uses_col])
        new_avg = _clean_avg(row[avg_col]) if has_avg_col else None

        if previous_indexed is not None and key in previous_indexed.index:
            old_row = previous_indexed.loc[key]
            old_uses = int(old_row[uses_col])
            old_avg = _clean_avg(old_row[avg_col]) if has_avg_col else None
        else:
            old_uses, old_avg = 0, None

        if old_uses != new_uses or old_avg != new_avg:
            changes.append(UsageChange(label, old_uses, new_uses, old_avg, new_avg))

    return changes


def _clean_avg(value: float) -> float | None:
    return None if pd.isna(value) else float(value)


def build_top_units(
    overall_df: pd.DataFrame, top_n: int = TOP_UNITS_COUNT
) -> list[tuple[str, int]]:
    """Top N units by usage since CURRENT_THRESHOLD, across all endgames combined."""
    uses_col = f"Uses Since {CURRENT_THRESHOLD}"
    top = overall_df.nlargest(top_n, uses_col)
    return [(unit, int(uses)) for unit, uses in zip(top["Unit"], top[uses_col])]


def _read_previous(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


logger = AutomationLogger(__name__)


async def run() -> None:
    notifier = notifier_from_env()

    try:
        logger.info("Starting weekly HSR character usage update")

        df = _load_dataframe()
        logger.info(f"Loaded {len(df)} row(s) from the sheet")

        overall_previous = _read_previous(OVERALL_CSV)
        by_endgame_previous = _read_previous(BY_ENDGAME_CSV)

        overall_current = build_overall_usage(df)
        by_endgame_current = build_per_endgame_usage(df)

        overall_changes = _current_patch_changes(
            ["Unit"], overall_previous, overall_current
        )
        by_endgame_changes = _current_patch_changes(
            ["Endgame Type", "Unit"], by_endgame_previous, by_endgame_current
        )
        top_units = build_top_units(overall_current)
        logger.info(
            f"Computed usage tables: {len(overall_changes)} overall change(s), "
            f"{len(by_endgame_changes)} per-endgame change(s) for patch {CURRENT_THRESHOLD}"
        )

        overall_current.to_csv(OVERALL_CSV, index=False)
        by_endgame_current.to_csv(BY_ENDGAME_CSV, index=False)
        logger.info(f"Wrote {OVERALL_CSV} and {BY_ENDGAME_CSV}")

        if notifier is not None:
            await notifier.send_usage_update(
                overall_changes, by_endgame_changes, top_units, CURRENT_THRESHOLD
            )
            logger.info("Sent weekly usage update to Discord")
        else:
            logger.warning(
                "DISCORD_WEBHOOK_URL not set - skipping Discord notification"
            )

        logger.info("Weekly HSR character usage update finished successfully")

    except Exception as error:
        logger.error(f"Weekly character usage update failed: {error}")

        if notifier is not None:
            await notifier.send_failure("Weekly Character Usage Update", str(error))

        raise


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
