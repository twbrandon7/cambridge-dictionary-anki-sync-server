import os
import re

from anki._backend import RustBackend
from anki.collection import Collection


def remove_anki_cloze_tags(text):
    """
    This function removes Anki cloze deletion tags from the given text.

    Anki cloze deletion tags are in the format {{cN::text}}, where N is an integer
    and 'text' is the cloze text. For example, in the text "I love {{c1::Australian}} wines",
    the function will return "I love Australian wines".

    Args:
        text (str): The text from which to remove the Anki cloze deletion tags.

    Returns:
        str: The text with the Anki cloze deletion tags removed.
    """
    # The regular expression pattern for Anki cloze deletion tags.
    pattern = r"{{c\d+::(.*?)}}"

    # Use the re.sub function to replace the cloze deletion tags with the cloze text.
    return re.sub(pattern, r"\1", text)


def remove_html_tags(text: str) -> str:
    """
    This function removes HTML tags from the given text.

    Args:
        text (str): The text from which to remove the HTML tags.

    Returns:
        str: The text with the HTML tags removed.
    """
    # The regular expression pattern for HTML tags.
    pattern = r"<.*?>"

    # Use the re.sub function to replace the HTML tags with an empty string.
    return re.sub(pattern, "", text)


def create_anki_collection(data_dir: str | None = None) -> Collection:
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return Collection(
        os.path.join(data_dir, "collection.anki2"),
        backend=RustBackend(langs=["en"]),
    )
