# coding=utf-8
"""Send input invitations to wishlist-shop telegram bot chat."""
import os

import django
from telegram import Update
from telegram.ext import ContextTypes

from .history import add_message_to_history
from .messages import normalise_markdown_text, send_message
from .states import (
    WAITING_CERTIFICATE_ID, WAITING_CUSTOMER_PHONE, WAITING_CUSTOMER_FULLNAME,
    WAITING_PAYMENT_SCREENSHOT, WAITING_RECIPIENT_CONTACT,
    WAITING_RECIPIENT_NAME
)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impressions.settings')
django.setup()

from bot.database import Database  # noqa: E402


async def send_customer_fullname_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send invitation to customer to enter their full name."""
    if context.chat_data['language'] == 'russian':
        text = 'Введи, пожалуйста, свои фамилию и имя (кириллицей):'
    else:
        text = 'Please write your first and last name:'

    message = await context.bot.send_message(
        chat_id=update.effective_chat['id'],
        text=text
    )
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_FULLNAME


async def send_customer_phone_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to the chat Request to enter the customer phone number."""
    if context.chat_data['language'] == 'russian':
        text = 'Оставь, пожалуйста, свой контактный номер телефона:'
    else:
        text = 'Please write your contact phone number:'

    message = await update.message.reply_text(text=text)
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_PHONE


async def send_payment_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Payment details and wait for payment screenshot."""
    payment_details = await Database.get_payment_details(
        context.chat_data['language']
    )
    payment_details = normalise_markdown_text(payment_details)
    if context.chat_data['language'] == 'russian':
        text = normalise_markdown_text(
            f'{text}Оплатить покупку можно по указанным реквизитам:\n\n*' +
            payment_details +
            '\n\n*После оплаты отправь нам скриншот с подтверждением оплаты:'
        )
    else:
        text = normalise_markdown_text(
            f"{text}"
            "You can pay for the purchase by the specified details:\n\n*" +
            payment_details +
            "\n\n*After payment, send us a screenshot with payment:"
            "confirmation"
        )

    message = await send_message(
        update, context, text, parse_mode='MarkdownV2'
    )
    add_message_to_history(context, message)
    return WAITING_PAYMENT_SCREENSHOT


async def send_recipient_name_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Courier delivery button click."""
    if context.chat_data['language'] == 'russian':
        text = 'Введи имя получателя (кириллицей):'
    else:
        text = 'Please write the recipient name:'

    # message = await update.callback_query.edit_message_text(text=text)
    message = await context.bot.send_message(
        chat_id=update.effective_chat['id'],
        text=text
    )
    add_message_to_history(context, message)
    return WAITING_RECIPIENT_NAME


async def send_recipient_contact_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Request recipient's contact."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Как нам связаться с получателем?\n\n'
            'Напиши номер в WhatsApp или ник в Telegram:'
        )
    else:
        text = (
            'How do we contact the recipient?\n\n'
            'Write the number in WhatsApp or nickname in Telegram:'
        )
    message = await update.message.reply_text(text=text)
    add_message_to_history(context, message)
    return WAITING_RECIPIENT_CONTACT


async def send_certificate_id_invitation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send certificate ID input request to chat."""
    if context.chat_data['language'] == 'russian':
        text = f'{text}Введи ID сертификата, чтобы активировать его:'
    else:
        text = f"{text}Write your certificate ID to activate it:"
    await update.callback_query.edit_message_text(text=text)
    return WAITING_CERTIFICATE_ID
