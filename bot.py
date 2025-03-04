# (c) @JigarVarma2005
# Edit codes at your own risk
from config import Config
from requests import get
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, CallbackQuery
import random
import asyncio
import json
from helper.db import manage_db
from pyrogram.errors import UserNotParticipant
from helper.markup import MakeCaptchaMarkup
# Prepare bot
app = Client(Config.SESSION_NAME, api_id=Config.APP_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
# Local database for saving user info
LocalDB = {}
ch_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Updates Channel", url="https://t.me/RobotTech_Official"),
                                    InlineKeyboardButton(text="Support Group", url="https://t.me/Chatting_officials")]])
BOT_UNAME = Config.BOT_USERNAME

@app.on_chat_member_updated()
async def check_chat_captcha(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if Config.API_TOKEN is None:
        await client.send_message(chat_id, "Please get the apy key from @JV_Community")
        return
    chat = manage_db().chat_in_db(chat_id)
    if not chat:
        return
    try:
        user_s = await client.get_chat_member(chat_id, user_id)
        if (user_s.is_member is False) and (LocalDB.get(user_id, None) is not None):
            try:
                await client.delete_messages(
                    chat_id=chat_id,
                    message_ids=LocalDB[user_id]["msg_id"]
                )
            except:
                pass
            return
        elif (user_s.is_member is False):
            return
    except UserNotParticipant:
        return
    chat_member = await client.get_chat_member(chat_id, user_id)
    if chat_member.restricted_by:
        if chat_member.restricted_by.id == (await client.get_me()).id:
            pass
        else:
            return
    try:
        if LocalDB.get(user_id, None) is not None:
            try:
                await client.send_message(
                    chat_id=chat_id,
                    text=f"{message.from_user.mention} again joined group without verifying!\n\n"
                         f"He can try again after 10 minutes.",
                    disable_web_page_preview=True
                )
                await client.delete_messages(chat_id=chat_id,
                                             message_ids=LocalDB[user_id]["msg_id"])
            except:
                pass
            await asyncio.sleep(600)
            del LocalDB[user_id]
    except:
        pass
    try:
        await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
    except:
        return
    await client.send_message(chat_id,
                              text=f"{message.from_user.mention} to chat here please verify that your a human",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Verify Now", callback_data=f"verify_{chat_id}_{user_id}")]]))
        
@app.on_message(filters.command(["captcha",f"captcha@{BOT_UNAME}"]) & ~filters.private)
async def add_chat(bot, message):
    if Config.API_TOKEN is None:
        await message.reply_text("Please get the apy key from @JV_Community")
        return
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = await bot.get_chat_member(chat_id, user_id)
    if user.status == "creator" or user.status == "administrator" or user.user.id in Config.SUDO_USERS:
        chat = manage_db().chat_in_db(chat_id)
        if chat:
            await message.reply_text("Captcha already tunned on here, use /remove to turn off")
        else:
            await message.reply_text(text=f"Please select the captcha type",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Number", callback_data=f"new_{chat_id}_{user_id}_N"),
                                                                        InlineKeyboardButton(text="Emoji", callback_data=f"new_{chat_id}_{user_id}_E")]]))
        
@app.on_message(filters.command(["help",f"help@{BOT_UNAME}"]))
async def start_chat(bot, message):
    await message.reply_text(text="/captcha - turn on captcha : There are two types of captcha\n/remove - turn off captcha\n\nfor more help ask in my support group",
                             reply_markup=ch_markup)
    
@app.on_message(filters.command(["start",f"start@{BOT_UNAME}"]))
async def help_chat(bot, message):
    await message.reply_text(text="I can help you to protect your group from bots using captcha.\n\nCheck /help to know more.",
                             reply_markup=ch_markup)
    
@app.on_message(filters.command(["remove",f"remove@{BOT_UNAME}"]) & ~filters.private)
async def del_chat(bot, message):
    if Config.API_TOKEN is None:
        await message.reply_text("Please get the apy key from @JV_Community")
        return
    chat_id = message.chat.id
    user = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator" or user.user.id in Config.SUDO_USERS:
        j = manage_db().delete_chat(chat_id)
        if j:
            await message.reply_text("Captcha turned off on this chat")
        
@app.on_callback_query()
async def cb_handler(bot, query):
    cb_data = query.data
    if cb_data.startswith("new_"):
        chat_id = query.data.rsplit("_")[1]
        user_id = query.data.split("_")[2]
        captcha = query.data.split("_")[3]
        if query.from_user.id != int(user_id):
            await query.answer("This Message is Not For You!", show_alert=True)
            return
        if captcha == "N":
            type_ = "Number"
        elif captcha == "E":
            type_ = "Emoji"
        chk = manage_db().add_chat(int(chat_id), captcha)
        if chk == 404:
            await query.message.edit("Captcha already tunned on here, use /remove to turn off")
            return
        else:
            await query.message.edit(f"{type_} Captcha turned on for this chat.")
    elif cb_data.startswith("verify_"):
        chat_id = query.data.split("_")[1]
        user_id = query.data.split("_")[2]
        if query.from_user.id != int(user_id):
            await query.answer("This Message is Not For You!", show_alert=True)
            return
        chat = manage_db().chat_in_db(int(chat_id))
        print("proccesing cb data")
        if chat:
            c = chat["captcha"]
            markup = [[],[],[]]
            if c == "N":
                print("proccesing number captcha")
                await query.answer("Creating captcha for you")
                data_ = get(f"https://api.jigarvarma.tk/num_captcha?token={Config.API_TOKEN}").text
                data_ = json.loads(data_)
                _numbers = data_["answer"]["answer"]
                list_ = ["0","1","2","3","5","6","7","8","9"]
                random.shuffle(list_)
                tot = 2
                LocalDB[int(user_id)] = {"answer": _numbers, "list": list_, "mistakes": 0, "captcha": "N", "total":tot, "msg_id": None}
                count = 0
                for i in range(3):
                    markup[0].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
                for i in range(3):
                    markup[1].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
                for i in range(3):
                    markup[2].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
            elif c == "E":
                print("proccesing img captcha")
                await query.answer("Creating captcha for you")
                data_ = get(f"https://api.jigarvarma.tk/img_captcha?token={Config.API_TOKEN}").text
                data_ = json.loads(data_)
                _numbers = data_["answer"]["answer"]
                list_ = data_["answer"]["list"]
                count = 0
                tot = 3
                for i in range(5):
                    markup[0].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
                for i in range(5):
                    markup[1].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
                for i in range(5):
                    markup[2].append(InlineKeyboardButton(f"{list_[count]}", callback_data=f"jv_{chat_id}_{user_id}_{list_[count]}"))
                    count += 1
                LocalDB[int(user_id)] = {"answer": _numbers, "list": list_, "mistakes": 0, "captcha": "E", "total":tot, "msg_id": None}
            c = LocalDB[query.from_user.id]['captcha']
            if c == "N":
                typ_ = "number"
            if c == "E":
                typ_ = "emoji"
            msg = await bot.send_photo(chat_id=chat_id,
                            photo=data_["answer"]["captcha"],
                            caption=f"{query.from_user.mention} Please click on each {typ_} button that is showen in image, {tot} mistacks are allowed.",
                            reply_markup=InlineKeyboardMarkup(markup))
            LocalDB[query.from_user.id]['msg_id'] = msg.message_id
            await query.message.delete()
    if cb_data.startswith("jv_"):
        chat_id = query.data.rsplit("_")[1]
        user_id = query.data.split("_")[2]
        _number = query.data.split("_")[3]
        if query.from_user.id != int(user_id):
            await query.answer("This Message is Not For You!", show_alert=True)
            return
        if query.from_user.id not in LocalDB:
            await query.answer("Try Again After Re-Join!", show_alert=True)
            return
        c = LocalDB[query.from_user.id]['captcha']
        tot = LocalDB[query.from_user.id]["total"]
        if c == "N":
            typ_ = "number"
        if c == "E":
            typ_ = "emoji"
        if _number not in LocalDB[query.from_user.id]["answer"]:
            LocalDB[query.from_user.id]["mistakes"] += 1
            await query.answer(f"You pressed wrong {typ_}!", show_alert=True)
            n = tot - LocalDB[query.from_user.id]['mistakes']
            if n == 0:
                await query.message.edit_caption(f"{query.from_user.mention}, you failed to solve the captcha!\n\n"
                                               f"You can try again after 10 minutes.",
                                               reply_markup=None)
                await asyncio.sleep(600)
                del LocalDB[query.from_user.id]
                return
            markup = MakeCaptchaMarkup(query.message["reply_markup"]["inline_keyboard"], _number, "❌")
            await query.message.edit_caption(f"{query.from_user.mention}, select all the {typ_}s you see in the picture. "
                                           f"You are allowed only {n} mistakes.",
                                           reply_markup=InlineKeyboardMarkup(markup))
        else:
            LocalDB[query.from_user.id]["answer"].remove(_number)
            markup = MakeCaptchaMarkup(query.message["reply_markup"]["inline_keyboard"], _number, "✅")
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(markup))
            if not LocalDB[query.from_user.id]["answer"]:
                await query.answer("You Passed🥳 the Captcha!", show_alert=True)
                del LocalDB[query.from_user.id]
                await bot.unban_chat_member(chat_id=query.message.chat.id, user_id=query.from_user.id)
                await query.message.delete(True)
            await query.answer()
    elif cb_data.startswith("done_"):
        await query.answer("Dont click on same button again", show_alert=True)
    elif cb_data.startswith("wrong_"):
        await query.answer("Dont click on same button again", show_alert=True)
        
if __name__ == "__main__":
    app.run()
