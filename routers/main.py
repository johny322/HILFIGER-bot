from aiogram import Router, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext

from models import User, PreviousPreset, ALL_PRESETS_DICT, BaseModel
from log import decode_log_config, encode_log_config
from data import texts
from data.keyboards import menu_markup, parsers_markup, cancel_markup
from routers.names import PARSERS_FUNCTIONS

router = Router()


@router.callback_query(text="delete")
async def delete_handler(query: types.CallbackQuery, state: FSMContext):
    await query.message.delete()
    await state.clear()


@router.message(commands={"start"})
async def welcome_handler(message: types.Message):
    payload = message.text.split()
    ref_id = None
    new_log = None
    try:
        if payload[1].split("_")[0] == "cfg":
            ref = None
            new_log = decode_log_config(payload[1])
        else:
            ref = User.get(user_id=int(payload[1]))
            ref_id = ref.user_id
    except (IndexError, ValueError, User.DoesNotExist):
        ref = None

    full_name = message.from_user.first_name
    if message.from_user.last_name:
        full_name += " " + message.from_user.last_name
    try:
        user = User.get(user_id=message.from_user.id)
        if new_log is not None:
            user.log_config = encode_log_config(new_log)
            user.save()
            await message.answer(
                text=texts.new_config_log
            )
        if ref:
            if ref.user_id == message.from_user.id:
                await message.answer(
                    text=texts.cannot_self_ref
                )
            else:
                user.referal_id = ref.user_id
                user.save()
                await message.answer(
                    text=texts.you_ref.format(
                        ref_name=f"@{ref.username}" if ref.username else ref.full_name
                    )
                )
    except User.DoesNotExist:
        log_config = "cfg_1_1_1_1_0_0_0_1_0_1_1_1"
        if new_log is not None:
            log_config = encode_log_config(new_log)
        User.create(
            user_id=message.from_user.id,
            full_name=full_name,
            username=message.from_user.username,
            referal_id=ref_id,
            log_config=log_config
        )
    await message.answer(
        text=texts.welcome.format(
            user_id=message.from_user.id,
            full_name=full_name
        ),
        reply_markup=menu_markup
    )


@router.message(Text(text_contains="отмена", text_ignore_case=True))
@router.message(commands={"cancel"}, state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    # await message.answer(text=texts.cancel)
    await state.clear()
    await welcome_handler(message)


@router.message(Text(text_contains="начать парсинг", text_ignore_case=True))
async def start_parse(message: types.Message):
    await message.answer(
        text=texts.choose_parser,
        reply_markup=parsers_markup
    )


@router.message(Text(text_contains="предыдущий парсинг", text_ignore_case=True))
async def start_previous_parse_handler(message: types.Message, state: FSMContext):
    user = User.get(user_id=message.from_user.id)
    try:
        prev_preset = PreviousPreset.get(owner=user)
    except PreviousPreset.DoesNotExist:
        await message.answer(
            text='У вас нет предыдущего парсера'
        )
        return
    market_preset_id = prev_preset.market_preset_id
    market_table_name = prev_preset.market_table_name
    prev_state = prev_preset.prev_state
    preset_table = ALL_PRESETS_DICT.get(market_table_name)
    if not preset_table:
        await message.answer(
            text='Предыдущий парсер не найден'
        )
        return

    preset: BaseModel = preset_table.get(id=market_preset_id)

    prev_state = prev_state.split(':')[0]
    new_state = f'{prev_state}:preset_count'

    await state.update_data(preset=preset, new_state=new_state, prev_state=prev_state, country=prev_preset.country)

    if prev_state in ['ToriFi', 'Olx', 'EbayKleinanzigen']:
        await message.answer(
            text='Отправь токен',
            reply_markup=cancel_markup
        )
        await state.set_state('previous_parse_token')
        return

    await message.answer(
        text=texts.preset_settings.format(
            settings='Имя: <b>{name}</b>'.format(
                name=preset.query,
            )
        ),
        reply_markup=cancel_markup
    )
    await state.set_state('pars_count')


@router.message(state='pars_count')
async def start_previous_parse_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    prev_state = data['prev_state']
    new_state = data['new_state']
    await state.set_state(new_state)

    run_parser_handler = PARSERS_FUNCTIONS.get(prev_state)
    if run_parser_handler is None:
        await message.answer(
            text='Предыдущий парсер не найден'
        )
        return
    await run_parser_handler(message, state)


@router.message(state='previous_parse_token')
async def previous_parse_token_handler(message: types.Message, state: FSMContext):
    token = message.text
    await state.update_data(token=token)
    data = await state.get_data()
    preset = data['preset']

    await message.answer(
        text=texts.preset_settings.format(
            settings='Имя: <b>{name}</b>'.format(
                name=preset.query,
            )
        ),
        reply_markup=cancel_markup
    )
    await state.set_state('pars_count')


@router.callback_query(text="parse")
async def back_parse(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text(
        text=texts.choose_parser,
        reply_markup=parsers_markup
    )


# maybe add every state
@router.message(Text(text_contains="в главное меню", text_ignore_case=True))
async def go_main_menu(message: types.Message):
    await welcome_handler(message)
