from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2
from helper_func import encode, get_message_id
from database import find_join_req


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


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    user_id = message.from_user.id
    is_verified, reason = await is_verified_user(client, user_id)

    if not is_verified:
        if reason == "join":
            await message.reply(f"🚀 पहले हमारे चैनल को जॉइन करें: [Join Now](https://t.me/{FORCE_SUB_CHANNEL})")
        elif reason == "request":
            await message.reply(f"📩 कृपया दूसरे चैनल में request भेजें: [Request Here](https://t.me/{FORCE_SUB_CHANNEL2})")
        return

    while True:
        try:
            channel_message = await client.ask(
                text="Forward Message From The DB Channel (With Quotes)..\n\nOr Send The DB Channel Post link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return

        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nThis Forwarded Post Is Not From My DB Channel", quote=True)
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    await channel_message.reply_text(f"<b>Here Is Your Link</b>\n\n{link}", quote=True, reply_markup=reply_markup)
