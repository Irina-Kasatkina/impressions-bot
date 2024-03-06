# coding=utf-8
"""Perform actions with chat messages in the wishlist-shop telegram bot."""
from telegram import (
    InlineKeyboardMarkup,
    Message,
    Update
)
from telegram.ext import ContextTypes

from .history import clear_history


async def send_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = None
) -> Message:
    """Send a menu to chat."""
    if update.callback_query:
        message = await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
        return message

    await clear_history(update, context, first_message_deletion=False)
    messages_history = context.chat_data.get('messages_history', [])
    if messages_history:
        message = await context.bot.edit_message_text(
            text=text,
            chat_id=update.effective_chat['id'],
            message_id=messages_history[0],
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
        return message

    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=True
    )
    if message:
        context.chat_data['messages_history'] = [message.message_id]
    return message


def get_misunderstanding_message(language: str) -> str:
    """Returns a message that the user action is not clear"""
    if language == 'russian':
        text = (
            'Извини, непонятно, что ты хочешь выбрать. '
            'Попробуй ещё раз.\n\n'
        )
    else:
        text = (
            "Sorry, it's not clear what you want to choose. "
            "Try again.\n\n"
        )
    return text


def normalise_markdown_text(text: str) -> str:
    """Normalise text for markdown parsing in Telegram."""
    escape_chars = r'_[]()~`>#+-=|{}.!'
    new_text = ''
    old_character = ''
    for character in text:
        if character in escape_chars and old_character != '\\':
            new_text += '\\'
        new_text += character
        old_character = character
    return new_text
