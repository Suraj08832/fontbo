import os
import random
import string
import asyncio
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from aiohttp import web

# Load environment variables
load_dotenv()

async def handle_edited_message(update: Update, context: CallbackContext) -> None:
    """Handle edited messages in group chats."""
    if update.edited_message and update.edited_message.chat.type in ['group', 'supergroup']:
        original_text = update.edited_message.text
        edited_text = update.edited_message.edit_date
        
        warning_message = (
            f"⚠️ Warning: Message edited by {update.edited_message.from_user.first_name}\n"
            f"Original text: {original_text}\n"
            f"Edited at: {edited_text}"
        )
        
        await update.edited_message.reply_text(warning_message)

# Stylish characters for name generation
STYLISH_CHARS = {
    'a': ['α', 'ą', 'å', 'à', 'á', 'â', 'ã', 'ä', 'æ'],
    'b': ['β', 'b̶', 'b̷', 'b̸'],
    'c': ['c̶', 'c̷', 'c̸', 'ç'],
    'd': ['d̶', 'd̷', 'd̸', 'đ'],
    'e': ['ε', 'ę', 'è', 'é', 'ê', 'ë'],
    'f': ['f̶', 'f̷', 'f̸'],
    'g': ['g̶', 'g̷', 'g̸'],
    'h': ['h̶', 'h̷', 'h̸'],
    'i': ['ι', 'ì', 'í', 'î', 'ï'],
    'j': ['j̶', 'j̷', 'j̸'],
    'k': ['k̶', 'k̷', 'k̸'],
    'l': ['l̶', 'l̷', 'l̸', 'ł'],
    'm': ['m̶', 'm̷', 'm̸'],
    'n': ['n̶', 'n̷', 'n̸', 'ñ'],
    'o': ['ο', 'ò', 'ó', 'ô', 'õ', 'ö', 'ø'],
    'p': ['p̶', 'p̷', 'p̸'],
    'q': ['q̶', 'q̷', 'q̸'],
    'r': ['r̶', 'r̷', 'r̸'],
    's': ['s̶', 's̷', 's̸', 'š'],
    't': ['t̶', 't̷', 't̸'],
    'u': ['υ', 'ù', 'ú', 'û', 'ü'],
    'v': ['v̶', 'v̷', 'v̸'],
    'w': ['w̶', 'w̷', 'w̸'],
    'x': ['x̶', 'x̷', 'x̸'],
    'y': ['y̶', 'y̷', 'y̸', 'ý'],
    'z': ['z̶', 'z̷', 'z̸', 'ž']
}

# New stylish fonts
STYLISH_FONTS = [
    "𝙉𝘼𝙈𝙀 𝙈𝘼𝙆𝙀𝙍",
    "ᶦ ͢ᵃᵐ⛦⃕‌!❛𝆺𝅥⤹࿗𓆪ꪾ™",
    "🔥!⃪⍣꯭꯭𓆪꯭🝐",
    "!✦ 𝆺𝅥⎯ꨄ",
    ".𝁘ໍ!𓆪ִֶָ ֺ⎯꯭‌ 𓆩💗𓆪𓈒",
    "𝅃꯭᳚𓄂️𝆺𝅥⃝🔥 ⃪ͥ͢ ᷟ𓆩 ! 乛|⁪⁬⁮⁮⁮⁮ ‌⁪⁬𓆪🐼™",
    "𝅃꯭᳚🦁!˶꯭꯭꯭꯭꯭꯭֟፝͟͝ ⚡꯭꯭꯭꯭꯭",
    "❥‌‌❥ ⃝⃪⃕🦚⟵᷽᷍!˚‌‌‌‌◡‌⃝🐬᪳ ‌⃪𔘓❁‌‌❍•:➛",
    "𝅥‌꯭𝆬‌🦋⃪꯭ ─⃛͢┼ 𝞄⃕𝖋𝖋 !🥵⃝⃝ᬽ꯭ ⃪꯭ ꯭𝅥‌꯭𝆬‌➺꯭⎯⎯᪵᪳",
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # New unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    # Additional unique styles
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹��",
    "⏤͟͞●!●───♫▷"
]

def generate_stylish_name(name: str) -> str:
    """Generate a stylish version of the given name."""
    stylish_name = ""
    for char in name.lower():
        if char in STYLISH_CHARS:
            stylish_name += random.choice(STYLISH_CHARS[char])
        elif char in string.ascii_letters:
            stylish_name += char
        else:
            stylish_name += char
    return stylish_name

def get_stylish_font(name: str) -> str:
    """Get a random stylish font for the name."""
    return random.choice(STYLISH_FONTS).replace("NAME", name)

def create_style_buttons(name: str, page: int = 0) -> InlineKeyboardMarkup:
    """Create buttons for all styles in a 5x5 grid."""
    buttons = []
    start_idx = page * 25  # 5x5 = 25 buttons per page
    end_idx = min(start_idx + 25, len(STYLISH_FONTS))
    
    # Create 5 rows of 5 buttons each
    for row in range(5):
        current_row = []
        for col in range(5):
            idx = start_idx + (row * 5) + col
            if idx < end_idx:
                style_text = STYLISH_FONTS[idx]
                stylish_name = generate_stylish_name(name)
                
                # Create preview text
                preview_text = style_text
                if "NAME" in preview_text:
                    preview_text = preview_text.replace("NAME", stylish_name)
                elif "!" in preview_text:
                    preview_text = preview_text.replace("!", stylish_name)
                
                # Limit preview length if too long
                if len(preview_text) > 15:  # Reduced length for 5x5 grid
                    preview_text = preview_text[:15] + "..."
                
                current_row.append(InlineKeyboardButton(
                    preview_text,
                    callback_data=f"style_{name}_{idx}"
                ))
            else:
                # Add empty button to maintain grid
                current_row.append(InlineKeyboardButton(
                    " ",
                    callback_data="empty"
                ))
        
        buttons.append(current_row)
    
    # Add navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{name}_{page-1}"))
    if end_idx < len(STYLISH_FONTS):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{name}_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Welcome to the Stylish Name Bot! 🎨\n\n"
        "Use /style <your name> to generate a stylish version of your name.\n"
        "Example: /style John"
    )
    await update.message.reply_text(welcome_message)

async def style(update: Update, context: CallbackContext) -> None:
    """Generate and send a stylish version of the provided name."""
    if not context.args:
        await update.message.reply_text("Please provide a name to style. Example: /style John")
        return

    name = " ".join(context.args)
    stylish_name = generate_stylish_name(name)
    
    response = f"✨ Your name: {name}\n\n"
    response += "Choose a style from the buttons below:"
    
    reply_markup = create_style_buttons(name)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "empty":
        return  # Do nothing for empty buttons
    
    if query.data.startswith("style_"):
        _, name, style_idx = query.data.split("_")
        style_idx = int(style_idx)
        style_text = STYLISH_FONTS[style_idx]
        stylish_name = generate_stylish_name(name)
        
        # Combine style with stylish name
        combined_text = style_text
        if "NAME" in combined_text:
            combined_text = combined_text.replace("NAME", stylish_name)
        elif "!" in combined_text:
            combined_text = combined_text.replace("!", stylish_name)
        
        # Send the combined text as a new message for easy copying
        await query.message.reply_text(f"📋 Here's your stylish text:\n\n{combined_text}")
    
    elif query.data.startswith("page_"):
        _, name, page = query.data.split("_")
        page = int(page)
        try:
            await query.edit_message_text(
                text=f"✨ Your name: {name}\n\nChoose a style from the buttons below:",
                reply_markup=create_style_buttons(name, page)
            )
        except Exception as e:
            print(f"Error updating message: {e}")
            # If edit fails, send a new message
            await query.message.reply_text(
                text=f"✨ Your name: {name}\n\nChoose a style from the buttons below:",
                reply_markup=create_style_buttons(name, page)
            )

# Create a simple web app
async def web_app():
    app = web.Application()
    routes = web.RouteTableDef()
    
    @routes.get('/')
    async def hello(request):
        return web.Response(text="Bot is running!")
    
    app.add_routes(routes)
    return app

async def main() -> None:
    """Start the bot and web server."""
    # Create the Application and pass it your bot's token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    print("Initializing bot...")
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("style", style))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_edited_message))

    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 8080))
    
    # Start web server
    print(f"Starting web server on port {port}...")
    app = await web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Web server started successfully on port {port}")
    
    # Start the Bot
    print("Starting bot...")
    try:
        await application.initialize()
        await application.start()
        print("Bot initialized successfully")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Error starting bot: {e}")
        await application.stop()
        await application.shutdown()
        raise
    finally:
        print("Shutting down...")
        try:
            await application.stop()
            await application.shutdown()
        except Exception as e:
            print(f"Error during shutdown: {e}")

if __name__ == '__main__':
    try:
        print("Starting application...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 