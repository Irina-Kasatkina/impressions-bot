from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class BotData(models.Model):
    bot_name = models.CharField('Название бота', max_length=256)
    english_bot_name = models.CharField(
        'Название бота по-английски',
        max_length=256
    )
    russian_policy_url = models.URLField(
        'Url Политики конфиденциальности на русском',
        blank=True
    )
    english_policy_url = models.URLField(
        'Url Политики конфиденциальности на английском',
        blank=True
    )
    russian_payment_details = models.TextField(
        'Реквизиты для оплаты сертификата (на русском)',
        blank=True
    )
    english_payment_details = models.TextField(
        'Реквизиты для оплаты сертификата (на английском)',
        blank=True
    )
    russian_self_delivery_address = models.CharField(
        'Адрес пункта самовывоза по-русски',
        max_length=256,
        blank=True
    )
    russian_self_delivery_hours = models.CharField(
        'Время работы самовывоза по-русски',
        max_length=256,
        blank=True
    )
    english_self_delivery_address = models.CharField(
        'Адрес пункта самовывоза по-английски',
        max_length=256,
        blank=True
    )
    english_self_delivery_hours = models.CharField(
        'Время работы самовывоза по-английски',
        max_length=256,
        blank=True
    )

    class Meta:
        verbose_name = 'бот'
        verbose_name_plural = 'боты'


class ChatData(models.Model):
    chat_id = models.PositiveBigIntegerField(
        'ID чата',
        primary_key=True,
        null=False,
        blank=False
    )
    start_at = models.DateTimeField(
        'Впервые обратился к боту',
        auto_now_add=True,
    )
    called_at = models.DateTimeField(
        'Последний раз общался с ботом',
        auto_now=True,
        db_index=True,
    )
    data = models.JSONField()

    class Meta:
        ordering = ['-called_at']
        verbose_name = 'чат'
        verbose_name_plural = 'чаты'


class Impression(models.Model):
    number = models.PositiveIntegerField(r'№ п/п', unique=True)
    name = models.CharField('Наименование по-русски', max_length=256)
    english_name = models.CharField(
        'Наименование по-английски',
        max_length=256
    )
    price_in_rubles = models.PositiveIntegerField('Цена в рублях')
    price_in_euros = models.PositiveIntegerField('Цена в Евро')
    url_for_russians = models.URLField('Url русского описания', blank=True)
    url_for_english = models.URLField('Url английского описания', blank=True)
    for_men = models.BooleanField('Для мужчин', default=False)
    for_girls = models.BooleanField('Для девушек', default=False)
    for_couples = models.BooleanField('Для пар', default=False)
    for_all = models.BooleanField('Для всех', default=False)

    class Meta:
        ordering = ['number']
        verbose_name = 'впечатление'
        verbose_name_plural = 'впечатления'


class Customer(models.Model):
    chat_id = models.PositiveBigIntegerField(
        'ID чата',
        primary_key=True,
        null=False,
        blank=False
    )
    registered_at = models.DateTimeField('Зарегистрирован', auto_now_add=True)
    tg_username = models.CharField('Ник в Telegram', max_length=256)
    email = models.EmailField('Email', default='', blank=True)
    fullname = models.CharField('Фамилия и имя', max_length=256)
    phone = PhoneNumberField(
        'Нормализованный номер телефона',
        blank=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'заказчик'
        verbose_name_plural = 'заказчики'


class Order(models.Model):
    RUSSIAN_LANGUAGE = 'RU'
    ENGLISH_LANGUAGE = 'EN'
    LANGUAGES = [
        (RUSSIAN_LANGUAGE, 'Русский'),
        (ENGLISH_LANGUAGE, 'English'),
    ]

    EMAIL = 'EM'
    GIFT_BOX = 'GB'
    RECEIVING_METHODS = [
        (EMAIL, 'По email'),
        (GIFT_BOX, 'В подарочной коробке')
    ]

    COURIER_DELIVERY = 'CD'
    SELF_DELIVERY = 'SD'
    NOT_SPECIFIED = 'NS'
    DELIVERY_METHODS = [
        (COURIER_DELIVERY, 'Доставка курьером'),
        (SELF_DELIVERY, 'Самовывоз'),
        (NOT_SPECIFIED, 'Не указан')
    ]

    number = models.CharField(
        'Номер заказа', max_length=128, default='', blank=True
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    impression = models.ForeignKey(
        Impression,
        on_delete=models.PROTECT,
        verbose_name='Впечатление',
        related_name='orders',
    )
    language = models.CharField(
        'Язык',
        max_length=2,
        choices=LANGUAGES,
        default=RUSSIAN_LANGUAGE
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        verbose_name='Заказчик',
        related_name='orders',
    )
    recipient_fullname = models.CharField(
        'Фамилия и имя адресата',
        max_length=256
    )
    recipient_contact = models.CharField('Контакты адресата', max_length=256)
    receiving_method = models.CharField(
        'Способ получения',
        max_length=2,
        choices=RECEIVING_METHODS
    )
    delivery_method = models.CharField(
        'Способ доставки',
        max_length=2,
        choices=DELIVERY_METHODS,
        default=NOT_SPECIFIED
    )
    delivery_address = models.CharField(
        'Адрес доставки', max_length=512, default='', blank=True
    )
    payment_screenshot = models.ImageField(
        'Скриншот оплаты', upload_to='payment_screenshots',
        null=True, blank=True
    )
    confirmed = models.BooleanField('Оплата подтверждена', default=False)
    given_for_delivery = models.BooleanField(
        'Передан в доставку',
        default=False
    )
    delivered = models.BooleanField('Доставлен', default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class Certificate(models.Model):
    certificate_id = models.IntegerField('ID сертификата', unique=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    start_date = models.DateField('Начинает действовать')
    expiry_date = models.DateField('Заканчивает действовать')
    impression = models.ForeignKey(
        Impression,
        on_delete=models.PROTECT,
        verbose_name='Впечатление',
        related_name='certificates',
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        verbose_name='Заказ',
        related_name='certificate',
    )
    activated_at = models.DateTimeField('Активирован', null=True, blank=True)
    blocked = models.BooleanField('Заблокирован оператором', default=False)
    used = models.BooleanField('Использован', default=False)

    class Meta:
        ordering = ['-expiry_date']
        verbose_name = 'сертификат'
        verbose_name_plural = 'сертификаты'


class SupportApplication(models.Model):
    RUSSIAN_LANGUAGE = 'RU'
    ENGLISH_LANGUAGE = 'EN'
    LANGUAGES = [
        (RUSSIAN_LANGUAGE, 'Русский'),
        (ENGLISH_LANGUAGE, 'English'),
    ]

    EMAIL_ORDER = 'EO'
    GIFTBOX_ORDER = 'GO'
    SUCCESSFUL_ACTIVATION = 'SA'
    ACTIVATION_PROBLEM = 'AP'
    QUESTION_FOR_OPERATOR = 'QO'
    REQUEST_TYPES = [
        (EMAIL_ORDER, 'Новый заказ с получением по email'),
        (GIFTBOX_ORDER, 'Новый заказ с получением в коробке'),
        (SUCCESSFUL_ACTIVATION, 'Успешная активация сертификата'),
        (ACTIVATION_PROBLEM, 'Проблема при активации сертификата'),
        (QUESTION_FOR_OPERATOR, 'Вопрос оператору')
    ]

    registered_at = models.DateTimeField('Зарегистрирована', auto_now_add=True)
    chat_id = models.PositiveBigIntegerField(
        'ID чата',
        null=False,
        blank=False
    )
    tg_username = models.CharField('Ник в Telegram', max_length=256)
    language = models.CharField(
        'Язык',
        max_length=2,
        choices=LANGUAGES,
        default=RUSSIAN_LANGUAGE
    )
    request_type = models.CharField(
        'Тип запроса',
        max_length=2,
        choices=REQUEST_TYPES,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        verbose_name='Заказ',
        related_name='applications',
        null=True
    )
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.PROTECT,
        verbose_name='Сертификат',
        related_name='applications',
        null=True
    )
    accepted = models.BooleanField('Взята в работу', default=False)
    notes = models.TextField('Заметки', default='', blank=True)
    closed = models.BooleanField('Закрыта', default=False)

    class Meta:
        ordering = ['-registered_at']
        verbose_name = 'заявка на поддержку'
        verbose_name_plural = 'заявки на поддержку'


class Faq(models.Model):
    number = models.PositiveIntegerField(r'№ п/п', unique=True)
    russian_question = models.CharField('Вопрос по-русски', max_length=256)
    russian_answer = models.TextField('Ответ по-русски')
    english_question = models.CharField('Вопрос по-английски', max_length=256)
    english_answer = models.TextField('Ответ по-английски')
    availability = models.BooleanField('Доступен в боте', default=True)

    class Meta:
        ordering = ['number']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
