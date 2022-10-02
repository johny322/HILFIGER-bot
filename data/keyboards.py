from datetime import timedelta
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from log import LogModel, encode_log_config
from models import get_datetime_now
from data.texts import config_share

menu_markup = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="👨‍💻 Начать парсинг")],
    [
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="🛠️ Инструменты")
    ],
    [KeyboardButton(text="❓ Помощь")],
], resize_keyboard=True)

settings_markup = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="⛔️ Черный список продавцов"),
        KeyboardButton(text="⛔️ Черный список слов"),
    ],
    [KeyboardButton(text="🔗 Конфигуратор лога")],
    [KeyboardButton(text="🏠 В главное меню")]
], resize_keyboard=True)

parsers_markup = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text='🇧🇪 2DEHANDS.BE',
            callback_data="dehands_start"
        ),
    ],
])

delete_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отмена", callback_data="delete")]
])

confirm_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data='yes'),
            InlineKeyboardButton(text="❌ Нет", callback_data='no')
        ]
    ]
)

cancel_btn = KeyboardButton(text="❌ Отмена")
cancel_markup = ReplyKeyboardMarkup(keyboard=[
    [cancel_btn]
], resize_keyboard=True)
no_cancel_markup = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="no")],
    [cancel_btn]
], resize_keyboard=True)
cancel_parse_markup = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="❌ Завершить парсинг")]
], resize_keyboard=True)


def get_price_markup() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(
                text="1-950",
            ),
        ],
        [
            KeyboardButton(
                text="100-2000",
            ),
        ],
        [
            KeyboardButton(
                text="1-9999999",
            ),
        ], [cancel_btn]
    ], resize_keyboard=True)


def get_currency_markup(currencies):
    keyboard = [[KeyboardButton(text=currency) for currency in currencies]]
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return markup


# 2022/02/26  2022/02/25
# 2022/02/22  2022/02/20
# 2022/02/15.  2022/02/01

def get_post_date_markup() -> ReplyKeyboardMarkup:
    today = get_datetime_now()
    yesterday = today - timedelta(days=1)
    fday = today - timedelta(days=4)
    wday = today - timedelta(days=7)
    twday = today - timedelta(days=12)
    tfday = today - timedelta(days=25)
    return ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(
                text=today.strftime("%Y-%m-%d"),
            ),
            KeyboardButton(
                text=yesterday.strftime("%Y-%m-%d"),
            )
        ],
        [
            KeyboardButton(
                text=fday.strftime("%Y-%m-%d"),
            ),
            KeyboardButton(
                text=wday.strftime("%Y-%m-%d"),
            )
        ],
        [
            KeyboardButton(
                text=twday.strftime("%Y-%m-%d"),
            ),
            KeyboardButton(
                text=tfday.strftime("%Y-%m-%d"),
            )
        ],
        [
            KeyboardButton(
                text="no",
            )
        ],
        [cancel_btn]
    ], resize_keyboard=True)


def get_seller_date_markup() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(
                text="2021-01-01",
            ),
            KeyboardButton(
                text="2019-01-01",
            )
        ],
        [
            KeyboardButton(
                text="2016-01-01",
            ),
            KeyboardButton(
                text="2018-06-15",
            )
        ],
        [
            KeyboardButton(
                text="no",
            )
        ],
        [cancel_btn]
    ], resize_keyboard=True)


def get_light(value: bool):
    return "🟢" if value else "🔴"


def get_log_markup(log: LogModel, bot_username: str) -> InlineKeyboardMarkup:
    config_string = encode_log_config(log)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{get_light(log.photo)} Фото товара",
                callback_data="cfgtoggle:photo"
            ),
            InlineKeyboardButton(
                text=f"{get_light(log.title)} Имя товара",
                callback_data="cfgtoggle:title"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.price)} Цена товара",
                callback_data="cfgtoggle:price"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.location)} Местоположение товара",
                callback_data="cfgtoggle:location"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.description)} Описание товара",
                callback_data="cfgtoggle:description"
            ),
            InlineKeyboardButton(
                text=f"{get_light(log.views)} Просмотры товара",
                callback_data="cfgtoggle:views"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.created)} Дата создания товара",
                callback_data="cfgtoggle:created"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.seller_name)} Имя продавца",
                callback_data="cfgtoggle:seller_name"
            ),
            InlineKeyboardButton(
                text=f"{get_light(log.seller_rate)} Рейтинг продавца",
                callback_data="cfgtoggle:seller_rate"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.posts_count)} Кол-во обьяв продавца",
                callback_data="cfgtoggle:posts_count"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.seller_reg)} Дата регистрации продавца",
                callback_data="cfgtoggle:seller_reg"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{get_light(log.only_with_phone)} Только с телефоном",
                callback_data="cfgtoggle:only_with_phone"
            )
        ],
        [
            InlineKeyboardButton(
                text="Поделиться своим конфигом",
                switch_inline_query=config_share.format(
                    bot_username=bot_username,
                    config_string=config_string
                )
            )
        ],
    ])


def start_parse_markup(parser: str, payload: str = "") -> InlineKeyboardMarkup:
    if payload:
        payload = ":" + payload
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Запустить парсинг",
            callback_data=parser + payload
        )],
        [InlineKeyboardButton(
            text="Пресеты",
            callback_data=parser + "_preset" + payload
        )],
        [InlineKeyboardButton(
            text="Свой текст WhatsApp",
            callback_data=parser + "_texts" + payload
        )],
        [InlineKeyboardButton(
            text="<<",
            callback_data="parse"
        )],
    ])


def texts_markup(parser: str, text_models, payload: str = "") -> InlineKeyboardMarkup:
    if payload:
        payload = ":" + payload
    btns = []
    for txt_model in text_models:
        btns.append([
            InlineKeyboardButton(
                text=txt_model.name,
                callback_data=parser + f"_text:{txt_model.id}" + payload
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        *btns,
        [InlineKeyboardButton(
            text="Создать текст 📝",
            callback_data=parser + "_create_text"
        )],
        [InlineKeyboardButton(
            text="Удалить все текста 🗑",
            callback_data=parser + "_texts_delete" + payload
        )],
        [InlineKeyboardButton(
            text="<<",
            callback_data=parser + "_start" + payload
        )]
    ])


def back_texts_markup(parser: str, payload: str = "") -> InlineKeyboardMarkup:
    if payload:
        payload = ":" + payload
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="<<",
            callback_data=parser + "_texts" + payload
        )]
    ])


mail_sure_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Уверен ✅", callback_data="mailsure")],
    [InlineKeyboardButton(text="Нет ❌", callback_data="delete")],
])


def get_sellers_black_markup(turned: bool) -> InlineKeyboardMarkup:
    status = "🟢 [Вкл.]" if turned else "🔴 [Откл.]"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=status + " Общий список",
            callback_data="toggle_sellers_black"
        )],
        [InlineKeyboardButton(
            text="🗑 Очистить список продавцов",
            callback_data="delete_sellers_black"
        )],
        # share
    ])


def get_words_black_markup(turned: bool) -> InlineKeyboardMarkup:
    status = "🟢" if turned else "🔴"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=status + " Черный список слов",
            callback_data="toggle_words_black"
        )],
        [InlineKeyboardButton(
            text="⏬ Добавить запрещенное слово",
            callback_data="add_black_word"
        )],
        [InlineKeyboardButton(
            text="🗑 Очистить черный список слов",
            callback_data="delete_words_black"
        )],
        # share
    ])


save_preset_markup = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="yes")],
    [KeyboardButton(text="no")],
    [cancel_btn]
], resize_keyboard=True)

parse_business_account = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="yes")],
    [KeyboardButton(text="no")],
    [cancel_btn]
], resize_keyboard=True)

parse_rating = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="1"),
        KeyboardButton(text="2"),
        KeyboardButton(text="3"),

    ],
    [
        KeyboardButton(text="4"),
        KeyboardButton(text="5"),
    ],
    [
        KeyboardButton(text="no")
    ],
    [cancel_btn]
], resize_keyboard=True)


def get_presets_markup(parser: str, presets: Optional[dict] = None, payload: str = "") -> InlineKeyboardMarkup:
    if payload:
        payload = ":" + payload
    btns = []
    if presets:
        for key, val in presets.items():
            btns.append([InlineKeyboardButton(
                text=f"📁 {key}",
                callback_data=parser + f"_run_preset:{val}" + payload
            )])
    return InlineKeyboardMarkup(inline_keyboard=[
        *btns,
        [InlineKeyboardButton(
            text="Удалить определенный пресет",
            callback_data=parser + "_del_preset" + payload
        )],
        [InlineKeyboardButton(
            text="Удалить все пресеты",
            callback_data=parser + "_del_presets" + payload
        )],
        [InlineKeyboardButton(
            text="<<",
            callback_data=parser + "_start" + payload
        )]
    ])


def get_back_parsing_markup(parser: str, payload: str = "") -> InlineKeyboardMarkup:
    if payload:
        payload = ":" + payload
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Назад",
            callback_data=parser + "_start" + payload
        )]
    ])


count_markup = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="20"),
        KeyboardButton(text="50")
    ],
    [
        KeyboardButton(text="70"),
        KeyboardButton(text="100")
    ],
    [cancel_btn]
], resize_keyboard=True)

no_count_markup = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text="20"),
        KeyboardButton(text="50")
    ],
    [
        KeyboardButton(text="70"),
        KeyboardButton(text="100")
    ],
    [KeyboardButton(text="no")],
    [cancel_btn]
], resize_keyboard=True)
