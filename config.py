import json
import os
from typing import Optional, List

from aiogram import Bot, Dispatcher
from loguru import logger
from pydantic import BaseSettings


class Settings(BaseSettings):
    token: str
    admin_ids: List[int]
    bot_username: str

    class Config:
        env_prefix = "bot_"


def load_config(path) -> Optional[Settings]:
    if not os.path.exists(path):
        logger.error(f"Config file: '{path}' does not exists!")
        exit(1)

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return Settings(**data)
        except json.JSONDecodeError:
            logger.error(f"Config file: '{path}' is not valid Json!")


path = "settings_local.json"
if not os.path.exists(path):
    path = "settings.json"
config = load_config(path)

bot = Bot(token=config.token, parse_mode="HTML")
dp = Dispatcher()

THROTTLE_TIME = 0.2  # период троттлинга в секундах

user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
mob_user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.141 Mobile Safari/537.36"
new_mob_user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.167 Mobile Safari/537.36'
