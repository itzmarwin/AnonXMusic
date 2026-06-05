# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import asyncio

from pyrogram import errors, filters, types

from anony import app, db, lang

broadcasting = asyncio.Lock()


@app.on_message(filters.command(["broadcast"]) & app.sudoers)
@lang.language()
async def _broadcast(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text(message.lang["gcast_usage"])

    if broadcasting.locked():
        return await message.reply_text(message.lang["gcast_active"])

    msg = message.reply_to_message
    copy = "-copy" in message.command
    sent = await message.reply_text(message.lang["gcast_start"])

    async with broadcasting:

        count = 0
        failed = None

        if "-nochat" not in message.command:
            groups = list(await db.get_chats())

            for chat in groups:
                try:
                    (
                        await msg.copy(chat, reply_markup=msg.reply_markup)
                        if copy
                        else await msg.forward(chat)
                    )
                    count += 1
                    await asyncio.sleep(0.2)
                except errors.FloodWait as fw:
                    await asyncio.sleep(fw.value + 10)
                except Exception as ex:
                    if not failed:
                        failed = open("errors.txt", "w")
                    failed.write(f"{chat} - {ex}\n")
                    continue

        await sent.edit_text(
            f"» 𝖡𝗋𝗈𝖺𝖽𝖼𝖺𝗌𝗍𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖳𝗈 {count}  𝖢𝗁𝖺𝗍𝗌"
        )

        if "-user" not in message.command:
            if failed:
                failed.close()
                await message.reply_document(document="errors.txt")
                try:
                    os.remove("errors.txt")
                except Exception:
                    pass
            return

        ucount = 0
        users = list(await db.get_users())

        for user in users:
            try:
                (
                    await msg.copy(user, reply_markup=msg.reply_markup)
                    if copy
                    else await msg.forward(user)
                )
                ucount += 1
                await asyncio.sleep(0.2)
            except errors.FloodWait as fw:
                await asyncio.sleep(fw.value + 10)
            except Exception as ex:
                if not failed:
                    failed = open("errors.txt", "a") 
                failed.write(f"{user} - {ex}\n")
                continue

    final_text = f"» 𝖡𝗋𝗈𝖺𝖽𝖼𝖺𝗌𝗍𝖾𝖽 𝖬𝖾𝗌𝗌𝖺𝗀𝖾𝗌 𝖳𝗈 {ucount}  𝖴𝗌𝖾𝗋𝗌"

    if failed:
        failed.close()
        await message.reply_document(
            document="errors.txt",
            caption=final_text,
        )
        try:
            os.remove("errors.txt")
        except Exception:
            pass
    else:
        await message.reply_text(final_text)
