from datetime import datetime

import pytz
from peewee import *
from peewee import Metadata

db = SqliteDatabase("base.db")


def get_datetime_now() -> datetime:
    return datetime.now(pytz.timezone("Europe/Moscow")).replace(tzinfo=None)


class BaseModel(Model):
    id = PrimaryKeyField(unique=True)
    created = DateTimeField(default=get_datetime_now)

    class Meta:
        database = db
        order_by = "id"


class User(BaseModel):
    user_id = IntegerField(unique=True)
    full_name = CharField()
    username = CharField(null=True)
    log_config = CharField(default="cfg_1_1_1_1_0_0_0_1_0_1_1_1_1")
    other_banned = BooleanField(default=False)
    black_words = BooleanField(default=False)

    class Meta:
        db_table = "users"


class BlackWord(BaseModel):
    owner = ForeignKeyField(User, backref="words")
    name = CharField()

    class Meta:
        db_table = "black_words"


class DehandsBanned(BaseModel):
    owner = ForeignKeyField(User)
    seller = CharField()  # seller id

    class Meta:
        db_table = "dehands_bans"


class DehandsPreset(BaseModel):
    owner = ForeignKeyField(User)
    name = CharField()
    query = CharField()
    reg_date = DateTimeField(null=True)
    post_date = DateTimeField(null=True)
    max_rating = IntegerField(null=True)
    price_s = IntegerField()
    price_e = IntegerField()
    max_views = IntegerField(null=True)
    max_posts = IntegerField(null=True)

    class Meta:
        db_table = "dehands_presets"


class PreviousPreset(BaseModel):
    owner = ForeignKeyField(User)
    market_table_name = CharField()
    market_preset_id = IntegerField()
    prev_state = CharField()
    country = CharField(null=True)

    class Meta:
        db_table = "previous_presets"


class DehandsText(BaseModel):
    owner = ForeignKeyField(User)
    name = CharField()
    text = TextField(default="Hi")

    class Meta:
        db_table = "dehands_texts"


db.create_tables([
    User, BlackWord,
    PreviousPreset,
    DehandsPreset,
    DehandsBanned,
    DehandsText
])

ALL_BANNED = [
    DehandsBanned
]

ALL_PRESETS = [
    DehandsPreset
]

ALL_PRESETS_DICT = {preset._meta.table_name: preset for preset in ALL_PRESETS}


def add_previous_preset(owner, market_table_name, market_preset_id, prev_state, country=None):
    try:
        PreviousPreset.get(owner=owner)
        PreviousPreset.update(market_table_name=market_table_name,
                              market_preset_id=market_preset_id,
                              prev_state=prev_state,
                              country=country,
                              ).where(PreviousPreset.owner == owner).execute()
    except PreviousPreset.DoesNotExist:
        PreviousPreset.create(owner=owner,
                              market_table_name=market_table_name,
                              market_preset_id=market_preset_id,
                              prev_state=prev_state,
                              country=country
                              )
