from aiogram import Router, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from loguru import logger

from data import texts
from data.keyboards import menu_markup
from models import User

router = Router()


@router.message(Text(text_contains="завершить парсинг", text_ignore_case=True), state="*")
async def parsing_end_handler(message: types.Message, state: FSMContext):
    logger.debug("Parsing interrupt")
    curr_state = await state.get_state()
    if curr_state:
        if curr_state.split(":")[1] == "cancel":
            await state.clear()
            return

    full_name = message.from_user.first_name
    if message.from_user.last_name:
        full_name += " " + message.from_user.last_name
    try:
        User.get(user_id=message.from_user.id)
    except User.DoesNotExist:
        User.create(
            user_id=message.from_user.id,
            full_name=full_name,
            username=message.from_user.username
        )
    await message.answer(
        text=texts.welcome.format(
            user_id=message.from_user.id,
            full_name=full_name
        ),
        reply_markup=menu_markup
    )
    await state.clear()

