from aiogram import Router, types
from aiogram.dispatcher.filters import Text

from data import texts

router = Router()


@router.message(Text(text_contains="помощь", text_ignore_case=True))
@router.message(commands={"help"})
async def help_handler(message: types.Message):
    await message.answer(
        text=texts.faq,
        disable_web_page_preview=True
    )
    await message.answer(
        text=texts.termines,
        disable_web_page_preview=True
    )
