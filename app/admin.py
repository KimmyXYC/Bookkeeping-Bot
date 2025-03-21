from telebot import types
from loguru import logger

from app import utils


async def blind(bot, message: types.Message, db):
    try:
        command_args = message.text.split()
        if len(command_args) != 3:
            await bot.reply_to(message, "参数错误")
            return
        user_id = command_args[1]
        user_name = command_args[2]
        user_index = db.get("index")
        if user_index is None:
            user_index = {"id":[]}
        if user_id in user_index["id"]:
            await bot.reply_to(message, f"用户 {user_id} 已经绑定")
            return
        user_index[f"name_{user_name}"] = user_id
        user_index[f"id_{user_id}"] = user_name
        user_index["id"].append(int(user_id))
        db.set("index", user_index)
        await bot.send_message(message.chat.id, f"成功绑定用户 {user_name} {user_id}")
        logger.info(f"[Blind] Bind user {user_name} {user_id}")
    except Exception as e:
        await bot.reply_to(message, f"绑定失败 {e}")
        logger.error(f"[Blind] {e}")
        raise e


async def create(bot, message: types.Message, db):
    command_args = message.text.split()
    if len(command_args) != 4:
        await bot.reply_to(message, "参数错误")
        return
    user_id = command_args[1]
    amount = command_args[2]
    unix_time = command_args[3]
    id_list = db.get("index")
    if id_list is None:
        id_list = {"id": []}
    if int(user_id) not in id_list["id"]:
        await bot.reply_to(message, f"用户 {user_id} 未绑定")
        return
    user_index = db.get(f"user_{user_id}")
    if user_index is None:
        user_index = {"capital": 0, "interest": 0, "repay": 0, "temp_capital": 0, "unix_time": 0}
    user_index["capital"] = float(amount)
    user_index["temp_capital"] = float(amount)
    user_index["unix_time"] = int(unix_time)
    db.set(f"user_{user_id}", user_index)
    await bot.reply_to(message, f"成功创建债务 {user_id} {amount} {unix_time}")
    logger.info(f"[Create] Create debt for {user_id} {amount} {unix_time}")


async def set_rate(bot, message: types.Message, db):
    rate = message.text.split(" ")[1]
    db.set("rate", float(rate))
    id_list = db.get("index")
    if id_list is None:
        id_list = {"id": []}
    for user_id in id_list["id"]:
        user_index = db.get(f"user_{user_id}")
        temp_capital = user_index["temp_capital"]
        hours = (utils.get_unix_time() - user_index["unix_time"])/3600
        user_index["interest"] += utils.calculate_compound_interest(temp_capital, int(rate), hours) - temp_capital
        user_index["temp_capital"] = utils.calculate_compound_interest(temp_capital, int(rate), hours)
        user_index["unix_time"] = utils.get_unix_time()
        db.set(f"user_{user_id}", user_index)
    await bot.reply_to(message, f"成功设置利率为 {rate}%, 并计算了利息")
    logger.info(f"[Set Rate] Set rate to {rate}%")
