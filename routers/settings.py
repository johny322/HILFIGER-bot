from aiogram import Router, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from config import config
from models import (
    User, BlackWord, ALL_BANNED
)
from data import texts
from data.states import NewBlackWord
from data.keyboards import get_log_markup, settings_markup, \
    get_sellers_black_markup, get_words_black_markup
from log import encode_log_config, decode_log_config

router = Router()


@router.message(Text(text_contains="настройки", text_ignore_case=True))
async def settings_handler(message: types.Message):
    await message.answer(
        text=texts.submenu,
        reply_markup=settings_markup
    )


@router.message(Text(text_contains="конфигуратор лога", text_ignore_case=True))
async def parser_logging_config(message: types.Message):
    user = User.get(user_id=message.from_user.id)
    await message.answer(
        text=texts.parse_config,
        reply_markup=get_log_markup(
            decode_log_config(user.log_config),
            config.bot_username
        )
    )


@router.callback_query(lambda cb: cb.data.split(":")[0] == "cfgtoggle")
async def config_toggle(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    field = query.data.split(":")[1]
    log = decode_log_config(user.log_config)
    setattr(log, field, not getattr(log, field))
    user.log_config = encode_log_config(log)
    user.save()
    await query.message.edit_text(
        text=texts.parse_config,
        reply_markup=get_log_markup(log, "config_bot")
    )


@router.message(Text(text_contains="черный список продавцов", text_ignore_case=True))
async def sellers_black_list(message: types.Message):
    user = User.get(user_id=message.from_user.id)
    count = 0
    for banned_model in ALL_BANNED:
        count += banned_model.select().where(banned_model.owner == user).count()

    await message.answer(
        text=texts.seller_black_list.format(
            sellers_black=count
        ),
        reply_markup=get_sellers_black_markup(user.other_banned)
    )


@router.callback_query(text="toggle_sellers_black")
async def toggle_sellers_black(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    user.other_banned = not user.other_banned
    user.save()
    await query.message.edit_text(
        text=query.message.text,
        reply_markup=get_sellers_black_markup(user.other_banned)
    )


@router.callback_query(text="delete_sellers_black")
async def delete_sellers_black(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    for banned_model in ALL_BANNED:
        banned_model.delete().where(banned_model.owner == user).execute()

    await query.answer("Успешно удалил")
    try:
        await query.message.edit_text(
            text=texts.seller_black_list.format(
                sellers_black=0
            ),
            reply_markup=get_sellers_black_markup(user.other_banned)
        )
    except TelegramBadRequest:
        pass


@router.message(Text(text_contains="черный список слов", text_ignore_case=True))
async def words_black_list(message: types.Message):
    user = User.get(user_id=message.from_user.id)
    user_words = BlackWord.select().where(BlackWord.owner == user)
    words = "\n".join(w.name for w in user_words)
    if not words:
        words = "У вас нет запрещенных слов"
    await message.answer(
        text=texts.word_black_list.format(
            words=words
        ),
        reply_markup=get_words_black_markup(user.black_words)
    )


@router.callback_query(text="toggle_words_black")
async def toggle_words_black(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    user.black_words = not user.black_words
    user.save()
    await query.message.edit_text(
        text=query.message.text,
        reply_markup=get_words_black_markup(user.black_words)
    )


@router.callback_query(text="delete_words_black")
async def delete_words_black(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    BlackWord.delete().where(BlackWord.owner == user).execute()
    words = "У вас нет запрещенных слов"
    await query.answer("Успешно удалил")
    try:
        await query.message.edit_text(
            text=texts.word_black_list.format(
                words=words
            ),
            reply_markup=get_words_black_markup(user.black_words)
        )
    except TelegramBadRequest:
        pass


@router.callback_query(text="add_black_word")
async def add_black_word_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(
        text=texts.new_black_word
    )
    await state.set_state(NewBlackWord.main)


@router.message(NewBlackWord.main)
async def new_black_words(message: types.Message, state: FSMContext):
    user = User.get(user_id=message.from_user.id)
    for word in message.text.split():
        BlackWord.create(
            owner=user,
            name=word
        )
    user_words = BlackWord.select().where(BlackWord.owner == user)
    words = "\n".join(w.name for w in user_words)
    if not words:
        words = "У вас нет запрещенных слов"
    await message.answer(
        text=texts.word_black_list.format(
            words=words
        ),
        reply_markup=get_words_black_markup(user.black_words)
    )
    await state.clear()
