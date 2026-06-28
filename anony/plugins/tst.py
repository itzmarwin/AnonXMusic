from pyrogram import filters, types
from anony import app

MANAGEMENT_BOT = "StickerKangBot"

WELCOME_MSG = "For welcome messages, add @StickerKangBot to your group."
FILTER_MSG = "For filters, add @StickerKangBot to your group."
TAG_MSG = "For tagging members, add @StickerKangBot to your group."
ANTIPROMO_MSG = "For anti-promotion settings, add @StickerKangBot to your group."


async def management_bot_present(client, chat_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, MANAGEMENT_BOT)
        if member:
            return True
    except Exception:
        pass
    return False


@app.on_message(filters.command(["welcome", "setwelcome"]) & ~app.bl_users)
async def welcome_cmd(client, m: types.Message):
    if m.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, m.chat.id):
            return
    await m.reply_text(WELCOME_MSG)


@app.on_message(filters.command(["filter"]) & ~app.bl_users)
async def filter_cmd(client, m: types.Message):
    if m.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, m.chat.id):
            return
    await m.reply_text(FILTER_MSG)


@app.on_message(filters.command(["all", "tagall", "call"]) & ~app.bl_users)
async def tag_cmd(client, m: types.Message):
    if m.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, m.chat.id):
            return
    await m.reply_text(TAG_MSG)


@app.on_message(filters.command(["antipromo"]) & ~app.bl_users)
async def antipromo_cmd(client, m: types.Message):
    if m.chat.type in ["group", "supergroup"]:
        if await management_bot_present(client, m.chat.id):
            return
    await m.reply_text(ANTIPROMO_MSG)
