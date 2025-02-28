from telebot import types
from loguru import logger

from app import utils


async def overview(bot, message: types.Message, db):
    id_list = db.get("index")
    loan_rate = db.get("rate")
    if loan_rate is None:
        loan_rate = 10
        db.set("rate", loan_rate)
    command_args = message.text.split()
    if len(command_args) == 1:
        total_capital = 0
        total_interest = 0
        total_repay = 0
        total_surplus = 0
        for user_id in id_list["id"]:
            user_index = db.get(f"user_{user_id}")

            capital = user_index["capital"]
            repay = user_index["repay"]
            interest = user_index["interest"]

            hours = (utils.get_unix_time() - user_index["unix_time"])/3600
            temp_capital = user_index["temp_capital"]
            interest += utils.calculate_compound_interest(temp_capital, int(loan_rate), hours) - temp_capital

            total_capital += capital
            total_interest += interest
            total_repay += repay

        total_surplus += total_capital + total_interest - total_repay
        await bot.reply_to(message, f"总本金: {total_capital:.2f} USDT\n"
                                    f"总利息: {total_interest:.2f} USDT\n"
                                    f"总还款: {total_repay:.2f} USDT\n"
                                    f"总剩余: {total_surplus:.2f} USDT")
    else:
        user_name = command_args[1]
        id_list = db.get("index")
        user_id = id_list.get(f"name_{user_name}", None)
        if user_id is None:
            await bot.reply_to(message, f"用户 {user_name} 未绑定")
            return
        user_index = db.get(f"user_{user_id}")

        capital = user_index["capital"]
        repay = user_index["repay"]
        interest = user_index["interest"]

        hours = (utils.get_unix_time() - user_index["unix_time"]) / 3600
        temp_capital = user_index["temp_capital"]
        interest += utils.calculate_compound_interest(temp_capital, int(loan_rate), hours) - temp_capital

        await bot.reply_to(message, f"用户: {user_name} {user_id}\n"
                                    f"本金: {capital:.2f} USDT\n"
                                    f"利息: {interest:.2f} USDT\n"
                                    f"还款: {repay:.2f} USDT\n"
                                    f"剩余: {capital + interest - repay:.2f} USDT")


async def output_rate(bot, message: types.Message, db):
    loan_rate = db.get("rate")
    if loan_rate is None:
        loan_rate = 10
        db.set("rate", loan_rate)
    await bot.reply_to(message, f"当前利率为 {loan_rate}%")


async def repay_money(bot, message: types.Message, db):
    command_args = message.text.split()
    if len(command_args) != 2:
        await bot.reply_to(message, "参数错误")
        return

    loan_rate = db.get("rate")
    if loan_rate is None:
        loan_rate = 10
        db.set("rate", loan_rate)

    user_id = message.from_user.id
    try:
        repay_amount = float(command_args[1])
    except ValueError:
        await bot.reply_to(message, "还款金额需为数字")
        return
    if repay_amount <= 0:
        await bot.reply_to(message, "还款金额需大于 0")
        return
    id_list = db.get("index")
    if user_id not in id_list["id"]:
        await bot.reply_to(message, f"用户 {user_id} 未绑定")
        return

    user_index = db.get(f"user_{user_id}")
    capital = user_index["capital"]
    repay = user_index["repay"]
    interest = user_index["interest"]

    hours = (utils.get_unix_time() - user_index["unix_time"]) / 3600
    temp_capital = user_index["temp_capital"]
    interest += utils.calculate_compound_interest(temp_capital, int(loan_rate), hours) - temp_capital
    user_index["interest"] = interest
    user_index["temp_capital"] = utils.calculate_compound_interest(temp_capital, int(loan_rate), hours)
    user_index["unix_time"] = utils.get_unix_time()

    repay += repay_amount
    user_index["repay"] = repay

    if repay_amount > capital + interest - repay:
        user_index["temp_capital"] = 0
        user_index["repay"] = capital + interest
        await bot.reply_to(message, f"还款金额 {repay_amount:.2f} USDT, 超过剩余金额, 已还清")
        return

    db.set(f"user_{user_id}", user_index)
    await bot.reply_to(message, f"还款成功 {repay_amount:.2f} USDT")
