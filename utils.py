import genshin


def format_date(time: genshin.models.PartialTime) -> str:
    return f"{time.month:02d}/" f"{time.day:02d}/" f"{time.year}"
