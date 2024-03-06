# coding=utf-8
"""Send error messages to wishlist-shop telegram bot chat."""
from telegram import Update
from telegram.ext import ContextTypes

from .history import add_message_to_history
from .states import (
    WAITING_CUSTOMER_PHONE, WAITING_CUSTOMER_FULLNAME, WAITING_RECIPIENT_NAME
)


async def send_fullname_error_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Message about an error in the fullname."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Ошибка в написании фамилии и имени.\n'
            'Пожалуйста, пришли нам фамилию и имя (кириллицей):'
        )
    else:
        text = (
            'First and last name spelling error.\n'
            'Please send us the first and last name:'
        )

    message = await update.message.reply_text(text=text)
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_FULLNAME


async def send_phone_error_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Message about an error in the phone number."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Введён некорректный номер телефона.\n'
            'Пожалуйста, пришли нам свой номер телефона:'
        )
    else:
        text = (
            'Phone number spelling error.\n'
            'Please send us your phone number:'
        )

    message = await update.message.reply_text(text=text)
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_PHONE


async def send_name_error_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Message about an error in the fullname."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Ошибка в написании имени.\n'
            'Пожалуйста, пришли нам имя (кириллицей):'
        )
    else:
        text = (
            'First and last name spelling error.\n'
            'Please send us the name:'
        )

    message = await update.message.reply_text(text=text)
    add_message_to_history(context, message)
    return WAITING_RECIPIENT_NAME
