import os
import json
import requests
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8976916614:AAGJ1PowMhue-q2OMuOM7ToOI-r4p0RqlpY"

# Dictionary to store user data temporarily
user_data_store = {}

# Reply Keyboard markup (Buttons in English)
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("Set Password")],
        [KeyboardButton("Create Account")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome to Facebook Account Creator Bot!\n\n"
        "📌 Use the buttons below:\n"
        "• Set Password - Set your account password\n"
        "• Create Account - Create account with phone number",
        reply_markup=get_main_keyboard()
    )

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Main menu buttons (English)
    if text == "Set Password":
        context.user_data['awaiting_password'] = True
        await update.message.reply_text(
            "🔑 Please enter your desired password.\n\n"
            "Example: MySecurePass@123",
            reply_markup=get_main_keyboard()
        )
        return
        
    elif text == "Create Account":
        # Check if password is set
        if user_id not in user_data_store or not user_data_store[user_id].get('password'):
            await update.message.reply_text(
                "⚠️ Please set a password first! Click 'Set Password' button.",
                reply_markup=get_main_keyboard()
            )
            return
        
        context.user_data['awaiting_phone'] = True
        await update.message.reply_text(
            "📱 Please send the phone number.\n\n"
            "You can send in any format:\n"
            "+8801836483648\n"
            "or 8801836483648\n"
            "or 01836483648\n\n"
            "⚠️ I will use it exactly as you type.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Handle password input
    if context.user_data.get('awaiting_password'):
        password = text
        context.user_data['awaiting_password'] = False
        
        # Store password
        if user_id not in user_data_store:
            user_data_store[user_id] = {}
        user_data_store[user_id]['password'] = password
        
        await update.message.reply_text(
            f"✅ Password set successfully!\n\n"
            f"🔐 Password: `{password}`\n\n"
            f"Now click 'Create Account' button.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
    # Handle phone number input
    if context.user_data.get('awaiting_phone'):
        phone_number = text
        context.user_data['awaiting_phone'] = False
        
        # Get password
        password = user_data_store.get(user_id, {}).get('password')
        if not password:
            await update.message.reply_text(
                "⚠️ Password not found! Please set password again.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            "⏳ Creating account... Please wait...",
            reply_markup=get_main_keyboard()
        )
        
        # API call
        try:
            response = await create_account(phone_number, password)
            
            if response.get('success'):
                data = response
                # Format the response message
                result_text = (
                    f"✅ *Account Created Successfully!*\n\n"
                    f"👤 *NAME:* `{data.get('name', 'N/A')}`\n"
                    f"📱 *NUMBER:* `{data.get('phone', 'N/A')}`\n"
                    f"🆔 *UID:* `{data.get('uid', 'N/A')}`\n"
                    f"🔑 *PASSWORD:* `{data.get('password', 'N/A')}`\n"
                    f"🎂 *BIRTHDAY:* `{data.get('birthday', 'N/A')}`\n"
                    f"⏰ *TIME:* `{data.get('time', 'N/A')}`"
                )
                
                # Delete processing message
                await processing_msg.delete()
                
                # Send success message with monospace formatting
                await update.message.reply_text(
                    result_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_main_keyboard()
                )
                
            else:
                await processing_msg.edit_text(
                    f"❌ Failed to create account.\n\n"
                    f"Error: {response.get('message', 'Unknown error')}",
                    reply_markup=get_main_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            await processing_msg.edit_text(
                f"❌ An error occurred.\n\n"
                f"Error: {str(e)}",
                reply_markup=get_main_keyboard()
            )

async def create_account(phone, password):
    """Make API call to create Facebook account"""
    url = "https://account-submit.ai.studio/api/fb-creator/create"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; itel S665L Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.7922.199 Mobile Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Content-Type": "application/json",
        "sec-ch-ua-platform": "Android",
        "sec-ch-ua": "Not=A?Brand\";v=\"99\", \"Android WebView\";v=\"151\", \"Chromium\";v=\"151\"",
        "sec-ch-ua-mobile": "?1",
        "origin": "https://account-submit.ai.studio",
        "x-requested-with": "mark.via.gp",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://account-submit.ai.studio/",
        "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
        "priority": "u=1, i"
    }
    
    payload = {
        "phone": phone,
        "password": password
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return {"success": False, "message": str(e)}

# Handle unknown commands
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❓ Unknown command. Please use /start to begin.",
        reply_markup=get_main_keyboard()
    )

def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Register message handler for text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Start the Bot
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("✅ Bot is running!")

if __name__ == "__main__":
    main()