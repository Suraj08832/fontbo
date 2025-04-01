import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Hello! This is a simple test bot.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Error: TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    logger.info(f"Using token: {token[:5]}...{token[-5:]}")
    
    # Create application
    application = Application.builder().token(token).build()

    # Add command handler
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot polling...")
    application.run_polling(poll_interval=5.0, timeout=30)
    logger.info("Bot polling stopped")

if __name__ == '__main__':
    main() 