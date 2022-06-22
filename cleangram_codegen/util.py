from functools import lru_cache


@lru_cache()
def snake(text: str):
    """
    Transform **text** to snake_case

    >>> snake("TelegramObject")
    'telegram_object'

    :param text:
    :return:
    """
    return "".join([w if w.islower() else "_" + w.lower() for w in text]).lstrip('_')


def wrap(_type, _statement, _value):
    return f"{_type}[{_value}]" if _statement else _value
