import io
from asgiref.sync import sync_to_async
from datetime import datetime
from typing import Dict, List
from pytz import timezone

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import (
    BotData,
    Certificate,
    Customer,
    Faq,
    Impression,
    Order,
    SupportApplication
)


class Database():
    """Transfer data asynchronously between the database and the bot."""
    @sync_to_async
    def activate_certificate(
        self,
        chat_id: int,
        tg_username: str,
        language: str,
        certificate_id: int
    ) -> Dict:
        """Activate Certificate if available."""
        certificate = Certificate.objects.filter(
            certificate_id=int(certificate_id)
        ).select_related('impression').first()

        today_datetime = datetime.now(tz=timezone(settings.TIME_ZONE))
        today_date = today_datetime.date()

        availability = (
            certificate and
            not certificate.activated_at and
            not certificate.blocked and
            not certificate.used and
            certificate.start_date <= today_date and
            certificate.expiry_date >= today_date
        )
        if not availability:
            return {'availability': False}

        certificate.activated_at = today_datetime
        certificate.save()

        application_language = (
            SupportApplication.RUSSIAN_LANGUAGE
            if language == 'russian'
            else SupportApplication.ENGLISH_LANGUAGE
        )
        SupportApplication.objects.create(
            chat_id=int(chat_id),
            tg_username=tg_username,
            language=application_language,
            request_type=SupportApplication.SUCCESSFUL_ACTIVATION,
            certificate=certificate
        )
        impression_name = (
            certificate.impression.name
            if language == 'russian'
            else certificate.impression.english_name
        )

        return {
            'availability': availability,
            'impression_name': impression_name
        }

    @sync_to_async
    def create_order(
        self,
        chat_id: int,
        tg_username: str,
        language: str,
        customer_email: str,
        customer_fullname: str,
        customer_phone: str,
        impression_id: int,
        recipient_name: str,
        recipient_contact: str,
        email_receiving: bool,
        delivery_method: str = '',
        screenshot_stream: io.BytesIO = None
    ) -> None:
        """Create Order."""
        impression = Impression.objects.get(pk=impression_id)
        order_language = (
            Order.RUSSIAN_LANGUAGE
            if language == 'russian'
            else Order.ENGLISH_LANGUAGE
        )
        customer, _ = Customer.objects.update_or_create(
            chat_id=int(chat_id),
            defaults={
                'tg_username': tg_username,
                'email': customer_email,
                'fullname': customer_fullname,
                'phone': customer_phone
            }
        )
        receiving_method = Order.EMAIL if email_receiving else Order.GIFT_BOX
        if delivery_method == 'courier_delivery':
            delivery_method = Order.COURIER_DELIVERY
        elif delivery_method == 'self_delivery':
            delivery_method = Order.SELF_DELIVERY
        else:
            delivery_method = Order.NOT_SPECIFIED

        order = Order.objects.create(
            impression=impression,
            language=order_language,
            customer=customer,
            recipient_name=recipient_name,
            recipient_contact=recipient_contact,
            receiving_method=receiving_method,
            delivery_method=delivery_method
        )

        if screenshot_stream:
            screenshot_filename = f'{order.id}.jpg'
            screenshot_file = InMemoryUploadedFile(
                screenshot_stream,
                field_name='payment_screenshot',
                name=screenshot_filename,
                content_type='image/jpeg',
                size=screenshot_stream.getbuffer().nbytes,
                charset=None
            )
            order.payment_screenshot = screenshot_file
            order.save()

        application_language = (
            SupportApplication.RUSSIAN_LANGUAGE
            if language == 'russian'
            else SupportApplication.ENGLISH_LANGUAGE
        )
        request_type = (
            SupportApplication.EMAIL_ORDER
            if email_receiving
            else SupportApplication.GIFTBOX_ORDER
        )
        SupportApplication.objects.create(
            chat_id=chat_id,
            tg_username=tg_username,
            language=application_language,
            request_type=request_type,
            order=order
        )

    @sync_to_async
    def create_support_application(
        self,
        chat_id: int,
        tg_username: str,
        language: str,
        request_type: str
    ) -> None:
        """Create SupportApplication."""
        application_language = (
            SupportApplication.RUSSIAN_LANGUAGE
            if language == 'russian'
            else SupportApplication.ENGLISH_LANGUAGE
        )
        application_request_type = (
            SupportApplication.ACTIVATION_PROBLEM
            if request_type == 'activation_problem'
            else SupportApplication.QUESTION_FOR_OPERATOR
        )
        SupportApplication.objects.create(
            chat_id=int(chat_id),
            tg_username=tg_username,
            language=application_language,
            request_type=application_request_type,
        )

    @sync_to_async
    def get_faq_details(self, language: str) -> List[Dict]:
        """Get faq questions from database."""
        faq_details = Faq.objects.filter(availability=True)
        if language == 'russian':
            return [
                {
                    'question': faq_detail.russian_question,
                    'url': faq_detail.russian_url
                }
                for faq_detail in faq_details
            ]

        return [
            {
                'question': faq_detail.english_question,
                'url': faq_detail.english_url
            }
            for faq_detail in faq_details
        ]

    @sync_to_async
    def get_impression(self, impression_id: int, language: str) -> Dict:
        """Get impression from database."""
        impression = Impression.objects.filter(
            id=int(impression_id)
        ).first()
        if not impression:
            return {}

        if language == 'russian':
            return {
                'id': impression.id,
                'name': impression.name,
                'price': f'{impression.price_in_rubles} ₽'
            }
        return {
            'id': impression.id,
            'name': impression.english_name,
            'price': f'{impression.price_in_euros} €'
        }

    @sync_to_async
    def get_impressions(
        self,
        language: str,
        impressions_category: str
    ) -> List[Dict]:
        """Get impressions from database."""
        if impressions_category == 'man':
            impressions = Impression.objects.filter(for_men=True)
        elif impressions_category == 'girl':
            impressions = Impression.objects.filter(for_girls=True)
        elif impressions_category == 'couple':
            impressions = Impression.objects.filter(for_couples=True)
        elif impressions_category == 'all':
            impressions = Impression.objects.filter(for_all=True)
        else:
            return []

        if language == 'russian':
            return [
                {
                    'id': impression.id,
                    'name': impression.name,
                    'price': f'{impression.price_in_rubles} ₽',
                    'url': impression.url_for_russians
                }
                for impression in impressions
            ]

        return [
            {
                'id': impression.id,
                'name': impression.english_name,
                'price': f'{impression.price_in_euros} €',
                'url': impression.url_for_english
            }
            for impression in impressions
        ]

    @sync_to_async
    def get_payment_details(self, language: str) -> str:
        """Get payment details from database."""
        bot = BotData.objects.all()
        if language == 'russian':
            return bot[0].russian_payment_details

        return bot[0].english_payment_details

    @sync_to_async
    def get_policy_url(self, language: str) -> str:
        """Get Privacy policy url from database."""
        bot = BotData.objects.all()
        if language == 'russian':
            return bot[0].russian_policy_url

        return bot[0].english_policy_url

    @sync_to_async
    def get_self_delivery_point(self, language: str) -> Dict:
        """Get details of self-delivery point from database."""
        bot = BotData.objects.all()
        if language == 'russian':
            return {
                'address': bot[0].russian_self_delivery_address,
                'opening_hours': bot[0].russian_self_delivery_hours
            }

        return {
            'address': bot[0].english_self_delivery_address,
            'opening_hours': bot[0].english_self_delivery_hours
        }
