import logging
import json
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, ContextTypes

# Загрузка переменных из .env
load_dotenv()

# Получение токенов из переменных окружения
TOKEN = os.getenv('TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка материалов из JSON
with open('materials.json', 'r', encoding='utf-8') as f:
    MATERIALS = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - показывает список материалов"""
    keyboard = [[InlineKeyboardButton(MATERIALS[key]['title'], callback_data=key)] for key in MATERIALS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Привет! Выбери материал:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия на кнопку материала"""
    query = update.callback_query
    material_key = query.data
    material = MATERIALS[material_key]
    
    keyboard = [[InlineKeyboardButton("Скачать демо", callback_data=f'demo_{material_key}')],
                [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{material_key}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)


    await query.answer()
    if material.get('image_path') and os.path.exists(material['image_path']):
        with open(material['image_path'], 'rb') as image_file:
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=image_file,
                    caption=f"{material['title']}\n\n{material['description']}"
                ),
                reply_markup=reply_markup
            )
    else:
        await query.edit_message_text(
            text=f"{material['title']}\n\n{material['description']}",
            reply_markup=reply_markup
        )

async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка демо-файла"""
    query = update.callback_query
    material_key = query.data.split('_')[1]
    material = MATERIALS[material_key]
    
    await query.answer()
    with open(material['demo_file_path'], 'rb') as demo_file:
        await context.bot.send_document(chat_id=query.message.chat_id, document=demo_file,
                                       caption="Вот демо-версия материала!")
    await query.edit_message_text(text=f"{material['title']}\n\n{material['description']}", reply_markup=query.message.reply_markup)

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрос оплаты"""
    query = update.callback_query
    material_key = query.data.split('_')[1]
    material = MATERIALS[material_key]
    
    await query.answer()
    
    try:
        # Отправляем инвойс
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=material['title'],
            description=material['description'],
            payload=material_key,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=[{'label': 'Цена', 'amount': material['price']}],
        )
        logger.info(f"Инвойс отправлен для {material['title']} (ключ: {material_key})")
    except Exception as e:
        logger.error(f"Ошибка при отправке инвойса: {e}")
        await query.message.reply_text("Произошла ошибка при создании счёта. Попробуйте позже.")

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка перед оплатой"""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка успешной оплаты"""
    if update.message.successful_payment:
        payment = update.message.successful_payment
        material_key = payment.invoice_payload
        material = MATERIALS[material_key]
        
        with open(material['full_file_path'], 'rb') as full_file:
            await update.message.reply_document(document=full_file,
                                               caption=f"Спасибо за покупку! Вот полный материал: {material['title']}")

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и событий
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern=r'^(material1)$'))
    application.add_handler(CallbackQueryHandler(handle_demo, pattern=r'^demo_'))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern=r'^buy_'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(None, successful_payment_handler))

    # Запуск polling
    application.run_polling()

if __name__ == '__main__':
    main()