# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:18
# @File    : controller.py
# @Software: PyCharm
from asgiref.sync import sync_to_async
from loguru import logger
from telebot import types
from telebot import util, formatting
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.asyncio_storage import StateMemoryStorage

from setting.telegrambot import BotSetting
from app import admin, user

StepCache = StateMemoryStorage()


@sync_to_async
def sync_to_async_func():
    pass


class BotRunner(object):
    def __init__(self, db):
        self.bot = AsyncTeleBot(BotSetting.token, state_storage=StepCache)
        self.db = db

    async def run(self):
        logger.info("Bot Start")
        bot = self.bot
        if BotSetting.proxy_address:
            from telebot import asyncio_helper

            asyncio_helper.proxy = BotSetting.proxy_address
            logger.info("Proxy tunnels are being used!")

        await self.bot.set_my_commands([
            types.BotCommand("help", "查看帮助"),
            types.BotCommand("overview", "查看总览 | /overview [用户名]"),
            types.BotCommand("rate", "查看利率"),
            types.BotCommand("repay", "还款 | /repay [金额]")
        ])
        await self.bot.set_my_commands([
            types.BotCommand("blind", "绑定用户"),
            types.BotCommand("create", "创建债务"),
            types.BotCommand("set_rate", "设置利率"),
            types.BotCommand("help", "查看帮助"),
            types.BotCommand("overview", "查看总览"),
            types.BotCommand("rate", "查看利率"),
            types.BotCommand("repay", "还款")
        ], scope=types.BotCommandScopeChat(chat_id=BotSetting.admin_id))

        @bot.message_handler(commands=["start", "help"], chat_types=["private"])
        async def listen_start_command(message: types.Message):
            _message = await bot.reply_to(
                message=message,
                text=formatting.format_text(
                    formatting.mbold("🥕 Help"),
                    formatting.mcode("/overview [用户名] 查看总览"),
                    formatting.mcode("/rate 查看利率"),
                    formatting.mcode("/repay [金额] 还款"),
                    formatting.mlink(
                        "🍀 Github", "https://github.com/KimmyXYC/Bookkeeping-Bot"
                    ),
                ),
                parse_mode="MarkdownV2",
                disable_web_page_preview=True
            )

        @bot.message_handler(commands="blind", chat_types=["private"])
        async def listen_blind_command(message: types.Message):
            if message.from_user.id != int(BotSetting.admin_id):
                return
            await admin.blind(bot, message, self.db)

        @bot.message_handler(commands="create", chat_types=["private"])
        async def listen_create_command(message: types.Message):
            if message.from_user.id != int(BotSetting.admin_id):
                return
            await admin.create(bot, message, self.db)

        @bot.message_handler(commands="set_rate", chat_types=["private", "group", "supergroup"])
        async def listen_set_rate_command(message: types.Message):
            if message.from_user.id != int(BotSetting.admin_id):
                return
            await admin.set_rate(bot, message, self.db)

        @bot.message_handler(commands="overview", chat_types=["private", "group", "supergroup"])
        async def listen_overview_command(message: types.Message):
            await user.overview(bot, message, self.db)

        @bot.message_handler(commands="rate", chat_types=["private", "group", "supergroup"])
        async def listen_rate_command(message: types.Message):
            await user.output_rate(bot, message, self.db)

        @bot.message_handler(commands="repay", chat_types=["private", "group", "supergroup"])
        async def listen_repay_command(message: types.Message):
            await user.repay_money(bot, message, self.db)

        try:
            await bot.polling(
                non_stop=True, allowed_updates=util.update_types, skip_pending=True
            )
        except ApiTelegramException as e:
            logger.opt(exception=e).exception("ApiTelegramException")
        except Exception as e:
            logger.exception(e)
