# coding=utf-8
"""Saves and clears chat history in the wishlist-shop telegram bot."""
from contextlib import suppress

import telegram.error
from telegram import Message, Update
from telegram.ext import ContextTypes


async def clear_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    first_message_deletion: bool = True,
    last_message_deletion: bool = True
) -> None:
    """Delete messages from chat."""
    messages_history = context.chat_data.get('messages_history', [])
    if update.message:
        if (
            not messages_history or
            messages_history[-1] != update.message.message_id
        ):
            messages_history.append(update.message.message_id)
            context.chat_data['messages_history'] = messages_history[:]

    last_message_id = -1
    if messages_history and not last_message_deletion:
        last_message_id = messages_history[-1]
        messages_history = messages_history[:-1]

    if not messages_history:
        return

    if not first_message_deletion and len(messages_history) == 1:
        return

    if first_message_deletion:
        with suppress(telegram.error.BadRequest):
            success = await context.bot.delete_messages(
                update.effective_chat['id'],
                messages_history[::-1]
            )
            if success:
                if last_message_deletion or last_message_id == -1:
                    context.chat_data['messages_history'] = []
                else:
                    context.chat_data['messages_history'] = [last_message_id]
        return

    first_message_id = messages_history[0]
    messages_history = messages_history[1:]
    with suppress(telegram.error.BadRequest):
        success = await context.bot.delete_messages(
            update.effective_chat['id'],
            messages_history[::-1]
        )
        if success:
            context.chat_data['messages_history'] = [first_message_id]


async def delete_last_history_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete last history message from chat."""
    messages_history = context.chat_data.get('messages_history', [])
    if not messages_history:
        return

    with suppress(telegram.error.BadRequest):
        success = await context.bot.delete_message(
            update.effective_chat['id'],
            messages_history[-1]
        )
        if success:
            context.chat_data['messages_history'] = messages_history[:-1]


def add_message_to_history(
    context: ContextTypes.DEFAULT_TYPE,
    message: Message
) -> None:
    """Add message to chat history."""
    if not message:
        return

    messages_history = context.chat_data.get('messages_history', [])
    if (
        not messages_history or
        messages_history[-1] != message.message_id
    ):
        messages_history.append(message.message_id)
        context.chat_data['messages_history'] = messages_history[:]
        print(context.chat_data['messages_history'])
