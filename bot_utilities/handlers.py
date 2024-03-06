# coding=utf-8
"""Handle all the actions of the wishlist-shop telegram bot."""
import io
import os
import re

import django
import phonenumbers
from telegram import (
    # InlineKeyboardButton,
    # InlineKeyboardMarkup,
    Update
)
from telegram.ext import ContextTypes

from .errors import (
    send_fullname_error_message, send_name_error_message,
    send_phone_error_message
)
from .history import (
    add_message_to_history, clear_history, delete_last_history_message
)
from .invitations import (
    send_certificate_id_invitation, send_customer_fullname_invitation,
    send_payment_invitation, send_customer_phone_invitation,
    send_recipient_contact_invitation, send_recipient_name_invitation
)
from .menus import (
    send_calling_person_menu, send_customer_confirmation_menu,
    send_delivery_methods_menu, send_faq_menu, send_good_certificate_menu,
    send_impressions_categories_menu, send_impressions_menu,
    send_language_menu, send_main_menu, send_privacy_policy_menu,
    send_receiving_methods_menu, send_recipient_confirmation_menu,
    send_screenshot_receiving_menu, send_self_delivery_menu,
    send_successful_booking_menu, send_wrong_certificate_menu
)
from .messages import get_misunderstanding_message

from .states import (
    START, SELECTING_LANGUAGE, MAIN_MENU, SELECTING_IMPRESSIONS_CATEGORY,
    SELECTING_IMPRESSION, SELECTING_RECEIVING_METHOD, WAITING_CUSTOMER_EMAIL,
    ACQUAINTED_PRIVACY_POLICY, WAITING_CUSTOMER_FULLNAME,
    WAITING_CUSTOMER_PHONE, WAITING_CUSTOMER_CONFIRMATION,
    WAITING_PAYMENT_SCREENSHOT, DIALOGUE_END, SELECTING_DELIVERY_METHOD,
    WAITING_RECIPIENT_NAME, WAITING_RECIPIENT_CONTACT,
    WAITING_RECIPIENT_CONFIRMATION, CONFIRMING_SELF_DELIVERY,
    WAITING_CERTIFICATE_ID, WRONG_CERTIFICATE_MENU, SELECTING_QUESTION
)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impressions.settings')
django.setup()

from bot.database import Database  # noqa: E402


async def handle_all_actions(
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
        WAITING_CUSTOMER_CONFIRMATION: handle_customer_confirmation,
        WAITING_PAYMENT_SCREENSHOT: handle_payment_screenshot,
        DIALOGUE_END: handle_dialogue_end,
        SELECTING_DELIVERY_METHOD: handle_delivery_methods_menu,
        WAITING_RECIPIENT_NAME: handle_recipient_name_message,
        WAITING_RECIPIENT_CONTACT: handle_recipient_contact_message,
        WAITING_RECIPIENT_CONFIRMATION: handle_recipient_confirmation,
        CONFIRMING_SELF_DELIVERY: handle_self_delivery_menu,
        WAITING_CERTIFICATE_ID: handle_certificate_id_message,
        WRONG_CERTIFICATE_MENU: handle_wrong_certificate_menu,
        SELECTING_QUESTION: handle_faq_menu
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
    await clear_history(update, context)
    context.chat_data.clear()
    context.chat_data['messages_history'] = []

    next_state = await send_language_menu(update, context)
    return next_state


async def handle_language_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Language selecting menu."""
    if not update.callback_query:
        next_state = await handle_start_command(update, context)
        return next_state

    await update.callback_query.answer()
    context.chat_data['language'] = update.callback_query.data

    next_state = await send_main_menu(update, context)
    return next_state


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
        next_state = await send_faq_menu(update, context)
        return next_state


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

    next_state = await send_impressions_menu(update, context)
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


async def handle_impressions_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Impression selecting."""
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == 'category_menu':
            next_state = await send_impressions_categories_menu(
                update, context
            )
            return next_state

        next_state = await handle_unrecognized_impression(update, context)
        return next_state

    impression_number = update.message.text.strip()
    if not impression_number.isnumeric():
        next_state = await handle_unrecognized_impression(update, context)
        return next_state

    impression_index = int(impression_number) - 1
    impressions_ids = context.chat_data.get('impressions_ids', [])
    if impression_index < 0 or len(impressions_ids) <= impression_index:
        next_state = await handle_unrecognized_impression(update, context)
        return next_state

    impression_id = impressions_ids[impression_index]
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
        next_state = await send_impressions_categories_menu(update, context)
        return next_state

    if update.callback_query.data == 'email':
        next_state = await handle_email_button(update, context)
        return next_state

    if update.callback_query.data == 'gift_box':
        next_state = await handle_giftbox_button(update, context)
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
    message = await update.callback_query.edit_message_text(text=text)
    add_message_to_history(context, message)
    return WAITING_CUSTOMER_EMAIL


async def handle_customer_email_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_EMAIL state."""
    add_message_to_history(context, update.message)

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

        message = await update.message.reply_text(text=text)
        add_message_to_history(context, message)
        return WAITING_CUSTOMER_EMAIL

    context.chat_data['customer_email'] = match.groups()[0]
    next_state = await send_privacy_policy_menu(update, context)
    return next_state


async def handle_giftbox_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Gift-box button click."""
    context.chat_data['receiving_method'] = 'gift_box'
    next_state = await send_privacy_policy_menu(update, context)
    return next_state


async def handle_privacy_policy_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Privacy Policy button click."""
    if not update.callback_query:
        next_state = await send_privacy_policy_menu(update, context)
        return next_state

    await clear_history(update, context)
    next_state = await send_customer_fullname_invitation(update, context)
    return next_state


async def handle_customer_fullname_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_FULLNAME state."""
    add_message_to_history(context, update.message)

    customer_fullname = update.message.text.strip()
    if len(customer_fullname) < 4 or ' ' not in customer_fullname:
        next_state = await send_fullname_error_message(update, context)
        return next_state

    context.chat_data['customer_fullname'] = customer_fullname
    next_state = await send_customer_phone_invitation(update, context)
    return next_state


async def handle_customer_phone_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_PHONE state."""
    add_message_to_history(context, update.message)

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
        next_state = await send_phone_error_message(update, context)
        return next_state

    context.chat_data['customer_phone'] = (
        f'+{value.country_code}{value.national_number}'
    )

    next_state = await send_customer_confirmation_menu(update, context)
    return next_state


async def handle_customer_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CUSTOMER_CONFIRMATION state."""
    if not update.callback_query:
        await context.bot.delete_message(
            update.effective_chat['id'],
            update.message.message_id
        )
        await delete_last_history_message(update, context)

        if context.chat_data['language'] == 'russian':
            text = (
                "Извини, непонятно, подтверждаешь ли ты, что верно ввёл свои "
                "ФИО и номер телефона.\n"
                "Нужно нажать на соответствующую кнопку.\n\n"
            )
        else:
            text = (
                "Sorry, it's not clear if you are confirming that you have "
                "entered your full name and phone number correctly.\n"
                "You need to click the appropriate button.\n\n"
            )
        next_state = await send_customer_confirmation_menu(
            update, context, text
        )
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'right_customer':
        if context.chat_data['receiving_method'] == 'email':
            await clear_history(update, context, last_message_deletion=False)
            next_state = await send_payment_invitation(update, context)
            return next_state

        next_state = await send_delivery_methods_menu(update, context)
        return next_state

    if update.callback_query.data == 'wrong_customer':
        if context.chat_data['language'] == 'russian':
            text = "Исправление данных:"
        else:
            text = "Correction of data:"

        message = await update.callback_query.edit_message_text(
            text=text,
            reply_markup=None,
        )
        add_message_to_history(context, message)

        next_state = await send_customer_fullname_invitation(
            update, context
        )
        return next_state


async def handle_payment_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle receipt of screenshot of payment."""
    add_message_to_history(context, update.message)
    if not update.message.photo:
        if context.chat_data['language'] == 'russian':
            text = 'Ты прислал не скриншот оплаты.\n\n'
        else:
            text = (
                "You didn't send a screenshot "
                "of the payment\n\n"
            )
        next_state = await send_payment_invitation(update, context, text)
        return next_state

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
        recipient_name=context.chat_data['customer_fullname'],
        recipient_contact='Получателем является заказчик',
        email_receiving=True,
        screenshot_stream=screenshot_stream
    )

    next_state = await send_screenshot_receiving_menu(update, context)
    return next_state


async def handle_dialogue_end(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle end of dialogue."""
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == 'main_menu':
            await clear_history(update, context, last_message_deletion=False)
            next_state = await send_main_menu(update, context)
            return next_state
    return 0


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
        await clear_history(update, context)
        next_state = await send_recipient_name_invitation(
            update, context
        )
        return next_state

    if update.callback_query.data == 'self_delivery':
        next_state = await send_self_delivery_menu(update, context)
        return next_state


async def handle_recipient_name_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_RECIPIENT_NAME state."""
    add_message_to_history(context, update.message)

    recipient_name = update.message.text.strip()
    if len(recipient_name) < 2:
        next_state = await send_name_error_message(update, context)
        return next_state

    context.chat_data['recipient_name'] = recipient_name
    next_state = await send_recipient_contact_invitation(update, context)
    return next_state


async def handle_recipient_contact_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_RECIPIENT_CONTACT state."""
    add_message_to_history(context, update.message)

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
        message = await update.message.reply_text(text=text)
        add_message_to_history(context, update.message)
        return WAITING_RECIPIENT_CONTACT

    context.chat_data['recipient_contact'] = recipient_contact
    next_state = await send_recipient_confirmation_menu(update, context)
    return next_state


async def handle_recipient_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_RECIPIENT_CONFIRMATION state."""
    if not update.callback_query:
        await context.bot.delete_message(
            update.effective_chat['id'],
            update.message.message_id
        )
        await delete_last_history_message(update, context)

        if context.chat_data['language'] == 'russian':
            text = (
                "Извини, непонятно, подтверждаешь ли ты, что верно ввёл "
                "имя и контакт получателя.\n"
                "Нужно нажать на соответствующую кнопку.\n\n"
            )
        else:
            text = (
                "Sorry, it's not clear if you are confirming that you have "
                "entered the recipient's name and contact correctly.\n"
                "You need to click the appropriate button.\n\n"
            )
        next_state = await send_recipient_confirmation_menu(
            update, context, text
        )
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'right_recipient':
        await clear_history(update, context, last_message_deletion=False)
        next_state = await send_successful_booking_menu(update, context)
        return next_state

    if update.callback_query.data == 'wrong_recipient':
        if context.chat_data['language'] == 'russian':
            text = "Исправление данных:"
        else:
            text = "Correction of data:"

        message = await update.callback_query.edit_message_text(
            text=text,
            reply_markup=None,
        )
        add_message_to_history(context, message)

        next_state = await send_recipient_name_invitation(
            update, context
        )
        return next_state


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
        next_state = await send_successful_booking_menu(update, context)
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
    next_state = await send_certificate_id_invitation(update, context, text)
    return next_state


async def handle_certificate_id_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the WAITING_CERTIFICATE_ID state."""
    add_message_to_history(context, update.message)

    certificate_id = update.message.text.strip()
    activation_results = await Database.activate_certificate(
        chat_id=update.effective_chat['id'],
        tg_username=update.effective_chat['username'],
        language=context.chat_data['language'],
        certificate_id=certificate_id
    )
    if activation_results['availability']:
        next_state = await send_good_certificate_menu(
            update,
            context,
            activation_results['impression_name']
        )
        return next_state

    next_state = await send_wrong_certificate_menu(update, context)
    return next_state


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
        next_state = await send_certificate_id_invitation(update, context)
        return next_state

    if update.callback_query.data == 'call_person':
        context.chat_data['request_type'] = 'activation_problem'
        next_state = await send_calling_person_menu(update, context)
        return next_state

    if update.callback_query.data == 'main_menu':
        await clear_history(update, context, last_message_deletion=False)
        next_state = await send_main_menu(update, context)
        return next_state


async def handle_faq_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle Question selecting."""
    if not update.callback_query:
        if context.chat_data['language'] == 'russian':
            text = (
                'Извини, непонятно, что ты хочешь выбрать. '
                'Нажми на кнопку.\n\n'
            )
        else:
            text = (
                "Sorry, it's not clear what you want to choose. "
                "Click on the button.\n\n"
            )

        next_state = await send_faq_menu(update, context, text)
        return next_state

    await update.callback_query.answer()

    if update.callback_query.data == 'main_menu':
        next_state = await send_main_menu(update, context)
        return next_state

    if update.callback_query.data == 'call_person':
        context.chat_data['request_type'] = 'question_for_operator'
        next_state = await send_calling_person_menu(update, context)
        return next_state
