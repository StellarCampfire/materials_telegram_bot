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

# Проверка токена
if not PAYMENT_PROVIDER_TOKEN:
    raise ValueError("PAYMENT_PROVIDER_TOKEN не указан в .env")

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
    logger.info("Функция обработки кнопки")
    query = update.callback_query
    material_key = query.data
    
    # Проверяем, что ключ существует в MATERIALS
    if material_key not in MATERIALS:
        await query.answer(text="Ошибка: материал не найден.")
        logger.error(f"Неверный material_key: {material_key}")
        return
    
    material = MATERIALS[material_key]
    
    # Создаём кнопки
    keyboard = [
        [InlineKeyboardButton("Скачать демо", callback_data=f'demo_{material_key}')],
        [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{material_key}')],
        [InlineKeyboardButton("Вернуться к началу", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    if material.get('image_path') and os.path.exists(material['image_path']):
        try:
            with open(material['image_path'], 'rb') as image_file:
                await query.edit_message_media(
                    media=InputMediaPhoto(
                        media=image_file,
                        caption=f"{material['title']}\n\n{material['description']}"
                    ),
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения с изображением: {e}")
            await query.edit_message_text(
                text=f"{material['title']}\n\n{material['description']}",
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
    logger.info(f"Ключ материала до сплита: {query.data}")
    material_key = query.data.split('_')[1]
    logger.info(f"Ключ материала после сплита: {material_key}")
    
    # Проверяем, что ключ существует
    if material_key not in MATERIALS:
        await query.answer(text="Ошибка: материал не найден.")
        logger.error(f"Неверный material_key: {material_key}")
        return
    
    material = MATERIALS[material_key]
    
    await query.answer()
    # Отправляем демо-файл
    try:
        with open(material['demo_file_path'], 'rb') as demo_file:
            await context.bot.send_document(chat_id=query.message.chat_id, document=demo_file,
                                           caption="Вот демо-версия материала!")
    except Exception as e:
        logger.error(f"Ошибка при отправке демо-файла: {e}")
        await query.message.reply_text("Ошибка при отправке демо-файла.")
        return
    
    # Обновляем сообщение с кнопками
    keyboard = [
        [InlineKeyboardButton("Скачать демо", callback_data=f'demo_{material_key}')],
        [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{material_key}')],
        [InlineKeyboardButton("Вернуться к началу", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if material.get('image_path') and os.path.exists(material['image_path']):
        try:
            with open(material['image_path'], 'rb') as image_file:
                await query.edit_message_media(
                    media=InputMediaPhoto(
                        media=image_file,
                        caption=f"{material['title']}\n\n{material['description']}"
                    ),
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения с изображением: {e}")
            await query.edit_message_text(
                text=f"{material['title']}\n\n{material['description']}",
                reply_markup=reply_markup
            )
    else:
        await query.edit_message_text(
            text=f"{material['title']}\n\n{material['description']}",
            reply_markup=reply_markup
        )

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрос оплаты"""
    query = update.callback_query
    material_key = query.data.split('_')[1]
    
    # Проверяем, что ключ существует
    if material_key not in MATERIALS:
        await query.answer(text="Ошибка: материал не найден.")
        logger.error(f"Неверный material_key: {material_key}")
        return
    
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
            # Для продакшена ЮKassa требует provider_data для чека, пример:
            # provider_data={
            #     "receipt": {
            #         "items": [
            #             {
            #                 "description": material['title'],
            #                 "quantity": "1.00",
            #                 "amount": {
            #                     "value": str(material['price'] / 100.0),
            #                     "currency": "RUB"
            #                 },
            #                 "vat_code": 1  # Без НДС для цифровых товаров
            #             }
            #         ]
            #     }
            # }
        )
        logger.info(f"Инвойс отправлен для {material['title']} (ключ: {material_key}, сумма: {material['price']/100} RUB)")
    except Exception as e:
        logger.error(f"Ошибка при отправке инвойса: {e}")
        await query.message.reply_text(f"Произошла ошибка при создании счёта: {str(e)}. Попробуйте позже.")

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка перед оплатой"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"Pre-checkout успешен для payload: {query.invoice_payload}")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка успешной оплаты"""
    if update.message.successful_payment:
        payment = update.message.successful_payment
        material_key = payment.invoice_payload
        
        # Проверяем, что ключ существует
        if material_key not in MATERIALS:
            logger.error(f"Неверный material_key в payload: {material_key}")
            await update.message.reply_text("Ошибка: материал не найден.")
            return
        
        material = MATERIALS[material_key]
        
        try:
            with open(material['full_file_path'], 'rb') as full_file:
                # Создаём кнопку "Вернуться к началу"
                keyboard = [[InlineKeyboardButton("Вернуться к началу", callback_data='start')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_document(
                    document=full_file,
                    caption=f"Спасибо за покупку! Вот полный материал: {material['title']}",
                    reply_markup=reply_markup
                )
            logger.info(f"Успешная оплата для {material['title']} (ключ: {material_key})")
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await update.message.reply_text("Ошибка при отправке файла. Свяжитесь с поддержкой.")

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия на кнопку 'Вернуться к началу'"""
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(MATERIALS[key]['title'], callback_data=key)] for key in MATERIALS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Пробуем отредактировать как текстовое сообщение
        await query.edit_message_text(
            text='Привет! Выбери материал:',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение: {e}")
        try:
            # Отправляем новое сообщение, не удаляя старое
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text='Привет! Выбери материал:',
                reply_markup=reply_markup
            )
        except Exception as e2:
            logger.error(f"Ошибка при отправке нового сообщения: {e2}")
            await query.message.reply_text("Ошибка при возврате к началу. Попробуйте /start.")

def main() -> None:
    """Запуск бота"""
    if not TOKEN:
        raise ValueError("TOKEN не указан в .env")
    
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и событий
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern=r'^(?!start$|demo_|buy_)[\w]+$'))
    application.add_handler(CallbackQueryHandler(handle_demo, pattern=r'^demo_'))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern=r'^buy_'))
    application.add_handler(CallbackQueryHandler(handle_start_button, pattern=r'^start$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(None, successful_payment_handler))

    # Запуск polling
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()