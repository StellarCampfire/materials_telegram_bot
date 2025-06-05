import logging
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, ContextTypes, filters
from logging.handlers import RotatingFileHandler
from database import Database

# Loading variables from .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')

# Token check
if not PAYMENT_PROVIDER_TOKEN:
    raise ValueError("PAYMENT_PROVIDER_TOKEN не указан в .env")

# Configure logging 
LOG_FILE = "/app/data/bot.log"
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)  # 5MB per file, keep 5 backups
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Show logs in console in utf-8
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
console_handler.stream.reconfigure(encoding='utf-8')
logger.addHandler(console_handler)

# Databse connecting
db = Database()

# Sending start message an material list
async def send_start_msg(telegramObject, reply_markup):
    username = telegramObject.from_user.username

    start_message = (
        f"🔹 Привет, {username}! 🔹\n\n"
        "Ищешь материалы по 1С, чтобы быстрее разобраться, учиться или работать продуктивнее? 📚✨\n\n"
        "У меня для тебя — подборка лучших материалов:\n"
        "✅ Актуально\n"
        "✅ Проверено\n"
        "✅ Удобно и понятно\n\n"
        "💡 Выбирай нужный материал, смотри демо-версию и получай полный доступ — всё просто!\n\n"
        "👇 Нажми кнопку ниже и начни прямо сейчас!"
    )

    await telegramObject.message.reply_text(start_message, reply_markup=reply_markup)

# Form and sending materials list
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton(material.title, callback_data=str(material.id))] 
        for material in db.get_all_materials()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await send_start_msg(update, reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await send_start_msg(query, reply_markup)


# Handle press on material button
async def handle_material_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    id = int(query.data)
    material = db.get_material_by_id(id)
    
    # Creating buttons
    keyboard = [
        [InlineKeyboardButton("Скачать демо", callback_data=f'demo_{id}')],
        [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{id}')],
        [InlineKeyboardButton("Вернуться к началу", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"{material.title}"
    if material.description:
        caption += f"\n\n{material.description}"

    await query.answer()
    try:
        # sending material description and image message
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=material.img_link,
            caption=caption[:1024],  # telegram symbols in message limit
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error while image sending: {e}")
        # Sendign only description text
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=caption[:4096],  # telegram symbols in message limit
            reply_markup=reply_markup
        )
    


async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    id = int(query.data.split('_')[1])
    material = db.get_material_by_id(id)
    username = query.from_user.username or query.from_user.first_name or str(query.from_user.id)
    
    await query.answer()
    # sending demo file url
    try:
        await query.message.reply_text(
            text=f"Вот ссылка на демо-версию материала:\n{material.demo_file_link}"
        )
        logger.info(f"Demo file link sent to {username} for {material.title} (ID: {id})")
    except Exception as e:
        logger.error(f"Error sending demo file link to {username} for {material.title} (ID: {id}): {e}, link: {material.demo_file_link}")
        await query.message.reply_text("Ошибка при отправке ссылки на демо-файл.")
        return

# Forming Payment Request
async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    materialId = int(query.data.split('_')[1])
    material = db.get_material_by_id(materialId)
    username = query.from_user.username or query.from_user.first_name or str(query.from_user.id)
    
    await query.answer()
    try:
        # sending invoice
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=material.title,
            description=material.title + " - full version.",
            payload=material.id,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=[{'label': 'Цена', 'amount': material.price}],
            # Для продакшена ЮKassa требует provider_data для чека, пример:
            need_email = True,
            send_email_to_provider = True,
            provider_data = {
                "receipt": {
                    "items": [
                        {
                            "description": material.title,
                            "quantity": "1.00",
                            "amount": {
                                "value": str(material.price / 100.0),
                                "currency": "RUB"
                            },
                            "vat_code": 1  # Без НДС для цифровых товаров
                        }
                    ]
                }
            }
        )
        logger.info(f"Invoice sent to {username} for {material.title} (ID: {material.id}, amount: {material.price/100} RUB)")
    except Exception as e:
        logger.error(f"Error sending invoice to {username} for {material.title} (ID: {material.id}): {e}")
        await query.message.reply_text(f"Произошла ошибка при создании счёта: {str(e)}. Попробуйте позже.")

# Check before payment
async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)

# Handle successfull payment
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.successful_payment:        
        try:
            payment = update.message.successful_payment
            materialId = int(payment.invoice_payload)
            
            username = update.message.from_user.username or update.message.from_user.first_name or str(update.message.from_user.id)
            amount = payment.total_amount / 100

            material = db.get_material_by_id(materialId)
            if material is None:
                raise Exception(f"Error after Successful payment by @{username}, summ: {amount} RUB. No such matherial with ID {materialId}")

            keyboard = [[InlineKeyboardButton("Вернуться к началу", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text=f"Спасибо за покупку! Вот полный материал {material.title}:\n{material.full_file_link}",
                reply_markup=reply_markup
            )

            logger.info(f"Successful payment by @{username} for Material(ID: '{material.title}', title: '{material.id}'), summ: {amount} RUB")
        except Exception as e:
            logger.error(f"Error while sending full material link: {e}")
            await update.message.reply_text("Ошибка при отправке файла. Свяжитесь с поддержкой.")



# Bot start
def main() -> None:
    if not TOKEN:
        raise ValueError("TOKEN не указан в .env")
    
    logger.info("Bot is starting...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_material_button, pattern=r'^(?!start$|demo_|buy_)[\w]+$'))
    application.add_handler(CallbackQueryHandler(handle_demo, pattern=r'^demo_'))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern=r'^buy_'))
    application.add_handler(CallbackQueryHandler(handle_start_button, pattern=r'^start$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(None, successful_payment_handler))

    logger.info("Bot started")
    
    application.run_polling()
    logger.info("Bot stopped")

if __name__ == '__main__':
    main()