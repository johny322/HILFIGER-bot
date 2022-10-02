from aiogram.dispatcher.fsm.state import StatesGroup, State


class Mailing(StatesGroup):
    post = State()
    sure = State()


class NewBlackWord(StatesGroup):
    main = State()


class Dehands(StatesGroup):
    url = State()
    count = State()
    price = State()
    seller_posts = State()
    reg_date = State()
    post_date = State()
    seller_rating = State()
    views = State()
    save = State()
    preset = State()
    cancel = State()
    preset_count = State()


class DehandsTextG(StatesGroup):
    text = State()
    name = State()
