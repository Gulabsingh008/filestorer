import os, asyncio, humanize
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, FILE_AUTO_DELETE
from helper_func import encode, decode, get_messages
from database import add_user, present_user, find_join_req, full_userbase, del_user

file_auto_delete = humanize.naturaldelta(FILE_AUTO_DELETE)


async def is_verified_user(client, user_id):
    """ यूज़र की सदस्यता और Join Request को चेक करने वाला फ़ंक्शन """
    if user_id in ADMINS:
        return True, None

    # पहला चैनल चेक करें
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            return False, "join"
    except:
        return False, "join"

    # दूसरा चैनल (Request Verification)
    request_found = await find_join_req(user_id)
    if not request_found:
        return False, "request"

    return True, None


@Bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_verified, reason = await is_verified_user(client, user_id)

    if not is_verified:
        buttons = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ]
        if reason == "request":
            buttons.append(
                [InlineKeyboardButton("📩 Send Request", url=f"https://t.me/{FORCE_SUB_CHANNEL2}")]
            )
        buttons.append(
            [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{client.username}?start={message.command[1]}")]
        )
        await message.reply_text(
            FORCE_MSG.format(mention=message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True,
            quote=True
        )
        return

    # ✅ यूज़र का वेरिफिकेशन हो गया, अब `/start` पर उसे वेलकम मैसेज मिलेगा
    if not await present_user(user_id):
        await add_user(user_id)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 About Me", callback_data="about"),
         InlineKeyboardButton("🔒 Close", callback_data="close")]
    ])

    await message.reply_text(
        text=START_MSG.format(mention=message.from_user.mention),
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        quote=True
    )


@Bot.on_message(filters.command("users") & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=f"Processing...")
    users = await full_userbase()
    await msg.edit(f"{len(users)} Users Are Using This Bot")


@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total, successful, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Broadcast Completed</u></b>

<b>Total Users :</b> <code>{total}</code>
<b>Successful :</b> <code>{successful}</code>
<b>Blocked Users :</b> <code>{blocked}</code>
<b>Deleted Accounts :</b> <code>{deleted}</code>
<b>Unsuccessful :</b> <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(f"Use This Command As A Reply To Any Telegram Message Without Any Spaces.")
        await asyncio.sleep(8)
        await msg.delete()


async def delete_files(messages, client, k):
    await asyncio.sleep(FILE_AUTO_DELETE)
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            print(f"The attempt to delete the media {msg.id} was unsuccessful: {e}")
    await k.edit_text("Your Video / File Is Successfully Deleted ✅")
