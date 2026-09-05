# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import os

from pyrogram import filters, types

from anony import app, lang


@app.on_message(filters.command(["faileddb"]) & ~app.bl_users)
@lang.language()
async def faileddb_func(_, m: types.Message):
    if m.from_user.id not in app.sudoers:
        return await m.reply_text(m.lang["faileddb_not_allowed"])

    file_path = "failed_songs.txt"
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return await m.reply_text(m.lang["faileddb_empty"])

    await m.reply_document(
        document=file_path,
        caption=m.lang["faileddb_caption"],
    )
