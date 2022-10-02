from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update
from cachetools import TTLCache

from data.texts import on_throttling
from config import THROTTLE_TIME

cache = TTLCache(maxsize=10_000, ttl=THROTTLE_TIME)


class ThrottlingMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        # Поскольку мидлварь только для Message, то тип Update всегда Message.
        # И проверку if isinstance(event, Message) можно пропустить, хотя PyCharm будет ругаться
        if event.chat.id in cache:
            await event.answer(on_throttling)
            return
        else:
            cache[event.chat.id] = None
        return await handler(event, data)
