from aiogram.types import Message
from aiogram.dispatcher.filters import BaseFilter

from config import config


class IsAdminFilter(BaseFilter):
    """
    Custom filter 
    """

    async def __call__(self, msg: Message):
        return msg.from_user.id in config.admin_ids

    class Config:
        arbitrary_types_allowed = True
