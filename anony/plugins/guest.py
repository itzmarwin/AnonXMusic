# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import traceback

from pyrogram import enums
from pyrogram.handlers import GuestMessageHandler
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from anony import app


GUEST_PROMO_TEXT = (
    "<b>သင့် Group အတွက် အကောင်းဆုံး Music Bot</b>\n\n"
    "Ads မရှိ • Promotion မရှိ • အရည်အသွေးမြင့် Music\n\n"
    f"@{app.username} ကို Add လုပ်ပါ။"
)


async def _guest_promo(_, m):
    try:
        print("=" * 50)
        print("Guest message received!")
        print(f"Guest Query ID: {m.guest_query_id}")
        print(m)

        await app.answer_guest_query(
            m.guest_query_id,
            result=InlineQueryResultArticle(
                title="Add me to your Group!",
                input_message_content=InputTextMessageContent(
                    GUEST_PROMO_TEXT,
                    parse_mode=enums.ParseMode.HTML,
                ),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="➕ Add me in Your Group",
                                url=f"https://t.me/{app.username}?startgroup=true",
                            )
                        ]
                    ]
                ),
            ),
        )

        print("Guest query answered successfully!")

    except Exception:
        print("Guest handler error:")
        traceback.print_exc()


# Register handler manually
app.add_handler(GuestMessageHandler(_guest_promo))
