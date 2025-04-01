import os
import random
import string
import asyncio
import sys
import logging
import signal
import time
import atexit
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
from aiohttp import web
from telegram.ext import Updater

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global variables
LOCKFILE = "/tmp/stylish_name_bot.lock"
BOT_INSTANCE_ID = f"{os.getpid()}-{int(time.time())}"

def create_lock():
    """Create a lock file to prevent multiple instances."""
    try:
        if os.path.exists(LOCKFILE):
            # Read existing lock file
            with open(LOCKFILE, 'r') as f:
                existing_pid = f.read().strip()
            logger.info(f"Found existing lock file with PID: {existing_pid}")
            
            # Check if the process is still running
            try:
                pid = int(existing_pid.split('-')[0])
                os.kill(pid, 0)  # This will raise OSError if process is not running
                logger.error(f"Another bot instance is already running with PID {pid}")
                return False
            except (OSError, ValueError):
                logger.info("Existing lock is stale. Overwriting it.")
                pass  # Process not running, we can proceed
        
        # Create or update lock file
        with open(LOCKFILE, 'w') as f:
            f.write(BOT_INSTANCE_ID)
        logger.info(f"Lock file created with ID: {BOT_INSTANCE_ID}")
        
        # Register cleanup function to remove lock file on exit
        atexit.register(remove_lock)
        return True
    except Exception as e:
        logger.error(f"Error creating lock file: {e}")
        return False

def remove_lock():
    """Remove the lock file on exit."""
    try:
        if os.path.exists(LOCKFILE):
            with open(LOCKFILE, 'r') as f:
                if f.read().strip() == BOT_INSTANCE_ID:
                    os.remove(LOCKFILE)
                    logger.info("Lock file removed")
    except Exception as e:
        logger.error(f"Error removing lock file: {e}")

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
    'a': ['α', 'ą', 'å', 'à', 'á', 'â', 'ã', 'ä', 'æ', '𝗔', '𝐀', '𝘈', '𝘼', '𝔄', '𝕬', '𝔸', '🄰', 'Ⓐ', 'Ꭺ', 'а', 'Ａ', 'ん', 'Ⱥ', '𝙰', 'Ɦ', '𝚨', '𝜜', '𝖆', 'ꮧ', 'ค', 'ꞏ', 'ꋫ', 'ᗩ', 'ᵃ', 'ₐ', 'ᴀ', '🅐', 'Λ', 'ꋬ', 'ꍏ', 'ǟ', 'a̾', 'ꁲ'],
    'b': ['β', 'b̶', 'b̷', 'b̸', '𝗕', '𝐁', '𝘉', '𝘽', '𝔅', '𝕭', '𝔹', '🄱', 'Ⓑ', 'Ᏼ', 'в', 'Ｂ', '乃', 'Ƀ', '𝙱', 'Ꞗ', '𝚩', '𝜝', '𝖇', 'ꮄ', '๒', 'Ꮽ', 'ꃃ', 'ᗷ', 'ᵇ', 'ᵦ', 'ʙ', '🅑', 'ꋰ', 'ꃳ', 'ß', 'b̾', 'ꋍ'],
    'c': ['c̶', 'c̷', 'c̸', 'ç', '𝗖', '𝐂', '𝘊', '𝘾', 'ℭ', '𝕮', 'ℂ', '🄲', 'Ⓒ', 'Ꮯ', 'c', 'Ｃ', '匚', 'Ȼ', '𝙲', 'Ꮯ', '𝚪', '𝜞', '𝖈', 'ꮸ', 'ς', 'Ꮸ', 'ꉔ', 'ᑕ', 'ᶜ', 'ƈ', 'ᴄ', '🅒', '↻', 'ꏳ', '꒝', 'ƈ', 'c̾', 'ꇓ'],
    'd': ['d̶', 'd̷', 'd̸', 'đ', '𝗗', '𝐃', '𝘋', '𝘿', '𝔇', '𝕯', '𝔻', '🄳', 'Ⓓ', 'Ꭰ', 'd', 'Ｄ', '刀', 'Ꭰ', '𝙳', 'Ꭰ', '𝚫', '𝜟', '𝖉', 'ꮷ', '๔', 'Ꮄ', 'ꊱ', 'ᗪ', 'ᵈ', 'ɖ', 'ᴅ', '🅓', 'ꀸ', 'ꂠ', 'Ꭰ', 'd̾', 'ꅐ'],
    'e': ['ε', 'ę', 'è', 'é', 'ê', 'ë', '𝗘', '𝐄', '𝘌', '𝙀', '𝔈', '𝕰', '𝔼', '🄴', 'Ⓔ', 'Ꭼ', 'є', 'Ｅ', 'モ', 'Ɇ', '𝙴', 'ꞓ', '𝚬', '𝜠', '𝖊', 'ꮛ', 'є', 'Ꮛ', 'ꏂ', 'ᗴ', 'ᵉ', 'ₑ', 'ᴇ', '🅔', 'ꉢ', 'ꏼ', 'E', 'e̾', 'ꍟ'],
    'f': ['f̶', 'f̷', 'f̸', '𝗙', '𝐅', '𝘍', '𝙁', '𝔉', '𝕱', '𝔽', '🄵', 'Ⓕ', 'Ꮄ', 'f', 'Ｆ', '下', 'Ϝ', '𝙵', 'Ꞙ', '𝚭', '𝜡', '𝖋', 'ꞙ', 'Ŧ', 'Ꞧ', 'ꎇ', 'ᖴ', 'ᶠ', 'ꎇ', 'ғ', '🅕', 'ꉱ', 'ꄞ', 'F', 'f̾', 'ꄲ'],
    'g': ['g̶', 'g̷', 'g̸', '𝗚', '𝐆', '𝘎', '𝙂', '𝔊', '𝕲', '𝔾', '🄶', 'Ⓖ', 'Ꮆ', 'g', 'Ｇ', 'ら', 'Ǥ', '𝙶', 'Ꞡ', '𝚮', '𝜢', '𝖌', 'ꮆ', 'ﻮ', 'Ꮑ', 'ꁅ', 'ᘜ', 'ᵍ', 'ɢ', '🅖', 'ꀯ', 'ꍌ', 'g', 'g̾', 'ꁅ'],
    'h': ['h̶', 'h̷', 'h̸', '𝗛', '𝐇', '𝘏', '𝙃', '𝔥', '𝕳', 'ℍ', '🄷', 'Ⓗ', 'Ꮋ', 'н', 'Ｈ', 'ん', 'Ȟ', '𝙷', 'Ꞝ', '𝚯', '𝜣', '𝖍', 'ꮒ', 'ђ', 'Ꮵ', 'ꀍ', 'ᕼ', 'ʰ', 'ₕ', 'ʜ', '🅗', 'ꀍ', 'ꢻ', 'н', 'h̾', 'ꍩ'],
    'i': ['ι', 'ì', 'í', 'î', 'ï', '𝗜', '𝐈', '𝘐', '𝙄', '𝔦', '𝕴', '𝕀', '🄸', 'Ⓘ', 'Ꭵ', 'і', 'Ｉ', '工', 'ɨ', '𝙸', 'ɨ', '𝚰', '𝜤', '𝖎', 'ꭵ', 'เ', 'Ꭵ', 'ꀤ', 'ᓰ', 'ⁱ', 'ᵢ', 'ɪ', '🅘', 'ꂦ', 'ⅈ', 'i', 'i̾', 'ꀤ'],
    'j': ['j̶', 'j̷', 'j̸', '𝗝', '𝐉', '𝘑', '𝙅', '𝔍', '𝕵', '𝕁', 'Ĵ', 'Ⓙ', 'Ꭻ', 'ј', 'Ｊ', 'ﾌ', 'Ɉ', '𝙹', 'Ꞥ', '𝚱', '𝜥', '𝖏', 'ꭻ', 'ן', 'Ꮴ', 'ꀭ', 'ᒍ', 'ʲ', 'ⱼ', 'ᴊ', '🅙', 'ꋊ', 'ꀭ', 'j', 'j̾', 'ꈤ'],
    'k': ['k̶', 'k̷', 'k̸', '𝗞', '𝐊', '𝘒', '𝙆', '𝔎', '𝕶', '𝕂', '🄺', 'Ⓚ', 'Ꮶ', 'к', 'Ｋ', '𝕜', 'Қ', '𝙺', 'Ꮶ', '𝚲', '𝜦', '𝖐', 'ꮶ', 'к', 'Ꮵ', 'ꀘ', 'ᛕ', 'ᵏ', 'ₖ', 'ᴋ', '🅚', 'ꀘ', 'ꋊ', 'к', 'k̾', 'ꀘ'],
    'l': ['l̶', 'l̷', 'l̸', 'ł', '𝗟', '𝐋', '𝘓', '𝙇', '𝔏', '𝕷', '𝕃', '🄻', 'Ⓛ', 'Ꮮ', 'l', 'Ｌ', 'ㄥ', 'Ɬ', '𝙻', 'Ꮮ', '𝚳', '𝜧', '𝖑', 'ꮭ', 'l', 'Ꮗ', 'ꀤ', 'ᒪ', 'ˡ', 'ₗ', 'ʟ', '🅛', 'ꂖ', 'ꍂ', 'L', 'l̾', 'ꋊ'],
    'm': ['m̶', 'm̷', 'm̸', '𝗠', '𝐌', '𝘔', '𝙈', '𝔐', '𝕸', '𝕄', '🄼', 'Ⓜ️', 'Ꮇ', 'м', 'Ｍ', '爪', 'ϻ', '𝙼', 'Ɦ', '𝚴', '𝜨', '𝖒', 'ꮇ', '๓', 'Ꮇ', 'ꂵ', 'ᗰ', 'ᵐ', 'ₘ', 'ᴍ', '🅜', 'ꎭ', 'ꂵ', 'м', 'm̾', 'ꎭ'],
    'n': ['n̶', 'n̷', 'n̸', 'ñ', '𝗡', '𝐍', '𝘕', '𝙉', '𝔑', '𝕹', 'ℕ', '🄽', 'Ⓝ', 'Ꮑ', 'и', 'Ｎ', '凵', 'Ƞ', '𝙽', 'Ꞟ', '𝚵', '𝜩', '𝖓', 'ꮑ', 'ภ', 'Ꮑ', 'ꋊ', 'ᑎ', 'ⁿ', 'ₙ', 'ɴ', '🅝', 'ꋊ', 'ꃔ', 'и', 'n̾', 'ꉧ'],
    'o': ['ο', 'ò', 'ó', 'ô', 'õ', 'ö', 'ø', '𝗢', '𝐎', '𝘖', '𝙊', '𝔒', '𝕺', '𝕆', '🄾', 'Ⓞ', 'Ꮎ', 'o', 'Ｏ', '口', 'Ỗ', '𝙾', 'Ȣ', '𝚶', '𝜪', '𝖔', 'ꮻ', '๏', 'Ꭷ', 'ꄲ', 'ᗝ', 'ᵒ', 'ₒ', 'ᴏ', '🅞', 'ꂦ', 'ꁏ', 'о', 'o̾', 'ꄱ'],
    'p': ['p̶', 'p̷', 'p̸', '𝗣', '𝐏', '𝘗', '𝙋', '𝔓', '𝕻', 'ℙ', '🄿', 'Ⓟ', 'Ꮲ', 'р', 'Ｐ', 'や', 'ρ', '𝙿', 'Ꞓ', '𝚷', '𝜫', '𝖕', 'ꮲ', 'р', 'Ꮔ', 'ꉣ', 'ᑭ', 'ᵖ', 'ₚ', 'ᴘ', '🅟', 'ꉣ', 'ꋊ', 'p', 'p̾', 'ꉣ'],
    'q': ['q̶', 'q̷', 'q̸', '𝗤', '𝐐', '𝘘', '𝙌', '𝔔', '𝕼', 'ℚ', '🅀', 'Ⓠ', 'Ꮕ', 'q', 'Ｑ', '𝕜', 'Ϙ', '𝚀', 'Ʞ', '𝚸', '𝜬', '𝖖', 'ꮕ', 'ợ', 'Ꭴ', 'ꋠ', 'ᑫ', 'ᑫ', 'ᵠ', 'ǫ', '🅠', 'ꁷ', 'ꃛ', 'q', 'q̾', 'ꆛ'],
    'r': ['r̶', 'r̷', 'r̸', '𝗥', '𝐑', '𝘙', '𝙍', '𝔕', '𝕽', 'ℝ', '🅁', 'Ⓡ', 'Ꭱ', 'r', 'Ｒ', '尺', 'Ɍ', '𝚁', 'ꞣ', '𝚹', '𝜭', '𝖗', 'ꮢ', 'г', 'Ꮁ', 'ꋪ', 'ᖇ', 'ʳ', 'ᵣ', 'ʀ', '🅡', 'ꋪ', 'ꋊ', 'r', 'r̾', 'ꋪ'],
    's': ['s̶', 's̷', 's̸', 'š', '𝗦', '𝐒', '𝘚', '𝙎', '𝔖', '𝕾', '𝕊', '🅂', 'Ⓢ', 'Ꮪ', 'ѕ', 'Ｓ', 'ち', 'Ϟ', '𝚂', 'Ꞧ', '𝚺', '𝜮', '𝖘', 'ꮪ', 'ร', 'Ꮄ', 'ꌗ', 'ᔕ', 'ˢ', 'ₛ', 's', '🅢', 'ꉹ', 'ꌚ', 's', 's̾', 'ꌗ'],
    't': ['t̶', 't̷', 't̸', '𝗧', '𝐓', '𝘛', '𝙏', '𝔗', '𝕿', '𝕋', '🅃', 'Ⓣ', 'Ꮖ', 'т', 'Ｔ', '匕', 'Ͳ', '𝚃', 'ꞧ', '𝚻', '𝜯', '𝖙', 'ꮖ', 't', 'Ꮏ', '꓄', 'ᕋ', 'ᵗ', 'ₜ', 'ᴛ', '🅣', '꓄', 'ꋖ', 't', 't̾', '꓅'],
    'u': ['υ', 'ù', 'ú', 'û', 'ü', '𝗨', '𝐔', '𝘜', '𝙐', '𝔘', '𝖀', '𝕌', '🅄', 'Ⓤ', 'Ꮼ', 'υ', 'Ｕ', 'ひ', 'Ⴎ', '𝚄', 'Ꮜ', '𝚼', '𝜰', '𝖚', 'ꮜ', 'ย', 'Ꮀ', 'ꀎ', 'ᑌ', 'ᵘ', 'ᵤ', 'ᴜ', '🅤', 'ꀎ', 'ꏵ', 'u', 'u̾', 'ꀎ'],
    'v': ['v̶', 'v̷', 'v̸', '𝗩', '𝐕', '𝘝', '𝙑', '𝔙', '𝖁', '𝕍', '🅅', 'Ⓥ', 'Ꮩ', 'v', 'Ｖ', '∨', 'Ỽ', '𝚅', 'ꞥ', '𝚽', '𝜱', '𝖛', 'ꮩ', 'ש', 'Ꭽ', 'ꃴ', 'ᐯ', 'ᵛ', 'ᵥ', 'ᴠ', '🅥', 'ꀰ', 'ꏙ', 'v', 'v̾', 'ꁴ'],
    'w': ['w̶', 'w̷', 'w̸', '𝗪', '𝐖', '𝘞', '𝙒', '𝔚', '𝖂', '𝕎', '🅆', 'Ⓦ', 'Ꮃ', 'w', 'Ｗ', '山', 'Ѡ', '𝚆', 'Ѡ', '𝚾', '𝜲', '𝖜', 'ꮗ', 'ฝ', 'Ꮗ', 'ꅐ', 'ᗯ', 'ʷ', 'ₙ', 'ᴡ', '🅦', 'ꅐ', 'ꋬ', 'w', 'w̾', 'ꅐ'],
    'x': ['x̶', 'x̷', 'x̸', '𝗫', '𝐗', '𝘟', '𝙓', '𝔛', '𝖃', '𝕏', '🅇', 'Ⓧ', 'Ꮍ', 'х', 'Ｘ', 'メ', 'ϰ', '𝚇', 'Ꮍ', '𝚿', '𝜳', '𝖝', 'ꮂ', 'א', 'Ꮽ', 'ꊼ', '᙭', 'ˣ', 'ₓ', 'x', '🅧', 'ꊼ', 'ꏗ', 'х', 'x̾', 'ꊼ'],
    'y': ['y̶', 'y̷', 'y̸', 'ý', '𝗬', '𝐘', '𝘠', '𝙔', '𝔜', '𝖄', '𝕐', '🅈', 'Ⓨ', 'Ꮍ', 'у', 'Ｙ', 'ㄚ', 'Ϥ', '𝚈', 'Ꮓ', '𝛀', '𝜴', '𝖞', 'ꭹ', 'ץ', 'Ꭹ', 'ꐟ', 'ᖻ', 'ʸ', 'ᵧ', 'ʏ', '🅨', 'ꐞ', 'ꏯ', 'y', 'y̾', 'ꐧ'],
    'z': ['z̶', 'z̷', 'z̸', 'ž', '𝗭', '𝐙', '𝘡', '𝙕', '𝔷', '𝖅', 'ℤ', '🅉', 'Ⓩ', 'Ꮓ', 'z', 'Ｚ', '乙', 'ɀ', '𝚉', 'Ꮓ', '𝜵', '𝖟', 'ꮓ', 'չ', 'Ꮓ', 'ꓜ', 'Ꮓ', 'ᶻ', 'ᵣ', 'ᴢ', '🅩', 'ꁴ', 'ꁉ', 'z', 'z̾', 'ꑄ']
}

# New stylish fonts
STYLISH_FONTS = [
    "𝙉𝘼𝙈𝙀 𝙈𝘼𝙆𝙀𝙍",
    "ᶦ ͢ᵃᵐ⛦⃕‌!❛𝆺𝅥⤹࿗𓆪ꪾ™",
    "🔥!⃪⍣꯭꯭𓆪꯭🝐",
    "!✦ 𝆺𝅥⎯ꨄ",
    ".𝁘ໍ!𓆪ִֶָ ֺ⎯꯭‌ 𓆩💗𓆪𓈒",
    "𝅃꯭᳚𓄂️𝆺𝅥⃝🔥 ⃪ͥ͢ ᷟ𓆩 ! 乛|⁪⁬⁮⁮⁮⁮ ‌⁪⁬𓆪™",
    "𝅃꯭᳚🦁!˶꯭꯭꯭꯭꯭꯭֟፝͟͝ ⚡꯭꯭꯭꯭꯭",
    "❥‌‌❥ ⃝⃪⃕🦚⟵᷽᷍!˚‌‌‌‌◡‌⃝🐬᪳ ‌⃪𔘓❁‌‌❍•:➛",
    "𝅥‌꯭𝆬‌🦋⃪꯭ ─⃛͢┼ 𝞄⃕𝖋𝖋 !🥵⃝⃝ᬽ꯭ ⃪꯭ ꯭𝅥‌꯭𝆬‌➺꯭⎯⎯᪵᪳",
    "𝅃!™ ٭ - 𓆪ꪾ⌯ 🜲 ˹ 𝐎ᴘ ˼",
    "𝐈тᷟʑ꯭ͤ𓄂︪︫︠𓆩〭〬!⍣⃪͜ ꭗ̥̽𝆺꯭𝅥𔘓༌🪽⎯꯭̽⎯꯭ ꯭",
    "𓏲!𓂃ֶꪳ 𓆩〭〬🦋𓆪ꪾ",
    "⎯꯭꯭֯‌⌯ !𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    "𝆺𝅥⃝🤍 ⃪ͥ͢ ᷟ ●!🤍᪳𝆺꯭𝅥⎯꯭̽⎯꯭",
    "⋆⎯፝֟፝֟⎯᪵ 𝆺꯭𝅥! ᭄꯭🦋꯭᪳᪳᪻⎯̽⎯🐣",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !⎯᳝֟፝֟⎯‌ꭙ⋆\"🔥",
    "⟶̽ꭙ⋆\"🔥𓆩〬 !🤍᪳𝆺꯭𝅥⎯᳝֟፝֟⎯‌",
    "─፝─᪵།‌꯭! ا۬͢𝆺𝅥⃝🌸𝄄꯭꯭𝄄꯭꯭ ̶꯭𝅥ͦ 𝆬👑",
    ".𝁘ໍ!ꨄ 🦋𓂃•",
    "⟶̽𓆩〬𝁘ໍ!𓂃˖ॐ🪼⎯᳝֟፝⎯‌ꭙ⋆\"",
    "͟͞ !𓂃 🔥𝆺𝅥 🜲 ⌯",
    "⎯꯭꯭֯‌!𓂃ֶꪳ 𓆩〭〬🔥𓆪ꪾ",
    ".𝁘ໍ⎯꯭̽- !⌯ 𝘅𝗗 𓂃⎯꯭‌ ִֶָ ֺ🎀",
    "❛ ⟶̽! ❜ 🌙⤹🌸",
    "⏤͟͞●!●───♫▷",
    "𝐓𝐫𝐚𝐝𝐢𝐭𝐢𝐨𝐧𝐚𝐥 𝐁𝐨𝐥𝐝: 𝐍𝐀𝐌𝐄",
    "𝑇𝑟𝑎𝑑𝑖𝑡𝑖𝑜𝑛𝑎𝑙 𝐼𝑡𝑎𝑙𝑖𝑐: 𝑁𝐴𝑀𝐸",
    "𝑻𝒓𝒂𝒅𝒊𝒕𝒊𝒐𝒏𝒂𝒍 𝑩𝒐𝒍𝒅 𝑰𝒕𝒂𝒍𝒊𝒄: 𝑵𝑨𝑴𝑬",
    "ᴛʀᴀᴅɪᴛɪᴏɴᴀʟ sᴍᴀʟʟᴄᴀᴘs: ɴᴀᴍᴇ",
    "ₜᵣₐdᵢₜᵢₒₙₐₗ ₛᵤbₛcᵣᵢₚₜ: ₙₐₘₑ",
    "ᵗʳᵃᵈⁱᵗⁱᵒⁿᵃˡ ˢᵘᵖᵉʳˢᶜʳⁱᵖᵗ: ⁿᵃᵐᵉ",
    "𝓣𝓻𝓪𝓭𝓲𝓽𝓲𝓸𝓷𝓪𝓵 𝓢𝓬𝓻𝓲𝓹𝓽: 𝓝𝓐𝓜𝓔",
    "𝕋𝕣𝕒𝕕𝕚𝕥𝕚𝕠𝕟𝕒𝕝 𝔻𝕠𝕦𝕓𝕝𝕖: ℕ𝔸𝕄𝔼",
    "Ⓣⓡⓐⓓⓘⓣⓘⓞⓝⓐⓛ Ⓒⓘⓡⓒⓛⓔⓓ: ⓃⒶⓂⒺ",
    "🅣🅡🅐🅓🅘🅣🅘🅞🅝🅐🅛 🅢🅠🅤🅐🅡🅔🅓: 🅝🅐🅜🅔",
    "𝗧𝗿𝗮𝗱𝗶𝘁𝗶𝗼𝗻𝗮𝗹 𝗦𝗮𝗻𝘀 𝗕𝗼𝗹𝗱: 𝗡𝗔𝗠𝗘",
    "𝘛𝘳𝘢𝘥𝘪𝘵𝘪𝘰𝘯𝘢𝘭 𝘚𝘢𝘯𝘴 𝘐𝘵𝘢𝘭𝘪𝘤: 𝘕𝘈𝘔𝘌",
    "𝗕𝗼𝗹𝗱 𝗦𝗮𝗻𝘀: 𝗡𝗔𝗠𝗘",
    "𝐁𝐨𝐥𝐝 𝐒𝐞𝐫𝐢𝐟: 𝐍𝐀𝐌𝐄",
    "𝘊𝘰𝘥𝘦𝘥 𝘐𝘵𝘢𝘭𝘪𝘤: 𝘕𝘈𝘔𝘌",
    "𝘿𝙚𝙣𝙨𝙚 𝙄𝙩𝙖𝙡𝙞𝙘: 𝙉𝘼𝙈𝙀",
    "𝔉𝔯𝔞𝔠𝔱𝔲𝔯 𝔊𝔬𝔱𝔥𝔦𝔠: 𝔑𝔄𝔐𝔈",
    "𝕭𝖑𝖆𝖈𝖐𝖑𝖊𝖙𝖙𝖊𝖗: 𝕹𝕬𝕸𝕰",
    "ℍ𝕠𝕡𝕡𝕪 𝔻𝕠𝕦𝕓𝕝𝕖: ℕ𝔸𝕄𝔼",
    "🅂🆀🆄🅰️🆁🅴🆂: 🄽🄰🄼🄴",
    "ⒸⒾⓇⒸⓁⒺⒹ: ⓃⒶⓂⒺ",
    "Ꮒꮛꮛꮢ ᏚꮯꮢꭵᏢᏆ: ᏁᎪᎷᎬ",
    "нєєя ƒαη¢у: иαмє",
    "Ｆｕｌｌ　Ｗｉｄｔｈ: ＮＡＭＥ",
    "ん乇乇尺 Jαραɳҽʂҽ: 刀卂爪乇",
    "ɦεε૨ ɭεεͳ: ȵȺɱΣ",
    "𝚂𝚖𝚊𝚕𝚕 𝙲𝚊𝚙𝚜: 𝙽𝙰𝙼𝙴",
    "Ꞓɇłŧɨȼ Șŧɏłɇ: ꞐȺⱮɆ",
    "𝚪𝚸𝚬𝚬𝚱: 𝚴𝚨𝚳𝚬",
    "𝜧𝜶𝜻𝜣 𝜮𝜸𝜹𝜾𝜫𝜻: 𝜨𝜜𝜧𝜠",
    "Ⲙⲓⲭⲉⲇ Ⲧⲩⲡⲉ: ⲚⲀⲘⲈ",
    "U̶n̶i̶c̶o̶d̶e̶ C̶o̶r̶r̶u̶p̶t̶: NAME",
    "NAME Style with Stars",
    "▌│█║▌║▌║ NAME ║▌║▌║█│▌",
    "▁ ▂ ▄ ▅ ▆ ▇ █ NAME █ ▇ ▆ ▅ ▄ ▂ ▁",
    "BoxStyle NAME BoxStyle",
    "꧁༒☬ NAME ☬༒꧂",
    "░▒▓█►─═  NAME ═─◄█▓▒░",
    "✿❀ NAME ❀✿",
    "Special NAME Style",
    "✰✰NAME✰✰"
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
        # Check if another instance is running
        if not create_lock():
            logger.error("Another bot instance is already running. Exiting.")
            return

        # Create the Application and pass it your bot's token
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
            return

        logger.info(f"Bot instance started with ID: {BOT_INSTANCE_ID}")
        logger.info("Bot token loaded successfully")
        logger.info("Initializing bot...")
        
        # Create application with custom settings to prevent conflicts
        application = (
            Application.builder()
            .token(token)
            .concurrent_updates(False)  # Process updates sequentially
            .build()
        )
        logger.info("Application built successfully")

        # Define shutdown handler
        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}. Shutting down gracefully.")
            remove_lock()
            sys.exit(0)
            
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

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
            return web.Response(text=f"Bot is running! Instance ID: {BOT_INSTANCE_ID}")
        
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
        
        # Run the bot with specific ID to prevent conflicts
        logger.info("Starting bot polling...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            pool_timeout=30,  # Shorter pool timeout
            read_timeout=7,   # Shorter read timeout
            write_timeout=5,  # Shorter write timeout
            connect_timeout=5, # Shorter connect timeout
            poll_interval=1.0 # Shorter poll interval
        )
        logger.info("Bot polling stopped")
    
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
    finally:
        logger.info("Application stopped")
        remove_lock()  # Ensure lock is removed

if __name__ == '__main__':
    main() 