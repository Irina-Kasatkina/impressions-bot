# coding=utf-8
"""Organize the work of the wishlist-shop telegram bot."""
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler
)

from bot_utilities.handlers import handle_all_actions


def main() -> None:
    """Run the bot."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()
    bot_token = os.environ['TELEGRAM_BOT_TOKEN']
    persistence = DjangoPersistence()

    application = (
        Application.builder()
        .token(bot_token)
        .read_timeout(50)
        .write_timeout(50)
        .get_updates_read_timeout(50)
        .persistence(persistence)
        .build()
    )

    application.add_handler(CallbackQueryHandler(handle_all_actions))
    application.add_handler(MessageHandler(filters.TEXT, handle_all_actions))
    application.add_handler(MessageHandler(filters.PHOTO, handle_all_actions))
    application.add_handler(CommandHandler('start', handle_all_actions))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impressions.settings')
    django.setup()

    from bot.persistence import DjangoPersistence
    main()
