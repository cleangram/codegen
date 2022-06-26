from .models import Component

TELEGRAM_PATH = Component(name="telegramPath", _module="base")

TELEGRAM_OBJECT = Component(name="TelegramObject", _module="base")
TELEGRAM_T = Component(name="T", _module="response")
TELEGRAM_RESPONSE = Component(name="Response", _module="response")
TELEGRAM_REQUEST = Component(name="Request", _module="request")
