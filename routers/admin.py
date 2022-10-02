from asyncio import sleep
from datetime import timedelta

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError
from loguru import logger

from routers.filters import IsAdminFilter
from data import texts
from data.states import Mailing
from data.keyboards import delete_markup, mail_sure_markup
from models import User, get_datetime_now, ALL_BANNED
from config import bot, dp

router = Router()
router.observers['message'].bind_filter(IsAdminFilter)


@router.message(commands={"mail", "mailing"})
async def mailing_handler(message: types.Message, state: FSMContext):
    await message.answer(text=texts.mailing_post, reply_markup=delete_markup)
    await state.set_state(Mailing.post)


@router.message(Mailing.post)
async def mailing_post_handler(message: types.Message, state: FSMContext):
    try:
        text = message.html_text
    except TypeError:
        text = None

    photo = None
    video = None
    if message.photo:
        photo = message.photo[-1].file_id
    if message.video:
        video = message.video.file_id

    await state.update_data(text=text, video=video, photo=photo)
    await state.set_state(Mailing.sure)
    await message.answer(text=texts.mail_sure, reply_markup=mail_sure_markup)


@router.callback_query(Mailing.sure, text="mailsure")
async def mailing_send_post(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    logger.debug(data)
    await state.clear()

    msg_count = 0
    block_count = 0
    error_count = 0
    for user in User.select():
        await sleep(0.2)
        try:
            if data["photo"]:
                await bot.send_photo(
                    chat_id=user.user_id,
                    photo=data["photo"],
                    caption=data["text"]
                )
            elif data["video"]:
                await bot.send_video(
                    chat_id=user.user_id,
                    video=data["video"],
                    caption=data["text"]
                )
            else:
                await bot.send_message(
                    chat_id=user.user_id,
                    text=data["text"]
                )
            msg_count += 1
        except TelegramForbiddenError as ex:
            block_count += 1
            logger.error(ex)
        except Exception as ex:
            error_count += 1
            logger.error(ex)

        await query.message.edit_text(
            text=texts.mail.format(
                msg_count=msg_count,
                block_count=block_count,
                error_count=error_count,
                last_update=get_datetime_now().strftime("%H:%M:%S"),
            )
        )

    await query.message.reply(
        text=texts.mail_end
    )


@router.callback_query(text="mailsure", state="*")
async def mailing_sure_invalid(query: types.CallbackQuery):
    await query.answer(text="Ошибка, данные стёрты!", show_alert=True)
    await query.message.delete()


@router.message(commands={'admin'})
async def admin_help(message: types.Message, state: FSMContext):
    await message.answer('Команды админа:\n'
                         '👋 /mail, /mailing - сделать рассылку\n'
                         '🗑 /cleardb - очистить старые данные в бд'
                         )


@router.message(commands={'cleardb'})
async def clear_db_handler(message: types.Message, state: FSMContext):
    now = get_datetime_now() - timedelta(days=30)
    count = 0
    for banned_model in ALL_BANNED:
        count += banned_model.delete().where(banned_model.created < now).execute()
    await message.answer('Старые записи из бд успешно удалены\n'
                         f'Всего удалено: {count}')
