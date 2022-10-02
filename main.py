from routers import router
from config import config, bot, dp
from utils.notify import notify_users
from utils.logger import setup_logger
from data.commands import base_commands
from middleware.throttling import ThrottlingMiddleware


async def on_startup(dispatcher, bot):
    await bot.set_my_commands(commands=base_commands)
    await notify_users(bot, config.admin_ids)


if __name__ == "__main__":
    setup_logger()
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.message.outer_middleware(
        ThrottlingMiddleware()
    )
    dp.run_polling(bot)
