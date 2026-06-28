from pyrogram import filters
from pyrogram import Client as AnonXMusic
from pyrogram.types import Message

MANAGEMENT_BOT = "StickerKangBot"

WELCOME_MSG = "For welcome messages, add @StickerKangBot to your group."
FILTER_MSG = "For filters, add @StickerKangBot to your group."
TAG_MSG = "For tagging members, add @StickerKangBot to your group."
ANTIPROMO_MSG = "For anti-promotion settings, add @StickerKangBot to your group."


async def management_bot_present(client: AnonXMusic, chat_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, MANAGEMENT_BOT)
        if member:
            return True
    except Exception:
        pass
    return False


@AnonXMusic.on_message(filters.command(["welcome", "setwelcome"], prefixes="/"))
async def welcome_cmd(client: AnonXMusic, message: Message):
    if message.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, message.chat.id):
            return
    await message.reply_text(WELCOME_MSG)


@AnonXMusic.on_message(filters.command(["filter"], prefixes="/"))
async def filter_cmd(client: AnonXMusic, message: Message):
    if message.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, message.chat.id):
            return
    await message.reply_text(FILTER_MSG)


@AnonXMusic.on_message(filters.command(["all", "tagall", "call"], prefixes="/"))
async def tag_cmd(client: AnonXMusic, message: Message):
    if message.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, message.chat.id):
            return
    await message.reply_text(TAG_MSG)


@AnonXMusic.on_message(filters.command(["antipromo"], prefixes="/"))
async def antipromo_cmd(client: AnonXMusic, message: Message):
    if message.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, message.chat.id):
            return
    await message.reply_text(ANTIPROMO_MSG)
