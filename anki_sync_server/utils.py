import re


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
