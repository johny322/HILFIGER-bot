import re
import urllib
from asyncio import sleep

from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile
from asyncstdlib import zip_longest
from loguru import logger

from data.constants import MAX_COUNT
from data.texts import create_result_text
from models import BlackWord, DehandsBanned, User, \
    get_datetime_now, DehandsPreset, DehandsText, add_previous_preset
from dateutil.parser import parse
from data import texts
from data.states import Dehands, DehandsTextG
from data.keyboards import (get_post_date_markup, get_price_markup,
                            start_parse_markup, cancel_markup, delete_markup,
                            menu_markup, cancel_parse_markup, get_seller_date_markup,
                            save_preset_markup, get_presets_markup,
                            texts_markup, back_texts_markup, count_markup,
                            no_count_markup, parse_rating
                            )
from parsers import dehands_parse
from log import decode_log_config

# from utils.checker import check_wa

router = Router()


@router.callback_query(text="dehands_start")
async def dehands_start(query: types.CallbackQuery):
    await query.message.edit_text(
        text=texts.parse_start_sub,
        reply_markup=start_parse_markup("dehands")
    )


@router.callback_query(text="dehands")
async def dehands(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(
        text=texts.parse_many_urls.format(
            parser_link="https://www.2dehands.be/q/apple/"
        ),
        reply_markup=delete_markup,
        disable_web_page_preview=True
    )
    await state.set_state(Dehands.url)


@router.message(Dehands.url)
async def dehands_url(message: types.Message, state: FSMContext):
    links = message.text.split('\n')
    queries = []
    for link in links:
        link = link.strip()
        if not link:
            continue
        match = re.match(r"(https://){0,1}(www\.){0,1}2dehands\.be/(.+)", link)
        if match:
            query = match.group(3)
        else:
            query = "q/" + link.lower().replace(' ', '+')
        queries.append(query)

    await message.answer(
        text=texts.parse_count,
        reply_markup=count_markup
    )
    await state.update_data(query=queries)
    await state.set_state(Dehands.count)


@router.message(Dehands.preset_count, lambda msg: not msg.text.isdigit())
@router.message(Dehands.count, lambda msg: not msg.text.isdigit())
async def dehands_count_inv(message: types.Message):
    await message.answer(
        text=texts.parse_count_invalid,
        reply_markup=count_markup
    )


@router.message(Dehands.count)
async def dehands_count(message: types.Message, state: FSMContext):
    count = int(message.text)
    if count > MAX_COUNT:
        await message.answer(
            text=texts.parse_count_too_much.format(
                max_count=MAX_COUNT
            ),
            reply_markup=cancel_markup
        )
        return
    await state.update_data(count=count)
    await message.answer(
        text=texts.parse_price.format(coin="EUR"),
        reply_markup=get_price_markup()
    )
    await state.set_state(Dehands.price)


@router.message(Dehands.price)
async def dehands_price_inv(message: types.Message, state: FSMContext):
    payload = message.text.split("-")
    try:
        starts = int(payload[0])
        ends = int(payload[1])
        await state.update_data(price_s=starts, price_e=ends)
        await state.set_state(Dehands.seller_posts)
        await message.answer(
            text=texts.parse_seller_posts,
            reply_markup=no_count_markup
        )
    except (IndexError, ValueError):
        await message.answer(
            text=texts.parse_price_invalid,
            reply_markup=get_price_markup()
        )


@router.message(Dehands.seller_posts)
async def dehands_seller_posts(message: types.Message, state: FSMContext):
    if not message.text.isdigit() and message.text != "no":
        await message.answer(text=texts.parse_seller_posts_invalid)
        return

    if message.text == "no":
        max_posts = None
    else:
        max_posts = int(message.text)
    await state.update_data(max_posts=max_posts)

    await message.answer(
        text=texts.parse_seller_rating,
        reply_markup=parse_rating
    )
    await state.set_state(Dehands.seller_rating)


@router.message(Dehands.seller_rating)
async def dehands_seller_rating(message: types.Message, state: FSMContext):
    if not message.text.isdigit() and message.text != "no":
        await message.answer(text=texts.parse_seller_rating_invalid)
        return
    if message.text.isdigit():
        if int(message.text) > 5:
            await message.answer(text=texts.parse_seller_posts_invalid)
            return
    if message.text == "no":
        max_rating = None
    else:
        max_rating = int(message.text)
    await state.update_data(max_rating=max_rating)

    await message.answer(
        text=texts.parse_post_views,
        reply_markup=no_count_markup
    )
    await state.set_state(Dehands.views)


@router.message(Dehands.views)
async def olx_max_post_views(message: types.Message, state: FSMContext):
    if not message.text.isdigit() and message.text != "no":
        await message.answer(text=texts.parse_post_views_invalid)
        return

    if message.text == "no":
        max_views = None
    else:
        max_views = int(message.text)

    await message.answer(
        text=texts.parse_creator_date,
        reply_markup=get_seller_date_markup()
    )

    await state.update_data(max_views=max_views)
    await state.set_state(Dehands.reg_date)


@router.message(Dehands.reg_date)
async def dehands_reg_date(message: types.Message, state: FSMContext):
    if message.text == "no":
        await message.answer(
            text=texts.parse_post_date,
            reply_markup=get_post_date_markup()
        )
        await state.update_data(reg_date=None)
        await state.set_state(Dehands.post_date)
        return

    try:
        reg_date = parse(message.text)
    except ValueError:
        logger.debug("ValueError reg_date")
        await message.answer(
            text=texts.parse_date_invalid,
            reply_markup=cancel_markup
        )
        return

    if reg_date.year > 2000 and reg_date < get_datetime_now():
        await message.answer(
            text=texts.parse_post_date,
            reply_markup=get_post_date_markup()
        )
        await state.update_data(reg_date=message.text)
        await state.set_state(Dehands.post_date)
    else:
        await message.answer(
            text=texts.parse_date_invalid,
            reply_markup=get_seller_date_markup()
        )


@router.message(Dehands.post_date)
async def dehands_post_date(message: types.Message, state: FSMContext):
    if message.text == "no":
        await state.update_data(post_date=None)
        await state.set_state(Dehands.save)
        await message.answer(
            text=texts.parse_save_preset,
            reply_markup=save_preset_markup
        )
        return

    try:
        post_date = parse(message.text)
        if post_date.year > 2000 and post_date < get_datetime_now():
            await state.update_data(post_date=message.text)
            await state.set_state(Dehands.save)
            await message.answer(
                text=texts.parse_save_preset,
                reply_markup=save_preset_markup
            )
        else:
            await message.answer(
                text=texts.parse_date_invalid,
                reply_markup=get_post_date_markup()
            )
    except ValueError:
        await message.answer(
            text=texts.parse_date_invalid,
            reply_markup=cancel_markup
        )


@router.message(Dehands.save, text="yes")
async def dehands_save_preset(message: types.Message, state: FSMContext):
    await message.answer(
        text=texts.preset_save_name,
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Dehands.preset)


@router.message(Dehands.save, text="no")
@router.message(Dehands.preset)
@router.message(Dehands.preset_count)
async def dehands_run_parse(message: types.Message, state: FSMContext):
    curr_state = await state.get_state()

    # ex = Excel()
    # main_key = 'Ссылка на товар'
    # data = {
    #     main_key: []
    # }
    # ex.set_main_key(main_key)
    # ex.set_data(data)

    user = User.get(user_id=message.from_user.id)
    log = decode_log_config(user.log_config)

    data = await state.get_data()
    if curr_state == "Dehands:preset_count":
        prev_preset = data.get('preset')
        if prev_preset:
            preset = prev_preset
        else:
            preset = DehandsPreset.get(owner=user, id=data['preset_id'])

        queries = preset.query.split('\n')
        count = int(message.text)
        if count > MAX_COUNT:
            await message.answer(
                text=texts.parse_count_too_much.format(
                    max_count=MAX_COUNT
                ),
                reply_markup=cancel_markup
            )
            return
        price_s = preset.price_s
        price_e = preset.price_e
        seller_reg = preset.reg_date
        post_date = preset.post_date
        max_posts = preset.max_posts
        max_views = preset.max_views
        max_rating = preset.max_rating
    else:
        queries = data["query"]
        count = data["count"]
        price_s = data["price_s"]
        price_e = data["price_e"]
        max_views = data['max_views']
        max_rating = data['max_rating']
        max_posts = data["max_posts"]
        seller_reg = None
        if data["reg_date"]:
            seller_reg = parse(data["reg_date"])
        post_date = None
        if data["post_date"]:
            post_date = parse(data["post_date"])

    # previous_state_name = f'{user.user_id}_previous_state'
    # try:
    #     market_preset_id = DehandsPreset.get(owner=user, name=previous_state_name)
    #     DehandsPreset.update(
    #         query=query,
    #         price_s=price_s,
    #         price_e=price_e,
    #         reg_date=seller_reg,
    #         post_date=post_date,
    #         max_posts=max_posts
    #     ).where((DehandsPreset.owner == user) & (DehandsPreset.name == previous_state_name)).execute()
    # except DehandsPreset.DoesNotExist:
    #     market_preset_id = DehandsPreset.create(
    #         owner=user,
    #         name=previous_state_name,
    #         query=query,
    #         price_s=price_s,
    #         price_e=price_e,
    #         reg_date=seller_reg,
    #         post_date=post_date,
    #         max_posts=max_posts
    #     )
    # add_previous_preset(user, DehandsPreset._meta.table_name, market_preset_id, curr_state)

    if curr_state == "Dehands:preset":
        try:
            DehandsPreset.get(owner=user, name=message.text)
            await message.answer(text=texts.preset_alredy_exists)
        except DehandsPreset.DoesNotExist:
            DehandsPreset.create(
                owner=user,
                name=message.text,
                query='\n'.join(queries),
                price_s=price_s,
                price_e=price_e,
                reg_date=seller_reg,
                post_date=post_date,
                max_posts=max_posts,
                max_views=max_views,
                max_rating=max_rating
            )
            await message.answer(text=texts.preset_saved)

    await state.set_state(Dehands.cancel)

    await message.answer(
        text=texts.parse_starts,
        reply_markup=cancel_parse_markup
    )
    posts_counted = 0
    posts_getted = 0

    skip_post_price = 0
    skip_post_date = 0
    skip_reg_date = 0
    skip_only_phone = 0
    skip_max_posts = 0
    skip_max_rating = 0
    skip_max_views = 0

    skip_ban_word = 0
    skip_ban_post = 0
    domain = "https://www.2dehands.be/"
    urls = [domain + query for query in queries]
    # url = f"https://www.2dehands.be/{query}"
    funcs = [dehands_parse(url, 2) for url in urls]
    async for parser_results in zip_longest(*funcs):
        if not parser_results:
            continue
        for post, get_posts, start_url in parser_results:
            if get_posts:
                await message.answer(
                    text=texts.parser_many_get_posts.format(
                        count_posts=get_posts,
                        url=start_url
                    ),
                    disable_web_page_preview=True
                )
                posts_getted += get_posts
            curr_state = await state.get_state()
            if not "Dehands:cancel" == curr_state:
                await message.answer(
                    text=texts.parse_interrupted,
                    reply_markup=menu_markup
                )
                return
            await sleep(0.1)
            if not post.price:
                skip_post_price += 1
                continue
            if post.price > price_e or post.price < price_s:
                skip_post_price += 1
                continue
            if post_date:
                if post_date > post.created:
                    skip_post_date += 1
                    continue
            if seller_reg:
                if seller_reg > post.seller_reg:
                    skip_reg_date += 1
                    continue
            if max_views is not None:
                if max_views < post.views:
                    skip_max_views += 1
                    continue
            if max_rating is not None:
                if max_rating < post.seller_rating:
                    skip_max_rating += 1
                    continue
            if max_posts is not None:
                if max_posts < post.seller_posts:
                    skip_max_posts += 1
                    continue

            if log.only_with_phone and not post.phone:
                skip_only_phone += 1
                continue

            word_ban = False
            for word in post.title.split():
                try:
                    BlackWord.get(
                        owner=user,
                        name=word
                    )
                    word_ban = True
                    break
                except BlackWord.DoesNotExist:
                    pass
            if word_ban:
                skip_ban_word += 1
                continue

            wa_texts = []
            for modl in DehandsText.select().where(DehandsText.owner == user):
                mtext = modl.text.replace("@link", "{link}"
                                          ).replace("@seller", "{seller}"
                                                    ).replace("@price", "{price}"
                                                              ).replace("@itemname", "{itemname}").format(
                    seller=post.seller_name,
                    price=post.price,
                    itemname=post.title,
                    link=post.link,
                )
                wa_texts.append((
                    f"<a href='https://web.whatsapp.com/send?phone={post.phone}&text={urllib.parse.quote(mtext)}'>{modl.name}</a>",
                    f"<a href='https://api.whatsapp.com/send?phone={post.phone}&text={urllib.parse.quote(mtext)}'>{modl.name}</a>",
                ))

            extra = dict(
                wa_texts=wa_texts,
                currency='EUR',
            )

            try:
                if user.other_banned:
                    DehandsBanned.get(seller=post.seller_id)
                else:
                    DehandsBanned.get(owner=user, seller=post.seller_id)
                logger.debug("post in black list")
                skip_ban_post += 1
                continue
            except DehandsBanned.DoesNotExist:
                DehandsBanned.create(owner=user, seller=post.seller_id)

            text = create_result_text(post, log, extra)
            posts_counted += 1
            text += f"\nℹ️ Осталось спарсить объявлений: <b>{count - posts_counted}/{count}</b>"

            if log.photo:
                try:
                    await message.answer_photo(
                        photo=post.photo_url,
                        caption=text
                    )
                except TelegramBadRequest as e:
                    if 'MEDIA_CAPTION_TOO_LONG' in str(e):
                        await message.answer_photo(
                            photo=post.photo_url
                        )
                        await message.answer(text=text, disable_web_page_preview=True)
            else:
                await message.answer(text=text, disable_web_page_preview=True)
            if posts_counted >= count:
                break
        if posts_counted >= count:
            break
    all_skip = skip_post_price + skip_post_date + skip_reg_date + skip_max_views + skip_max_rating + \
               skip_max_posts + skip_only_phone + skip_ban_post + skip_ban_word
    anythink_skip = posts_getted - all_skip - count

    skip_data = dict(
        skip_post_price=skip_post_price,
        skip_post_date=skip_post_date,
        skip_reg_date=skip_reg_date,
        skip_max_views=skip_max_views,
        skip_max_rating=skip_max_rating,
        skip_max_posts=skip_max_posts,
        skip_only_phone=skip_only_phone,
        skip_ban_post=skip_ban_post,
        skip_ban_word=skip_ban_word,
        anythink_skip=anythink_skip,
        all_count=posts_getted - count
    )
    await message.answer(
        text=texts.parse_ends + texts.parser_text_end(skip_data),
        reply_markup=menu_markup
    )
    # df = ex.get_df_bytes()
    # f = BufferedInputFile(df, 'Результат.xlsx')
    # await message.answer_document(f)


@router.message(Dehands.save)
async def dehands_preset_save_invalid(message: types.Message):
    await message.answer(
        text=texts.parse_save_preset,
        reply_markup=save_preset_markup
    )


@router.callback_query(text="dehands_preset")
async def dehands_preset(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    pr_query = DehandsPreset.select().where(DehandsPreset.owner == user)
    presets = {}
    for p in pr_query:
        if p.name != f'{user.user_id}_previous_state':
            presets[p.name] = p.id

    if not presets:
        await query.answer(text="У вас нет пресетов", show_alert=True)
        return

    await query.message.edit_text(
        text=texts.presets,
        reply_markup=get_presets_markup("dehands", presets)
    )


@router.callback_query(lambda cb: cb.data.split(":")[0] == "dehands_run_preset")
async def dehands_run_preset(query: types.CallbackQuery, state: FSMContext):
    preset = DehandsPreset.get(id=query.data.split(":")[1])
    await state.update_data(preset_id=preset.id)
    await state.set_state(Dehands.preset_count)
    reg_date = "Нет"
    if preset.reg_date:
        reg_date = preset.reg_date.strftime("%d-%m-%Y")
    post_date = "Нет"
    if preset.post_date:
        post_date = preset.post_date.strftime("%d-%m-%Y")
    max_posts = 'Нет'
    if preset.max_posts is not None:
        max_posts = preset.max_posts
    max_rating = 'Нет'
    if preset.max_rating is not None:
        max_rating = preset.max_rating
    max_views = 'Нет'
    if preset.max_views is not None:
        max_views = preset.max_views

    text_data = dict(
        name=preset.query,
        price=f"{preset.price_s}-{preset.price_e}",
        reg_date=reg_date,
        post_date=post_date,
        max_posts=max_posts,
        max_rating=max_rating,
        max_views=max_views,
        currency='EUR'
    )
    await query.message.edit_text(
        text=texts.preset_settings.format(
            settings=texts.get_preset_settings_text(text_data)
        ),
    )


@router.callback_query(text="dehands_del_presets")
async def dehands_delete_all_presets(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    DehandsPreset.delete().where(DehandsPreset.owner == user).execute()
    await dehands_start(query)


@router.callback_query(text="dehands_texts_delete")
async def dehands_delete_all_text(query: types.CallbackQuery):
    user = User.get(user_id=query.from_user.id)
    DehandsText.delete().where(DehandsText.owner == user).execute()
    await dehands_start(query)


@router.callback_query(text="dehands_texts")
async def dehands_custom_wa_text(query: types.CallbackQuery, state: FSMContext):
    user = User.get(user_id=query.from_user.id)
    text_models = list(DehandsText.select().where(DehandsText.owner == user))
    if text_models:
        await query.message.edit_text(
            text=texts.parser_texts,
            reply_markup=texts_markup("dehands", text_models)
        )
    else:
        await query.message.edit_text(text=texts.new_text)
        await state.set_state(DehandsTextG.text)


@router.callback_query(text="dehands_create_text")
async def dehands_create_text(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(text=texts.new_text)
    await state.set_state(DehandsTextG.text)


@router.callback_query(lambda cb: cb.data.split(":")[0] == "dehands_text")
async def dehands_text_info(query: types.CallbackQuery):
    text_id = int(query.data.split(":")[1])
    text = DehandsText.get(id=text_id)
    await query.message.edit_text(
        text=texts.parser_text_info.format(
            name=text.name,
            text=text.text
        ),
        reply_markup=back_texts_markup("dehands")
    )


@router.message(DehandsTextG.text)
async def dehands_new_text(message: types.Message, state: FSMContext):
    await message.answer(
        text=texts.new_text_name
    )
    await state.update_data(text=message.text)
    await state.set_state(DehandsTextG.name)


@router.message(DehandsTextG.name)
async def dehands_new_text_name(message: types.Message, state: FSMContext):
    user = User.get(user_id=message.from_user.id)
    try:
        DehandsText.get(owner=user, name=message.text)
        await message.answer(
            text=texts.new_text_name_exists
        )
    except DehandsText.DoesNotExist:
        data = await state.get_data()
        DehandsText.create(
            owner=user,
            name=message.text,
            text=data["text"]
        )
    finally:
        text_models = list(DehandsText.select().where(DehandsText.owner == user))
        await message.answer(
            text=texts.parser_texts,
            reply_markup=texts_markup("dehands", text_models)
        )
