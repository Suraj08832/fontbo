import os
import random
import string
import asyncio
import sys
import logging
import signal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from aiohttp import web

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def handle_edited_message(update: Update, context: CallbackContext) -> None:
    """Handle edited messages in group chats."""
    if update.edited_message and update.edited_message.chat.type in ['group', 'supergroup']:
        original_text = update.edited_message.text
        edited_text = update.edited_message.edit_date
        
        # Store edited message ID
        edited_message_id = update.edited_message.message_id
        
        warning_message = (
            f"⚠️ Warning: Message edited by {update.edited_message.from_user.first_name}\n"
            f"Original text: {original_text}\n"
            f"Edited at: {edited_text}"
        )
        
        # Send warning
        await update.edited_message.reply_text(warning_message)
        
        # Try to delete the edited message
        try:
            # Wait 5 seconds before deletion to allow users to see the warning
            await asyncio.sleep(5)
            await update.edited_message.delete()
            logger.info(f"Deleted edited message {edited_message_id} in chat {update.edited_message.chat.id}")
        except Exception as e:
            logger.error(f"Could not delete edited message: {e}")

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
    "𝅃꯭᳚𓄂️𝆺𝅥⃝🔥 ⃪ͥ͢ ᷟ𓆩 ! 乛|⁪⁬⁮⁮⁮⁮ ‌⁪⁬𓆪��™",
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

def main():
    """Main entry point for the application."""
    try:
        # Create the Application and pass it your bot's token
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
            return

        logger.info("Bot token loaded successfully")
        logger.info("Initializing bot...")
        
        # Create application
        application = Application.builder().token(token).build()
        logger.info("Application built successfully")

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("style", style))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, handle_edited_message))
        logger.info("Handlers added successfully")
        
        # Start the web server in a separate thread
        port = int(os.getenv('PORT', 8080))
        logger.info(f"Starting web server on port {port}...")
        
        # Setup web app
        app = web.Application()
        routes = web.RouteTableDef()
        
        @routes.get('/')
        async def hello(request):
            return web.Response(text="Bot is running!")
        
        app.add_routes(routes)
        
        # Run web server in a separate thread
        import threading
        def run_web_server():
            web_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(web_loop)
            runner = web.AppRunner(app)
            web_loop.run_until_complete(runner.setup())
            site = web.TCPSite(runner, '0.0.0.0', port)
            web_loop.run_until_complete(site.start())
            logger.info(f"Web server started successfully on port {port}")
            web_loop.run_forever()
            
        webserver_thread = threading.Thread(target=run_web_server)
        webserver_thread.daemon = True
        webserver_thread.start()
        
        # Run the bot until the user presses Ctrl-C
        logger.info("Starting bot polling...")
        application.run_polling(poll_interval=3.0, timeout=30, drop_pending_updates=True)
        logger.info("Bot polling stopped")
    
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
    finally:
        logger.info("Application stopped")

if __name__ == '__main__':
    main() 