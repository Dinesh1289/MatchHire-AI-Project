import re


def normalize_title(title: str) -> str:

    title = title.strip()

    title = re.sub(r"\s+", " ", title)

    remove_words = [
        "urgent hiring",
        "immediate joiner",
        "remote",
        "hybrid",
        "full time",
        "contract",
    ]

    cleaned = title.lower()

    for word in remove_words:
        cleaned = cleaned.replace(word, "")

    return cleaned.title().strip()