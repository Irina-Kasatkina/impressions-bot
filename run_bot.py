# coding=utf-8
"""Organize the work of the impressions telegram bot."""
import io
import logging
import os
import re
from typing import Dict

import phonenumbers
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    filters,
    MessageHandler
)


(START, SELECTING_LANGUAGE, MAIN_MENU, SELECTING_IMPRESSIONS_CATEGORY,
 SELECTING_IMPRESSION, SELECTING_RECEIVING_METHOD, WAITING_CUSTOMER_EMAIL,
 ACQUAINTED_PRIVACY_POLICY, WAITING_CUSTOMER_FULLNAME, WAITING_CUSTOMER_PHONE,
 WAITING_PAYMENT_SCREENSHOT, DIALOGUE_END, SELECTING_DELIVERY_METHOD,
 WAITING_RECIPIENT_FULLNAME, WAITING_RECIPIENT_CONTACT,
 CONFIRMING_SELF_DELIVERY, WAITING_CERTIFICATE_ID, WRONG_CERTIFICATE_MENU,
 SELECTING_QUESTION, ANSWER_MENU) = range(1, 21)


async def handle_users_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle all user actions."""
    if not update.message and not update.callback_query:
        return

    user_reply = (
        update.message.text
        if update.message
        else update.callback_query.data
    )
    states_functions = {
        START: handle_start_command,
        SELECTING_LANGUAGE: handle_language_menu,
        MAIN_MENU: handle_main_menu,
        SELECTING_IMPRESSIONS_CATEGORY: handle_impressions_categories_menu,
        SELECTING_IMPRESSION: handle_impressions_menu,
        SELECTING_RECEIVING_METHOD: handle_receiving_methods_menu,
        WAITING_CUSTOMER_EMAIL: handle_customer_email_message,
        ACQUAINTED_PRIVACY_POLICY: handle_privacy_policy_button,
        WAITING_CUSTOMER_FULLNAME: handle_customer_fullname_message,
        WAITING_CUSTOMER_PHONE: handle_customer_phone_message,
        WAITING_PAYMENT_SCREENSHOT: handle_payment_screenshot,
        DIALOGUE_END: handle_dialogue_end,
        SELECTING_DELIVERY_METHOD: handle_delivery_methods_menu,
        WAITING_RECIPIENT_FULLNAME: handle_recipient_fullname_message,
        WAITING_RECIPIENT_CONTACT: handle_recipient_contact_message,
        CONFIRMING_SELF_DELIVERY: handle_self_delivery_menu,
        WAITING_CERTIFICATE_ID: handle_certificate_id_message,
        WRONG_CERTIFICATE_MENU: handle_wrong_certificate_menu,
        SELECTING_QUESTION: handle_questions_menu,
        ANSWER_MENU: handle_answer_menu
    }
    chat_state = (
        START
        if user_reply == '/start'
        else context.chat_data.get('next_state') or START
    )
    state_handler = states_functions[int(chat_state)]
    next_state = await state_handler(update, context)
    context.chat_data['next_state'] = next_state


async def handle_start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the start command."""
    text = 'Выбери, пожалуйста, язык / Please select a language'
    keyboard = [[
        InlineKeyboardButton('🇷🇺 Русский', callback_data='russian'),
        InlineKeyboardButton('🇬🇧 English', callback_data='english')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return SELECTING_LANGUAGE


async def handle_language_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Language selecting menu."""
    if not update.callback_query:
        next_state = await handle_start_command(update, context)
        return next_state

    await update.callback_query.answer()
    context.chat_data.clear()
    context.chat_data['language'] = update.callback_query.data

    next_state = await send_main_menu(update, context)
    return next_state


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
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return MAIN_MENU

    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return MAIN_MENU


async def handle_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Main menu."""
    if not update.callback_query:
        text = get_misunderstanding_message(context.chat_data['language'])
        next_state = await send_main_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'impression':
        next_state = await send_impressions_categories_menu(update, context)
        return next_state

    if update.callback_query.data == 'certificate':
        next_state = await handle_certificate_button(update, context)
        return next_state

    if update.callback_query.data == 'faq':
        next_state = await send_questions_menu(update, context)
        return next_state


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
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
        return SELECTING_IMPRESSIONS_CATEGORY

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    return SELECTING_IMPRESSIONS_CATEGORY


def normalise_text(text: str) -> str:
    """Normalise text for parsing in Telegram."""
    escape_chars = r'_[]()~`>#+-=|{}.!'
    new_text = ''
    old_character = ''
    for character in text:
        if character in escape_chars and old_character != '\\':
            new_text += '\\'
        new_text += character
        old_character = character
    return new_text


async def handle_impressions_categories_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Impressions Category selecting."""
    if not update.callback_query:
        next_state = await handle_unrecognized_impressions_category(
            update, context
        )
        return next_state

    await update.callback_query.answer()
    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    impressions_category = update.callback_query.data
    next_state = await send_impressions_menu(
        update, context, impressions_category
    )
    return next_state


async def handle_unrecognized_impressions_category(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Unrecognized impressions category."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Извини, непонятно, какую категорию впечатлений ты хочешь '
            'выбрать. Попробуй ещё раз.\n\n'
        )
    else:
        text = (
            "Sorry, it's not clear which impressions category you want to "
            "choose. Try again.\n\n"
        )

    next_state = await send_impressions_categories_menu(update, context, text)
    return next_state


async def send_impressions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    category: str,
    text: str = ''
) -> int:
    """Send Impressions menu."""
    impressions = await Database.get_impressions(context.chat_data['language'])
    if not impressions:
        if context.chat_data['language'] == 'russian':
            text = 'Извини, впечатлений пока нет.\n'
        else:
            text = 'Sorry, no impressions yet.\n'
        next_state = await send_main_menu(update, context, text)
        return next_state

    if context.chat_data['language'] == 'russian':
        text = (
            normalise_text(text) +
            'Выбери впечатление, введи его номер и отправь нам:'
            '\n\n'
        )
    else:
        text = (
            normalise_text(text) +
            "Select an impression, enter its number and send it to us:"
            "\n\n"
        )

    context.chat_data['impressions_ids'] = []
    for impression in impressions:
        impression_title = normalise_text(make_impression_title(impression))
        text += f"[{impression_title}]({impression['url']})\n"
        context.chat_data['impressions_ids'].append(impression['id'])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='MarkdownV2',
        )
        return SELECTING_IMPRESSION

    await update.message.reply_text(
        text=text,
        parse_mode='MarkdownV2',
    )
    return SELECTING_IMPRESSION


def make_impression_title(impression: Dict) -> str:
    """Make impression title."""
    return (
        f"{impression['number']}. "
        f"{impression['name']} "
        f"- {impression['price']}"
    )


def calculate_buttons_in_row(buttons_count: int) -> int:
    """Count how many buttons to place in a row."""
    buttons_in_row = 5
    if buttons_count <= buttons_in_row:
        return buttons_count

    if not buttons_count % buttons_in_row:
        if buttons_count % buttons_in_row > 1:
            return buttons_in_row

        for buttons_in_row in range(7, 3, -1):
            if buttons_count % buttons_in_row > 1:
                return buttons_in_row
    return 5


async def handle_impressions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Impression selecting."""
    if not update.callback_query:
        next_state = await handle_unrecognized_impression(update, context)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    impression_id = update.callback_query.data
    if not impression_id.isnumeric():
        next_state = await handle_unrecognized_impression(update, context)
        return next_state

    context.chat_data['impression_id'] = impression_id
    next_state = await send_receiving_methods_menu(update, context)
    return next_state


async def handle_unrecognized_impression(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Unrecognized impression."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Извини, непонятно, какое впечатление ты хочешь '
            'выбрать. Попробуй ещё раз.\n\n'
        )
    else:
        text = (
            "Sorry, it's not clear which impression you want to "
            "choose. Try again.\n\n"
        )

    next_state = await send_impressions_menu(update, context, text)
    return next_state


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
    impression_title = make_impression_title(impression)
    if context.chat_data['language'] == 'russian':
        text = normalise_text(
            f'{text}Отличный выбор! Ты выбрал(а) ' +
            'сертификат:\n*' +
            impression_title +
            '*\n\nВ какой форме хочешь получить его?'
        )
        buttons = [
            '📧 По электронной почте',
            '📨 В подарочной коробке',
            '‹ Выбрать другое впечатление',
            '« Вернуться в главное меню'
        ]
    else:
        text = normalise_text(
            f'{text}Great choice! You chose ' +
            'the certificate:\n*' +
            impression_title +
            '*\n\nIn what form do you want to receive it?'
        )
        buttons = [
            '📧 By email',
            '📨 In a gift box',
            '‹ Choose a different impression',
            '« Back to main menu'
        ]

    keyboard = [
        [
            InlineKeyboardButton(buttons[0], callback_data='email'),
            InlineKeyboardButton(buttons[1], callback_data='gift_box'),
        ],
        [
            InlineKeyboardButton(buttons[2], callback_data='impression')
        ],
        [
            InlineKeyboardButton(buttons[3], callback_data='main_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        return SELECTING_RECEIVING_METHOD

    await update.message.reply_text(
        text=text,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    return SELECTING_RECEIVING_METHOD


async def handle_receiving_methods_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Receipt method selecting."""
    if not update.callback_query:
        if context.chat_data['language'] == 'russian':
            text = (
                'Извини, непонятно, какой способ получения сертификата ты '
                'хочешь выбрать. Попробуй ещё раз.\n\n'
            )
        else:
            text = (
                "Sorry, it's not clear which method of receiving "
                'your certificate you want to choose. '
                'Try again.\n\n'
            )
        next_state = await send_receiving_methods_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    if update.callback_query.data == 'impression':
        next_state = await send_impressions_menu(update, context)
        return next_state

    if update.callback_query.data == 'email':
        next_state = await handle_email_button(update, context)
        return next_state

    if update.callback_query.data == 'gift_box':
        next_state = await handle_gift_box_button(update, context)
        return next_state


async def handle_email_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Email button click."""
    context.chat_data['receiving_method'] = 'email'
    if context.chat_data['language'] == 'russian':
        text = 'Напиши почту, на которую хотел(а) бы получить сертификат:'
    else:
        text = (
            'Write the email to which you would like to receive '
            'the certificate:'
        )
    await update.callback_query.edit_message_text(text=text)
    return WAITING_CUSTOMER_EMAIL


async def handle_customer_email_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_EMAIL state."""
    pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
    match = re.match(pattern, update.message.text.strip())
    if not match:
        if context.chat_data['language'] == 'russian':
            text = (
                'Ошибка в написании электронной почты.\n'
                'Пожалуйста, пришли нам свой адрес электронной почты:'
            )
        else:
            text = 'Email spelling error.\nPlease send us your email:'

        await update.message.reply_text(text=text)
        return WAITING_CUSTOMER_EMAIL

    context.chat_data['customer_email'] = match.groups()[0]
    next_state = await send_privacy_policy(update, context)
    return next_state


async def handle_gift_box_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Gift-box button click."""
    context.chat_data['receiving_method'] = 'gift_box'
    next_state = await send_privacy_policy(update, context)
    return next_state


async def send_privacy_policy(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send Privacy Policy to chat."""
    policy_url = await Database.get_policy_url(context.chat_data['language'])
    if context.chat_data['language'] == 'russian':
        text = (
            'Спасибо, записали 👌\n\n'
            'Пожалуйста, ознакомься с *[Политикой конфиденциальности и '
            f'положением об обработке персональных данных 📇]({policy_url})*'
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

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        return ACQUAINTED_PRIVACY_POLICY

    await update.message.reply_text(
        text=text,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    return ACQUAINTED_PRIVACY_POLICY


async def handle_privacy_policy_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Privacy Policy button click."""
    if not update.callback_query:
        next_state = await send_privacy_policy(update, context)
        return next_state

    if context.chat_data['language'] == 'russian':
        text = 'Введи, пожалуйста, свои фамилию и имя (кириллицей):'
    else:
        text = 'Please write your first and last name:'
    await update.callback_query.edit_message_text(text=text)
    return WAITING_CUSTOMER_FULLNAME


async def handle_customer_fullname_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_FULLNAME state."""
    customer_fullname = update.message.text.strip()
    if len(customer_fullname) < 4 or ' ' not in customer_fullname:
        await send_fullname_error_message(update, context)
        return WAITING_CUSTOMER_FULLNAME

    context.chat_data['customer_fullname'] = customer_fullname
    next_state = await send_phone_number_request(update, context)
    return next_state


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

    await update.message.reply_text(text=text)
    return WAITING_CUSTOMER_FULLNAME


async def send_phone_number_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to the chat Request to enter the customer phone number."""
    if context.chat_data['language'] == 'russian':
        text = 'Оставь, пожалуйста, свой контактный номер телефона:'
    else:
        text = 'Please write your contact phone number:'

    await update.message.reply_text(text=text)
    return WAITING_CUSTOMER_PHONE


async def handle_customer_phone_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_PHONE state."""
    value = update.message.text.strip()
    error = not bool(value)
    if not error:
        if value[0] == '8':
            value = '+7' + value[1:]

        try:
            value = phonenumbers.parse(value)
        except phonenumbers.phonenumberutil.NumberParseException:
            error = True

        if not error:
            error = not phonenumbers.is_valid_number(value)

    if error:
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

        await update.message.reply_text(text=text)
        return WAITING_CUSTOMER_PHONE

    context.chat_data['customer_phone'] = (
        f'+{value.country_code}{value.national_number}'
    )
    if context.chat_data['receiving_method'] == 'email':
        next_state = await send_payment_details(update, context)
        return next_state

    next_state = await send_delivery_methods_menu(update, context)
    return next_state


async def send_payment_details(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Send Payment details and wait for payment screenshot."""
    payment_details = await Database.get_payment_details(
        context.chat_data['language']
    )
    payment_details = normalise_text(payment_details)
    if context.chat_data['language'] == 'russian':
        text = normalise_text(
            f'{text}Оплатить покупку можно по указанным реквизитам:\n\n*' +
            payment_details +
            '\n\n*После оплаты отправь нам скриншот с подтверждением оплаты:'
        )
    else:
        text = normalise_text(
            f"{text}"
            "You can pay for the purchase by the specified details:\n\n*" +
            payment_details +
            "\n\n*After payment, send us a screenshot with payment:"
            "confirmation"
        )
    await update.message.reply_text(text=text, parse_mode='MarkdownV2')
    return WAITING_PAYMENT_SCREENSHOT


async def handle_payment_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle receipt of screenshot of payment."""
    if not update.message.photo:
        if context.chat_data['language'] == 'russian':
            text = 'Ты прислал не скриншот оплаты.\n\n'
        else:
            text = (
                "You didn't send a screenshot "
                "of the payment\n\n"
            )
        await send_payment_details(update, context, text)

    file_id = update.message.photo[-1].file_id
    screenshot_file = await context.bot.get_file(file_id)
    screenshot_stream = io.BytesIO()
    await screenshot_file.download_to_memory(out=screenshot_stream)
    screenshot_stream.seek(0)

    await Database.create_order(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        customer_email=context.chat_data['customer_email'],
        customer_fullname=context.chat_data['customer_fullname'],
        customer_phone=context.chat_data['customer_phone'],
        impression_id=context.chat_data['impression_id'],
        recipient_fullname=context.chat_data['customer_fullname'],
        recipient_contact='Получателем является заказчик',
        email_receiving=True,
        screenshot_stream=screenshot_stream
    )

    if context.chat_data['language'] == 'russian':
        text = (
            'Спасибо за покупку! Мы всё проверим '
            'и в ближайшее время тебе напишет оператор 🎆'
        )
        button = 'Спасибо 👌'
    else:
        text = (
            'Thank you for your purchase! We will check everything '
            'and an operator will write to you shortly 🎆'
        )
        button = 'Thanks 👌'

    keyboard = [[InlineKeyboardButton(button, callback_data='dialogue_end')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return DIALOGUE_END


async def handle_dialogue_end(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle end of dialogue."""
    if update.callback_query:
        await update.callback_query.answer()
    return 0


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
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return SELECTING_DELIVERY_METHOD

    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return SELECTING_DELIVERY_METHOD


async def handle_delivery_methods_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Delivery method menu."""
    if not update.callback_query:
        if context.chat_data['language'] == 'russian':
            text = (
                'Извини, непонятно, какой способ доставки ты хочешь выбрать. '
                'Попробуй ещё раз.\n\n'
            )
        else:
            text = (
                "Sorry, it's not clear which delivery method you want "
                "to choose. Try again.\n\n"
            )
        next_state = await send_delivery_methods_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    context.chat_data['delivery_method'] = update.callback_query.data
    if update.callback_query.data == 'courier_delivery':
        next_state = await handle_courier_delivery_button(update, context)
        return next_state

    if update.callback_query.data == 'self_delivery':
        next_state = await send_self_delivery_menu(update, context)
        return next_state


async def handle_courier_delivery_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Courier delivery button click."""
    if context.chat_data['language'] == 'russian':
        text = 'Введи имя получателя (кириллицей):'
    else:
        text = 'Please write the recipient name:'
    await update.callback_query.edit_message_text(text=text)
    return WAITING_RECIPIENT_FULLNAME


async def handle_recipient_fullname_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_RECIPIENT_FULLNAME state."""
    recipient_fullname = update.message.text.strip()
    if len(recipient_fullname) < 1:
        await send_fullname_error_message(update, context)
        return WAITING_RECIPIENT_FULLNAME

    context.chat_data['recipient_fullname'] = recipient_fullname
    next_state = await send_recipient_contact_request(update, context)
    return next_state


async def send_recipient_contact_request(
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
    await update.message.reply_text(text=text)
    return WAITING_RECIPIENT_CONTACT


async def handle_recipient_contact_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_RECIPIENT_CONTACT state."""
    recipient_contact = update.message.text.strip()
    if len(recipient_contact) < 3:
        if context.chat_data['language'] == 'russian':
            text = (
                'Ошибка в присланных контактах.\nПожалуйста, '
                'пришли нам номер в WhatsApp или ник в Telegram:'
                )
        else:
            text = (
                'Error in spelling of contacts.\nPlease '
                'send us the number in WhatsApp or nickname in Telegram:'
            )
        await update.message.reply_text(text=text)
        return WAITING_RECIPIENT_CONTACT

    context.chat_data['recipient_contact'] = recipient_contact
    next_state = await send_successful_booking_message(update, context)
    return next_state


async def send_successful_booking_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send to chat Message about successful booking."""
    if context.chat_data['delivery_method'] == 'courier_delivery':
        recipient_fullname = context.chat_data['recipient_fullname']
        recipient_contact = context.chat_data['recipient_contact']
    else:
        recipient_fullname = context.chat_data['customer_fullname']
        recipient_contact = 'Получателем является заказчик'

    await Database.create_order(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        customer_email='',
        customer_fullname=context.chat_data['customer_fullname'],
        customer_phone=context.chat_data['customer_phone'],
        impression_id=context.chat_data['impression_id'],
        recipient_fullname=recipient_fullname,
        recipient_contact=recipient_contact,
        email_receiving=False,
        delivery_method=context.chat_data['delivery_method']
    )

    if context.chat_data['language'] == 'russian':
        text = (
            'Мы забронировали сертификат ✨\n\n'
            'В ближайшее время тебе напишет оператор'
        )
    else:
        text = (
            "We've booked the certificate ✨\n\n"
            "An operator will write to you shortly"
        )

    if update.callback_query:
        await update.callback_query.edit_message_text(text=text)
        return DIALOGUE_END

    await update.message.reply_text(text=text)
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


async def handle_self_delivery_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Confirming self-delivery menu."""
    if not update.callback_query:
        text = get_misunderstanding_message(context.chat_data['language'])
        next_state = await send_self_delivery_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'self_delivery_yes':
        next_state = await send_successful_booking_message(update, context)
        return next_state

    if update.callback_query.data == 'self_delivery_no':
        next_state = await send_delivery_methods_menu(update, context)
        return next_state


async def handle_certificate_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Activate certificate button click."""
    if context.chat_data['language'] == 'russian':
        text = (
            'Поздравляем - близкий человек подарил тебе прекрасные '
            'впечатления!\nОкунёмся в мир невероятных эмоций?\n\n'
        )
    else:
        text = (
            "Congratulations - a loved one has given you a wonderful "
            "experience!\nLet's dive into the world of incredible "
            "emotions?\n\n"
        )
    next_state = await send_certificate_id_request(update, context, text)
    return next_state


async def send_certificate_id_request(
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


async def handle_certificate_id_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CERTIFICATE_ID state."""
    certificate_id = update.message.text.strip()
    activation_results = await Database.activate_certificate(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        certificate_id=certificate_id
    )
    if activation_results['availability']:
        next_state = await send_good_certificate_message(
            update,
            context,
            activation_results['impression_name']
        )
        return next_state

    next_state = await send_wrong_certificate_menu(update, context)
    return next_state


async def send_good_certificate_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    impression_name: str
) -> int:
    """Send to chat menu for case of correct certificate ID."""
    if context.chat_data['language'] == 'russian':
        text = normalise_text(
            'Твое впечатление это -\n'
            f'*{impression_name}*\n'
            'Прекрасный выбор!\n\n'
            'В течение часа с тобой свяжется оператор\n'
            'и расскажет все детали.\n'
            'До скорых встреч ✋'
        )
    else:
        text = normalise_text(
            'Your impression is\n'
            f'*{impression_name}*\n'
            'Excellent choice!\n\n'
            'An operator will contact you within an hour\n'
            'with all the details.\n'
            'See you soon ✋'
        )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            parse_mode='MarkdownV2'
        )
        return DIALOGUE_END

    await update.message.reply_text(text=text, parse_mode='MarkdownV2')
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
        buttons = ['Ввести ID снова', 'Позвать человека']
    else:
        text_beginning = text if text else 'Something went wrong\n'
        text = (
            f'{text_beginning}Please check if you have entered the ID '
            'correctly and if the certificate expiry date is valid\n\n'
            'If you need help, click the "Call Person" button'
        )
        buttons = ['Enter ID again', 'Call Person']

    keyboard = [[
        InlineKeyboardButton(buttons[0], callback_data='certificate_id'),
        InlineKeyboardButton(buttons[1], callback_data='call_person')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=reply_markup
        )
        return WRONG_CERTIFICATE_MENU

    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return WRONG_CERTIFICATE_MENU


async def handle_wrong_certificate_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Wrong certificate menu."""
    if not update.callback_query:
        text = get_misunderstanding_message(context.chat_data['language'])
        next_state = await send_wrong_certificate_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'certificate_id':
        next_state = await send_certificate_id_request(update, context)
        return next_state

    if update.callback_query.data == 'call_person':
        context.chat_data['request_type'] = 'activation_problem'
        next_state = await send_calling_person_message(update, context)
        return next_state


async def send_calling_person_message(
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
    else:
        text = 'Thank you for contacting us, support will respond shortly'

    if update.callback_query:
        await update.callback_query.edit_message_text(text)
        return DIALOGUE_END

    await update.message.reply_text(text=text)
    return DIALOGUE_END


async def send_questions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str = ''
) -> int:
    """Handle the FAQ button click."""
    faq_details = await Database.get_faq_details(
        context.chat_data['language']
    )

    keyboard = []
    buttons_in_row = calculate_buttons_in_row(buttons_count=len(faq_details))
    for question_index, faq_detail in enumerate(faq_details):
        text += f"{question_index+1}. {faq_detail['question']}\n"
        if not (question_index % buttons_in_row):
            keyboard.append([])
        keyboard[-1].append(
            InlineKeyboardButton(
                f"{question_index+1}",
                callback_data=f"{faq_detail['id']}"
            )
        )

    if context.chat_data['language'] == 'russian':
        text += (
            '\nВыбери вопрос и нажми на кнопку с его номером:\n'
            if faq_details
            else 'Извини, FAQ пока пусто.\n'
        )
        buttons = ['Позвать человека', '« Вернуться в главное меню']
    else:
        text += (
            "\nClick on the button with the question number:\n"
            if faq_details
            else 'Sorry, the FAQ is empty for now.\n'
        )
        buttons = ['Call Person', '« Back to main menu']

    keyboard.append(
        [InlineKeyboardButton(buttons[0], callback_data='call_person')]
    )
    keyboard.append(
        [InlineKeyboardButton(buttons[1], callback_data='main_menu')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
        return SELECTING_QUESTION

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    return SELECTING_QUESTION


async def handle_questions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Question selecting."""
    if not update.callback_query:
        if context.chat_data['language'] == 'russian':
            text = (
                'Извини, непонятно, какой вопрос ты хочешь '
                'выбрать. Попробуй ещё раз.\n\n'
            )
        else:
            text = (
                "Sorry, it's not clear which question you want to "
                "choose. Try again.\n\n"
            )

        next_state = await send_questions_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    if update.callback_query.data == 'call_person':
        context.chat_data['request_type'] = 'question_for_operator'
        next_state = await send_calling_person_message(update, context)
        return next_state

    next_state = await send_answer_menu(update, context)
    return next_state


async def send_answer_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send a chat message when calling a person."""
    faq_detail = await Database.get_faq_detail(
        faq_id=update.callback_query.data,
        language=context.chat_data['language']
    )
    text = normalise_text(
        f"*{faq_detail['question']}*\n\n{faq_detail['answer']}"
    )

    if context.chat_data['language'] == 'russian':
        buttons = [
            '‹ Вернуться к списку вопросов',
            '« Вернуться в главное меню'
        ]
    else:
        buttons = ['‹ Back to list of questions', '« Back to main menu']

    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data='questions_list')],
        [InlineKeyboardButton(buttons[1], callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
        return ANSWER_MENU

    await update.message.reply_text(
        text=text,
        parse_mode='MarkdownV2',
        reply_markup=reply_markup
    )
    return ANSWER_MENU


async def handle_answer_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Answer menu."""
    if not update.callback_query:
        text = get_misunderstanding_message(context.chat_data['language'])
        next_state = await send_answer_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    if update.callback_query.data == 'questions_list':
        next_state = await send_questions_menu(update, context)
        return next_state


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

    application.add_handler(CallbackQueryHandler(handle_users_reply))
    application.add_handler(MessageHandler(filters.TEXT, handle_users_reply))
    application.add_handler(MessageHandler(filters.PHOTO, handle_users_reply))
    application.add_handler(CommandHandler('start', handle_users_reply))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impressions.settings')
    django.setup()

    from bot.persistence import DjangoPersistence
    from bot.database import Database
    main()
