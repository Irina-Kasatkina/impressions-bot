# coding=utf-8
"""Send different menus to the wishlist-shop telegram bot chat."""
import os

import django
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
from telegram.ext import ContextTypes

from .history import add_message_to_history, clear_history
from .messages import normalise_markdown_text, send_message
from .states import (
    ACQUAINTED_PRIVACY_POLICY, CONFIRMING_SELF_DELIVERY, DIALOGUE_END,
    MAIN_MENU, SELECTING_DELIVERY_METHOD, SELECTING_IMPRESSION,
    SELECTING_IMPRESSIONS_CATEGORY, SELECTING_LANGUAGE, SELECTING_QUESTION,
    SELECTING_RECEIVING_METHOD, WAITING_CUSTOMER_CONFIRMATION,
    WAITING_RECIPIENT_CONFIRMATION, WRONG_CERTIFICATE_MENU
)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impressions.settings')
django.setup()

from bot.database import Database  # noqa: E402


async def send_language_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send Language menu to chat."""
    text = 'Выбери, пожалуйста, язык / Please select a language'
    keyboard = [[
        InlineKeyboardButton('🇷🇺 Русский', callback_data='russian'),
        InlineKeyboardButton('🇬🇧 English', callback_data='english')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    if message:
        context.chat_data['messages_history'].append(message.message_id)
    return SELECTING_LANGUAGE


async def send_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Main menu to chat."""
    if context.chat_data['language'] == 'russian':
        message = 'Выбери, пожалуйста, что ты хочешь сделать'
        buttons = [
            'Выбрать впечатление',
            'Активировать сертификат',
            'F.A.Q. и поддержка'
        ]
    else:
        message = 'Please choose what you want to do'
        buttons = [
            'Select Impression',
            'Activate Certificate',
            'F.A.Q. and Support'
        ]

    text = f'{text}{message}'
    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='impression')],
        [InlineKeyboardButton(buttons[1], callback_data='certificate')],
        [InlineKeyboardButton(buttons[2], callback_data='faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_message(update, context, text, reply_markup=reply_markup)
    return MAIN_MENU


async def send_impressions_categories_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Impressions Categories menu."""
    if context.chat_data['language'] == 'russian':
        text = (
            text +
            'Для твоего удобства мы разделили подарки по нескольким '
            'категориям:'
            '\n\n'
        )
        buttons = [
            'Для мужчин',
            'Для девушек',
            'Для пар',
            'Посмотреть все',
            '« Вернуться в главное меню',
        ]
    else:
        text = (
            text +
            "For your convenience, we have divided gifts into several "
            "categories:"
            "\n\n"
        )
        buttons = [
            'For Men',
            'For Girls',
            'For Couples',
            'View All',
            '« Back to main menu'
        ]

    keyboard = []
    callbacks = ['man', 'girl', 'couple', 'all', 'main_menu']
    for button, callback in zip(buttons, callbacks):
        keyboard.append([InlineKeyboardButton(button, callback_data=callback)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_message(update, context, text, reply_markup=reply_markup)
    return SELECTING_IMPRESSIONS_CATEGORY


async def send_impressions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Impressions menu."""
    if update.callback_query:
        impressions_category = update.callback_query.data
        context.chat_data['impressions_category'] = impressions_category

    impressions = await Database.get_impressions(
        context.chat_data['language'],
        context.chat_data['impressions_category']
    )
    if not impressions:
        if context.chat_data['language'] == 'russian':
            text = 'Извини, впечатлений пока нет.\n'
        else:
            text = 'Sorry, no impressions yet.\n'
        next_state = await send_main_menu(update, context, text)
        return next_state

    if context.chat_data['impressions_category'] == 'man':
        russian_title = 'Это лучшие подарки для мужчин на Бали🔥'
        english_title = 'These are the best gifts for men in Bali🔥'
    elif context.chat_data['impressions_category'] == 'girl':
        russian_title = 'Это лучшие подарки для девушек на Бали 😍'
        english_title = 'These are the best gifts for girls in Bali 😍'
    elif context.chat_data['impressions_category'] == 'couple':
        russian_title = 'Эти подарки идеально подходят для пар ♥'
        english_title = 'These are perfect gifts for couples ♥'
    else:
        russian_title = ''
        english_title = ''

    if context.chat_data['language'] == 'russian':
        if russian_title:
            text += '*' + russian_title + '*\n\n'

        text += (
            'Нажимай на впечатление, чтобы прочитать о нём подробнее.\n'
            'Когда выберешь подходящее, отправь боту его номер, чтобы '
            'перейти к покупке.'
            '\n\n'
        )
        button = '‹  Вернуться к выбору категории'
    else:
        if english_title:
            text += '*' + english_title + '*\n\n'

        text += (
            "Click on an impression to read more about it.\n"
            "When you choose the right one, send the bot its number "
            "to proceed to purchase."
            "\n\n"
        )
        button = '‹  Back to category selection'

    text = normalise_markdown_text(text)
    context.chat_data['impressions_ids'] = []
    for impression_number, impression in enumerate(impressions, 1):
        impression_title = normalise_markdown_text(
            f"{impression_number}. {impression['name']} - "
            f"{impression['price']}"
        )
        text += f"[{impression_title}]({impression['url']})\n"
        context.chat_data['impressions_ids'].append(impression['id'])

    keyboard = [[InlineKeyboardButton(button, callback_data='category_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    parse_mode = 'MarkdownV2'

    await send_message(
        update, context, text, reply_markup=reply_markup, parse_mode=parse_mode
    )
    return SELECTING_IMPRESSION


async def send_receiving_methods_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send to chat Menu of ways to receive order."""
    impression = await Database.get_impression(
        context.chat_data['impression_id'],
        context.chat_data['language']
    )
    impression_title = f"{impression['name']} - {impression['price']}"
    if context.chat_data['language'] == 'russian':
        text = normalise_markdown_text(
            f'{text}Отличный выбор! Ты выбрал(а) ' +
            'сертификат:\n*' +
            impression_title +
            '*\n\nВ какой форме хочешь получить его?'
        )
        buttons = [
            '🎁 Сертификат в коробке',
            '💌 Электронный сертификат',
            '‹ Выбрать другое впечатление',
            '« Вернуться в главное меню'
        ]
    else:
        text = normalise_markdown_text(
            f'{text}Great choice! You chose ' +
            'the certificate:\n*' +
            impression_title +
            '*\n\nIn what form do you want to receive it?'
        )
        buttons = [
            '🎁 Certificate in a box',
            '💌 Electronic certificate',
            '‹ Choose a different impression',
            '« Back to main menu'
        ]

    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='gift_box')],
        [InlineKeyboardButton(buttons[1], callback_data='email')],
        [InlineKeyboardButton(buttons[2], callback_data='impression')],
        [InlineKeyboardButton(buttons[3], callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    parse_mode = 'MarkdownV2'

    await send_message(
        update, context, text, reply_markup=reply_markup, parse_mode=parse_mode
    )
    return SELECTING_RECEIVING_METHOD


async def send_privacy_policy_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send Privacy Policy link and button to chat."""
    policy_url = await Database.get_policy_url(context.chat_data['language'])
    if context.chat_data['language'] == 'russian':
        text = (
            'Спасибо, записали 👌\n\n'
            'Пожалуйста, ознакомься с [Политикой конфиденциальности и '
            f'положением об обработке персональных данных 📇]({policy_url})'
        )
        button = 'Ознакомлен(а)'
    else:
        text = (
            'Thank you, we wrote it down 👌\n\n'
            'Please read the *[Privacy Policy and the provisions '
            f'on the processing of personal data 📇]({policy_url})*'
        )
        button = 'Acquainted'

    keyboard = [[InlineKeyboardButton(button, callback_data='privacy_policy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    parse_mode = 'MarkdownV2'

    await send_message(
        update, context, text, reply_markup=reply_markup, parse_mode=parse_mode
    )
    return ACQUAINTED_PRIVACY_POLICY


async def send_customer_confirmation_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send confirmation menu of customer fullname and phonenumber."""
    if context.chat_data['language'] == 'russian':
        text = (
            text +
            "Ты ввел(а):\n"
            f"{context.chat_data['customer_fullname']}\n"
            f"{context.chat_data['customer_phone']}\n\n"
            "Всё верно?"
        )
        buttons = ["Да, верно", "Исправить данные"]
    else:
        text = (
            text +
            "Here's what you entered:\n"
            f"{context.chat_data['customer_fullname']}\n"
            f"{context.chat_data['customer_phone']}\n\n"
            "Is that right?"
        )
        buttons = ["Yes, that's right", 'Correct the data']

    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='right_customer')],
        [InlineKeyboardButton(buttons[1], callback_data='wrong_customer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_CONFIRMATION


async def send_screenshot_receiving_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Send the menu to get a screenshot."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Спасибо за покупку! Мы всё проверим '
            'и в ближайшее время тебе напишет оператор 🎆'
        )
        button = 'Спасибо 👌, вернуться в главное меню'
    else:
        text = (
            'Thank you for your purchase! We will check everything '
            'and an operator will write to you shortly 🎆'
        )
        button = 'Thanks 👌, back to the main menu'

    keyboard = [[InlineKeyboardButton(button, callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return DIALOGUE_END


async def send_delivery_methods_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Delivery methods menu."""
    if context.chat_data['language'] == 'russian':
        text = (
            f'{text}Спасибо!\n'
            'Подскажи, как тебе удобнее получить сертификат\n\n'
            'Пункт самовывоза находится на Буките\n\n'
            'Стоимость доставки зависит от района'
        )
        buttons = ['Доставка курьером', 'Самовывоз']
    else:
        text = (
            f'{text}Thank you!\n'
            'Tell me how you can get the certificate\n\n'
            'The self-delivery point is on Bukit.\n\n'
            'Delivery cost depends on the neighbourhood'
        )
        buttons = ['Courier delivery', 'Self-delivery']

    keyboard = [
        [
            InlineKeyboardButton(buttons[0], callback_data='courier_delivery'),
            InlineKeyboardButton(buttons[1], callback_data='self_delivery'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await clear_history(update, context)
    message = await context.bot.send_message(
        chat_id=update.effective_chat['id'],
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return SELECTING_DELIVERY_METHOD


async def send_recipient_confirmation_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send confirmation menu of recipient name and contact."""
    if context.chat_data['language'] == 'russian':
        text = (
            text +
            "Ты ввел(а):\n"
            f"{context.chat_data['recipient_name']}\n"
            f"{context.chat_data['recipient_contact']}\n\n"
            "Всё верно?"
        )
        buttons = ["Да, верно", "Исправить данные"]
    else:
        text = (
            text +
            "Here's what you entered:\n"
            f"{context.chat_data['recipient_name']}\n"
            f"{context.chat_data['recipient_contact']}\n\n"
            "Is that right?"
        )
        buttons = ["Yes, that's right", 'Correct the data']

    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='right_recipient')],
        [InlineKeyboardButton(buttons[1], callback_data='wrong_recipient')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return WAITING_RECIPIENT_CONFIRMATION


async def send_successful_booking_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Message about successful booking."""
    if context.chat_data['delivery_method'] == 'courier_delivery':
        recipient_name = context.chat_data['recipient_name']
        recipient_contact = context.chat_data['recipient_contact']
    else:
        recipient_name = context.chat_data['customer_fullname']
        recipient_contact = 'Получателем является заказчик'

    await Database.create_order(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        customer_email='',
        customer_fullname=context.chat_data['customer_fullname'],
        customer_phone=context.chat_data['customer_phone'],
        impression_id=context.chat_data['impression_id'],
        recipient_name=recipient_name,
        recipient_contact=recipient_contact,
        email_receiving=False,
        delivery_method=context.chat_data['delivery_method']
    )

    if context.chat_data['language'] == 'russian':
        text = (
            'Мы забронировали сертификат ✨\n\n'
            'В ближайшее время тебе напишет оператор'
        )
        button = 'Спасибо 👌, вернуться в главное меню'
    else:
        text = (
            "We've booked the certificate ✨\n\n"
            "An operator will write to you shortly"
        )
        button = 'Thanks 👌, back to the main menu'

    keyboard = [[InlineKeyboardButton(button, callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.callback_query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return DIALOGUE_END


async def send_self_delivery_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Handle Self-delivery button click."""
    self_delivery_point = await Database.get_self_delivery_point(
        context.chat_data['language']
    )
    if context.chat_data['language'] == 'russian':
        text = (
            f'{text}Самовывоз доступен по адресу:\n' +
            self_delivery_point['address'] +
            '\n\nЧасы работы:\n' +
            self_delivery_point['opening_hours']
        )
        buttons = ['Мне подходит', '‹ Назад к способам доставки']
    else:
        text = (
            f'{text}Self-collection is available at the address:\n' +
            self_delivery_point['address'] +
            '\n\nOpening hours:\n' +
            self_delivery_point['opening_hours']
        )
        buttons = ['It works for me', '‹ Back to delivery methods']

    keyboard = [[
        InlineKeyboardButton(buttons[0], callback_data='self_delivery_yes'),
        InlineKeyboardButton(buttons[1], callback_data='self_delivery_no'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return CONFIRMING_SELF_DELIVERY

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    return CONFIRMING_SELF_DELIVERY


async def send_good_certificate_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    impression_name: str
) -> int:
    """Send to chat menu for case of correct certificate ID."""
    if context.chat_data['language'] == 'russian':
        text = normalise_markdown_text(
            'Твое впечатление это -\n'
            f'*{impression_name}*\n'
            'Прекрасный выбор!\n\n'
            'В течение часа с тобой свяжется оператор\n'
            'и расскажет все детали.\n'
            'До скорых встреч ✋'
        )
        button = 'Спасибо 👌, вернуться в главное меню'
    else:
        text = normalise_markdown_text(
            'Your impression is\n'
            f'*{impression_name}*\n'
            'Excellent choice!\n\n'
            'An operator will contact you within an hour\n'
            'with all the details.\n'
            'See you soon ✋'
        )
        button = 'Thanks 👌, back to the main menu'

    keyboard = [[InlineKeyboardButton(button, callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(
        text=text,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return DIALOGUE_END


async def send_wrong_certificate_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send to chat menu for case of incorrect certificate ID."""
    if context.chat_data['language'] == 'russian':
        text_beginning = text if text else 'Что-то пошло не так\n'
        text = (
            f'{text_beginning}Проверь, пожалуйста, правильно ли ты ввел(а) '
            'ID и действителен ли срок действия сертификата\n\n'
            'Если тебе нужна помощь, нажми кнопку "Позвать человека"'
        )
        buttons = [
            'Ввести ID снова',
            'Позвать человека',
            'Спасибо 👌, вернуться в главное меню'
        ]
    else:
        text_beginning = text if text else 'Something went wrong\n'
        text = (
            f'{text_beginning}Please check if you have entered the ID '
            'correctly and if the certificate expiry date is valid\n\n'
            'If you need help, click the "Call Person" button'
        )
        buttons = [
            'Enter ID again',
            'Call Person',
            'Thanks 👌, back to the main menu'
        ]

    keyboard = [
        [
            InlineKeyboardButton(buttons[0], callback_data='certificate_id'),
            InlineKeyboardButton(buttons[1], callback_data='call_person')
        ],
        [
            InlineKeyboardButton(buttons[2], callback_data='main_menu'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # if update.callback_query:
    #     await update.callback_query.edit_message_text(
    #         text=text,
    #         reply_markup=reply_markup
    #     )
    #     return WRONG_CERTIFICATE_MENU

    message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return WRONG_CERTIFICATE_MENU


async def send_calling_person_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send a chat message when calling a person."""
    await Database.create_support_application(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        request_type=context.chat_data['request_type']
    )

    if context.chat_data['language'] == 'russian':
        text = 'Спасибо за обращение, поддержка ответит в ближайшее время'
        button = 'Спасибо 👌, вернуться в главное меню'
    else:
        text = 'Thank you for contacting us, support will respond shortly'
        button = 'Thanks 👌, back to the main menu'

    keyboard = [[InlineKeyboardButton(button, callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # if update.callback_query:
    message = await update.callback_query.edit_message_text(
        text,
        reply_markup=reply_markup
    )
    add_message_to_history(context, message)
    return DIALOGUE_END

    # await update.message.reply_text(text=text)
    # return DIALOGUE_END


async def send_faq_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Handle the FAQ button click."""
    faq_details = await Database.get_faq_details(
        context.chat_data['language']
    )
    if context.chat_data['language'] == 'russian':
        if faq_details:
            text += 'Нажми на вопрос, чтобы прочитать ответ на него.\n\n'
        else:
            text += 'Извини, FAQ пока пусто.\n\n'
        buttons = ['Позвать человека', '« Вернуться в главное меню']
    else:
        if faq_details:
            text += 'Click on a question to read the answer to it.\n\n'
        else:
            text += 'Sorry, the FAQ is empty for now.\n\n'
        buttons = ['Call Person', '« Back to main menu']

    text = normalise_markdown_text(text)
    for question_number, faq_detail in enumerate(faq_details, 1):
        faq_question = normalise_markdown_text(
            f"{question_number}. {faq_detail['question']}"
        )
        text += f"[{faq_question}]({faq_detail['url']})\n"

    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='call_person')],
        [InlineKeyboardButton(buttons[1], callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    parse_mode = 'MarkdownV2'

    await send_message(
        update, context, text, reply_markup=reply_markup, parse_mode=parse_mode
    )
    return SELECTING_QUESTION
