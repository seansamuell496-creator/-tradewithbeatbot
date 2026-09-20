import os
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Store active tests per user: {user_id: {"passage": str, "start_time": float}}
active_tests = {}

# Sample passages (add more for variety)
PASSAGES = [
    "The quick brown fox jumps over the lazy dog near the river bank.",
    "Programming is the art of telling another human what one wants the computer to do.",
    "Typing speed is measured in words per minute, where one word equals five characters.",
    "Learning to type without looking at the keyboard takes practice and patience.",
    "A journey of a thousand miles begins with a single step forward.",
    "The best way to predict the future is to invent it through consistent effort.",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with a Start Test button."""
    keyboard = [
        [InlineKeyboardButton("Start Test", callback_data="start_test")],
        [InlineKeyboardButton("Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to Typing Speed Test!\n\n"
        "Measure your WPM (words per minute) and accuracy.\n"
        "Click Start Test to begin.",
        reply_markup=reply_markup,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message."""
    await update.message.reply_text(
        "How to use this bot:\n\n"
        "1. Send /start\n"
        "2. Click Start Test\n"
        "3. Type the passage exactly as shown\n"
        "4. Send your typed text\n"
        "5. Get your WPM and accuracy\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/help - This message",
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == "start_test":
        await begin_test(query, context)
    elif query.data == "help":
        await query.edit_message_text(
            "How to use:\n"
            "1. Click Start Test\n"
            "2. Type the passage\n"
            "3. Send your text\n"
            "4. Get results\n\n"
            "Use /start to return to the menu.",
        )

async def begin_test(query, context):
    """Send a random passage for the user to type."""
    user_id = query.from_user.id
    passage = random.choice(PASSAGES)
    active_tests[user_id] = {"passage": passage, "start_time": time.time()}

    await query.edit_message_text(
        f"Type the following passage as fast and accurately as you can:\n\n"
        f"{passage}\n\n"
        f"Send your typed text when ready.",
    )

async def handle_typed_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user's typed text and calculate WPM and accuracy."""
    user_id = update.effective_user.id

    if user_id not in active_tests:
        await update.message.reply_text(
            "Please click /start and then Start Test first."
        )
        return

    test = active_tests.pop(user_id)
    original = test["passage"]
    elapsed = time.time() - test["start_time"]
    typed = update.message.text

    # Calculate accuracy: matching characters / total original characters
    correct = sum(1 for a, b in zip(original, typed) if a == b)
    accuracy = (correct / len(original)) * 100 if original else 0

    # Standard WPM: (total characters / 5) / minutes
    minutes = elapsed / 60
    wpm = (len(typed) / 5) / minutes if minutes > 0 else 0

    keyboard = [[InlineKeyboardButton("Try Again", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Results:\n\n"
        f"WPM: {wpm:.1f}\n"
        f"Accuracy: {accuracy:.1f}%\n"
        f"Time: {elapsed:.1f}s\n\n"
        f"Original ({len(original)} chars):\n{original}\n\n"
        f"You typed ({len(typed)} chars):\n{typed}",
        reply_markup=reply_markup,
    )

def main():
    """Start the bot using long polling."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Callback query handler for inline buttons
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Message handler for typed text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_typed_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
