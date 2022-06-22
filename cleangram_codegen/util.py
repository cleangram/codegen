def snake(text: str):
    """
    Transform **text** to snake_case

    >>> snake("TelegramObject")
    'telegram_object'

    :param text:
    :return:
    """
    return "".join([w if w.islower() else "_" + w.lower() for w in text]).lstrip('_')
