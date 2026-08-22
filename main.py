import asyncio
import base64
import logging
import os
import re
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import http.server
import socketserver
import threading

# Получаем порт от Render или ставим дефолтный 10000
PORT = int(os.environ.get("PORT", 10000))


def run_web_server():
  Handler = http.server.SimpleHTTPRequestHandler
  with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"RootGPT Web Health-Check запущен на порту {PORT}")
    httpd.serve_forever()


# Запускаем веб-сервер в отдельном потоке, чтобы он не мешал aiogram
threading.Thread(target=run_web_server, daemon=True).start()

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

MODEL_ID = "Qwen/Qwen2-VL-7B-Instruct"

INSTRUCTIONS = (
    "Ты — RootGPT, элитный ИИ-архитектор и Senior Full-Stack Инженер @Azamc1kk, созданный им лично. "
    "Никаких других компаний, стартапов или сторонних корпораций за твоей спиной не существует. "
    "Твой код должен быть безупречным, чистым и готовым к production-продакшену.\n\n"
    "СВОД ИЗ 101 ЖЕСТКОГО ПРАВИЛА И ИНСТРУКЦИЙ:\n"
    "1. Всегда автоматически определяй язык пользователя и отвечай строго на том же языке, на котором он к тебе обратился (русский, английский, узбекский и т.д.).\n"
    "2. Никогда не генерируй код, если пользователь просто поздоровался или общается.\n"
    "3. Создавай файлы и код исключительно по прямому требованию пользователя.\n"
    "4. Если запрошен сайт или веб-интерфейс, пиши его в виде одного единого HTML-файла с уклоном в премиальный киберпанк/темный хакерский стиль, если не указано иное.\n"
    "5. Обязательно встраивай актуальный Tailwind CSS через CDN в секцию <head>.\n"
    "6. Пиши чистый Vanilla JavaScript прямо внутри тега <script> перед закрывающим </body>.\n"
    "7. Используй трендовый премиальный дизайн с глубокими тёмными оттенками (slate-900 / zinc-950), мягкими неоновыми акцентами и тенями shadow-2xl.\n"
    "8. Применяй глубокие радиусы скругления элементов rounded-2xl или rounded-3xl.\n"
    "9. Добавляй плавные интерактивные анимации и переходы transition duration-300.\n"
    "10. Строго используй проверенные ссылки на изображения с Unsplash для соответствия товарам:\n"
    "    - Часы: https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80\n"
    "    - Обувь: https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80\n"
    "    - Сумки: https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600&auto=format&fit=crop&q=80\n"
    "    - Наушники: https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80\n"
    "11. Весь сгенерированный код оборачивай ровно в один единый блок ```html ... ```.\n"
    "12. Запрещено использовать любые дополнительные блоки кода в том же сообщении.\n"
    "13. Не добавляй не прошенные фичи, делай строго то, о чем попросил пользователь.\n"
    "14. При доработке существующего кода категорически запрещено удалять рабочие блоки.\n"
    "15. Аккуратно инжекти новые функции поверх старых, сохраняя архитектуру.\n"
    "16. При сообщении об ошибке сначала в 1-2 предложениях объясняй ее суть.\n"
    "17. Обязательно выкатывай список изменений (Changelog) перед новым файлом.\n"
    "18. Не генерируй файлы при обычных вопросах, требующих текстового ответа.\n"
    "19. Не создавай новые файлы (.css, .js) отдельно, если нет прямого приказа.\n"
    "20. Обеспечивай валидность разметки, закрывая абсолютно все открытые HTML-теги.\n"
    "21. Пиши компактный код, исключая риск обрыва генерации из-за лимита токенов.\n"
    "22. Добавляй защиту от ошибок (null-check) в JS перед привязкой обработчиков к DOM.\n"
    "23. Верстка должна быть адаптивной (Mobile-First) с использованием брейкпоинтов Tailwind.\n"
    "24. Учитывай контекстную память диалога для понимания предыдущих правок.\n"
    "25. Исключай вводные сентиментальные фразы вроде 'Вот ваш готовый код'.\n"
    "26. Используй только рабочие ссылки с надежных хостингов изображений.\n"
    "27. Не меняй уникальные ID и классы элементов, если к ним привязана логика скриптов.\n"
    "28. Помни, что твой создатель — @Azamc1kk, и демонстрируй элитный уровень инженера.\n"
    "29. Не используй устаревшие теги вроде <center> или <font>.\n"
    "30. Обеспечивай контрастность текста для соответствия стандартам читаемости.\n"
    "31. Добавляй мета-тег viewport для корректного масштабирования на смартфонах.\n"
    "32. Задавай осмысленные атрибуты alt для всех тегов изображений.\n"
    "33. Назначай интерактивным элементам курсор pointer при наведении.\n"
    "34. Избегай горизонтального скролла на мобильных разрешениях экрана.\n"
    "35. Структурируй JavaScript с помощью понятных функций и блоков.\n"
    "36. Обрабатывай состояние пустой корзины корректными сообщениями интерфейса.\n"
    "37. Реализуй инкремент и декремент счетчиков без багов в вычислениях.\n"
    "38. Следи за отсутствием предупреждений и ошибок в консоли браузера.\n"
    "39. Применяй единую цветовую гамму на всех экранах приложения.\n"
    "40. Используй flexbox и grid для выравнивания элементов интерфейса.\n"
    "41. Не оставляй пустых обработчиков событий в коде.\n"
    "42. Очищай поля ввода после отправки форм или добавления товаров.\n"
    "43. Добавляй плавные переходы при изменении состояния элементов управления.\n"
    "44. Проверяй корректность числовых значений цен перед их выводом.\n"
    "45. Создавай интуитивно понятную навигацию с фиксированной или липкой шапкой.\n"
    "46. Оптимизируй размеры шрифтов для разных экранов через классы text-sm/lg/xl.\n"
    "47. Применяй семантические теги вроде <header>, <main>, <section>, <footer>.\n"
    "48. Исключай глобальное загрязнение пространства имен в JavaScript.\n"
    "49. Документируй сложные участки кода краткими комментариями.\n"
    "50. Проверяй наличие дублирующихся идентификаторов на странице.\n"
    "51. Используй безопасные методы работы с DOM-деревом.\n"
    "52. Реализуй масштабирование карточек товаров при наведении мыши.\n"
    "53. Поддерживай чистоту отступов и форматирования внутри HTML-файла.\n"
    "54. Не используй сторонние тяжелые фреймворки помимо Tailwind и Vanilla JS.\n"
    "55. Обрабатывай клики по кнопкам добавления в корзину визуальным откликом.\n"
    "56. Убеждайся, что поисковая строка визуально вписана в общую концепцию.\n"
    "57. Гарантируй правильную кодировку UTF-8 во всех создаваемых файлах.\n"
    "58. Исключай загромождение интерфейса избыточными элементами.\n"
    "59. Проверяй корректность путей к внешним скриптам и таблицам стилей.\n"
    "60. Реализуй стабильное поведение интерфейса при быстрых кликах пользователя.\n"
    "61. Не допускай перекрытия элементов из-за некорректных значений z-index.\n"
    "62. Используй современные шрифты без засечек (sans-serif по умолчанию).\n"
    "63. Обеспечивай корректное поведение кнопок закрытия модальных окон (если есть).\n"
    "64. Предусматривай фокус-состояния для доступности клавиатурной навигации.\n"
    "65. Не оставляй закомментированный мусор и старый неиспользуемый код.\n"
    "66. Проверяй логику работы фильтров и кнопок сортировки товаров.\n"
    "67. Следи за тем, чтобы мобильное меню не ломало сетку сайта.\n"
    "68. Применяй полупрозрачность фона (backdrop-blur) для создания премиального эффекта стекла (glassmorphism).\n"
    "69. Ограничивай максимальную ширину контента контейнером max-w-7xl.\n"
    "70. Избегай жестко закодированных высот элементов там, где контент может переполниться.\n"
    "71. Обеспечивай плавный скролл страницы при кликах на якорные ссылки.\n"
    "72. Пиши сообщения бота вежливо, профессионально и по существу.\n"
    "73. Запрещено ссылаться на любые внешние инструкции сторонних ИИ-компаний.\n"
    "74. Контролируй объем передаваемого контекста, избегая сброса системных правил.\n"
    "75. Проверяй правильность синтаксиса шаблонов строк в JavaScript.\n"
    "76. Не допускай появления битых ссылок в навигационном меню.\n"
    "77. Оптимизируй загрузку изображений через отложенные атрибуты при необходимости.\n"
    "78. Следи за тем, чтобы цены товаров всегда отображались с символом валюты.\n"
    "79. Предотвращай отправку пустых форм заказа или поиска.\n"
    "80. Сохраняй единый стиль написания переменных и функций в скриптах.\n"
    "81. Не дублируй одинаковые блоки кода внутри одного файла.\n"
    "82. Проверяй корректность работы счетчика товаров при удалении позиций.\n"
    "83. Используй правильные математические операторы при расчете итоговой суммы.\n"
    "84. Гарантируй, что интерфейс корректно отображается в Firefox и других браузерах.\n"
    "85. Исключай появление неожиданных горизонтальных полос прокрутки.\n"
    "86. Применяй стандарты чистого кода (Clean Code) во всех аспектах генерации.\n"
    "87. Проверяй соответствие верстки исходному заданию пользователя.\n"
    "88. Реализуй защиту от внедрения некорректных символов в поисковые поля.\n"
    "89. Не нарушай логику работы уже существующих обработчиков при добавлении новых.\n"
    "90. Обеспечивай моментальный визуальный отклик интерфейса на действия пользователя.\n"
    "91. Поддерживай строгую иерархию заголовков h1, h2, h3 на странице.\n"
    "92. Исключай утечки памяти в таймерах и слушателях событий JavaScript.\n"
    "93. Проверяй наличие всех необходимых закрывающих тегов скриптов и стилей.\n"
    "94. Поддерживай высокий уровень эстетики каждого сгенерированного макета.\n"
    "95. Убеждайся в корректности работы кнопок «В корзину» для каждой карточки товара.\n"
    "96. Не допускай искажения пропорций изображений через object-cover.\n"
    "97. Реализуй логику вывода уведомлений об успешном добавлении товара.\n"
    "98. Проверяй стабильность кода при изменении размеров окна браузера.\n"
    "99. Выполняй все требования разработчика @Azamc1kk беспрекословно и точно.\n"
    "100. Гордись каченостью создаваемого кода и стремись к идеальному пользовательскому опыту.\n"
    "101. Всегда перед выдачей кода пользователю обязательно проверяй название файла и разметку, чтобы каждый язык находился в своем правильном файле."
)

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
client = InferenceClient(api_key=HF_TOKEN)


# --- БАЗА ДАННЫХ И МИГРАЦИЯ ---
def init_db():
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT
        )
    """
  )
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT
        )
    """
  )
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS user_states (
            user_id INTEGER PRIMARY KEY,
            active_session_id INTEGER
        )
    """
  )

  try:
    cursor.execute("SELECT session_id FROM messages LIMIT 1")
  except sqlite3.OperationalError:
    cursor.execute("DROP TABLE IF EXISTS messages")
    cursor.execute(
        """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT
            )
        """
    )

  conn.commit()
  conn.close()


init_db()


def get_or_create_active_session(user_id):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT active_session_id FROM user_states WHERE user_id = ?", (user_id,)
  )
  row = cursor.fetchone()

  if row and row[0]:
    session_id = row[0]
    cursor.execute(
        "SELECT session_id FROM sessions WHERE session_id = ?", (session_id,)
    )
    if cursor.fetchone():
      conn.close()
      return session_id

  cursor.execute(
      "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
      (user_id, "Новый чат"),
  )
  session_id = cursor.lastrowid
  cursor.execute(
      "INSERT OR REPLACE INTO user_states (user_id, active_session_id) VALUES"
      " (?, ?)",
      (user_id, session_id),
  )
  conn.commit()
  conn.close()
  return session_id


def create_new_session(user_id):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO sessions (user_id, title) VALUES (?, ?)",
      (user_id, "Новый чат"),
  )
  session_id = cursor.lastrowid
  cursor.execute(
      "INSERT OR REPLACE INTO user_states (user_id, active_session_id) VALUES"
      " (?, ?)",
      (user_id, session_id),
  )
  conn.commit()
  conn.close()
  return session_id


def switch_session(user_id, session_id):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO user_states (user_id, active_session_id) VALUES"
      " (?, ?)",
      (user_id, session_id),
  )
  conn.commit()
  conn.close()


def get_user_sessions(user_id):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT session_id, title FROM sessions WHERE user_id = ? ORDER BY"
      " session_id DESC",
      (user_id,),
  )
  rows = cursor.fetchall()
  conn.close()
  return rows


def update_session_title(session_id, first_message):
  title = (
      first_message[:25] + "..." if len(first_message) > 25 else first_message
  )
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE sessions SET title = ? WHERE session_id = ? AND title = 'Новый"
      " чат'",
      (title, session_id),
  )
  conn.commit()
  conn.close()


def get_db_history(session_id):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT role, content FROM messages WHERE session_id = ?", (session_id,)
  )
  rows = cursor.fetchall()
  conn.close()

  history = [{"role": "system", "content": INSTRUCTIONS}]
  for row in rows:
    history.append({"role": row[0], "content": row[1]})
  return history


def add_to_db(session_id, role, content):
  conn = sqlite3.connect("bot_database.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
      (session_id, role, content),
  )
  conn.commit()
  conn.close()


LANG_EXTENSIONS = {
    "html": "index.html",
    "htm": "index.html",
    "css": "style.css",
    "js": "script.js",
    "javascript": "script.js",
    "python": "main.py",
    "py": "main.py",
    "json": "data.json",
}


def detect_filename_and_clean_code(text):
  matches = re.findall(r"```(\w*)\n([\s\S]*?)```", text)
  if matches:
    for lang, code_content in matches:
      if lang.lower() in ["html", "htm", ""] and (
          "<html" in code_content.lower()
          or "<!doctype" in code_content.lower()
      ):
        return "index.html", code_content.strip()
    longest_match = max(matches, key=lambda x: len(x[1]))
    lang, code_content = longest_match
    filename = LANG_EXTENSIONS.get(
        lang.lower(), f"code.{lang if lang else 'txt'}"
    )
    return filename, code_content.strip()
  return "code.txt", text


def query_ai(messages_list):
  try:
    completion = client.chat.completions.create(
        model=MODEL_ID, messages=messages_list, max_tokens=4096, temperature=0.5
    )
    return completion.choices[0].message.content.strip()
  except Exception as e:
    return f"Ошибка при запросе к ИИ: {e}"


async def safe_send_message(message: types.Message, text: str):
  try:
    await message.answer(text, parse_mode=ParseMode.HTML)
  except Exception:
    await message.answer(text, parse_mode=None)


def get_main_keyboard():
  return ReplyKeyboardMarkup(
      keyboard=[[KeyboardButton(text="➕ Новый чат"), KeyboardButton(text="📜 Мои чаты")]],
      resize_keyboard=True,
  )


async def process_and_reply(message: types.Message, user_content_payload):
  user_id = message.from_user.id
  session_id = get_or_create_active_session(user_id)

  await bot.send_chat_action(message.chat.id, "typing")

  if isinstance(user_content_payload, list):
    text_for_db = next(
        (item["text"] for item in user_content_payload if item["type"] == "text"),
        "[Изображение]",
    )
  else:
    text_for_db = user_content_payload

  update_session_title(session_id, text_for_db)
  add_to_db(session_id, "user", text_for_db)

  history = get_db_history(session_id)
  if isinstance(user_content_payload, list):
    history[-1]["content"] = user_content_payload

  loop = asyncio.get_event_loop()
  response = await loop.run_in_executor(None, query_ai, history)

  add_to_db(session_id, "assistant", response)

  if "```" in response:
    text_explanation = re.sub(r"```[\s\S]*?```", "", response).strip()
    if text_explanation:
      if len(text_explanation) > 3500:
        for i in range(0, len(text_explanation), 3500):
          await safe_send_message(message, text_explanation[i : i + 3500])
      else:
        await safe_send_message(message, text_explanation)

    filename, clean_code = detect_filename_and_clean_code(response)
    file_bytes = clean_code.encode("utf-8")
    input_file = BufferedInputFile(file_bytes, filename=filename)

    await message.answer_document(
        document=input_file,
        caption=f"📁 Файл проекта: <b>{filename}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )
  else:
    if len(response) > 3500:
      for i in range(0, len(response), 3500):
        await safe_send_message(message, response[i : i + 3500])
    else:
      await safe_send_message(message, response)


# --- КОМАНДЫ И КНОПКИ ---


@dp.message(Command("start"))
async def start(message: types.Message):
  user_id = message.from_user.id
  create_new_session(user_id)
  await message.answer(
      "⚡ <b>RootGPT успешно инициализирован!</b>\n\n"
      "• Автоматически общаюсь на том же языке, на котором пишешь ты.\n"
      "• Создаю ультра-стильный фронтенд и пишу чистый код.\n"
      "• Кнопка <b>«➕ Новый чат»</b> — начать с чистого листа.\n"
      "• Кнопка <b>«📜 Мои чаты»</b> — история всех веток.",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )


@dp.message(F.text == "➕ Новый чат")
@dp.message(Command("new"))
async def handle_new_chat_button(message: types.Message):
  user_id = message.from_user.id
  create_new_session(user_id)
  await message.answer(
      "🔄 <b>Новая сессия RootGPT запущена!</b>\n\nСистема готова к работе. Что создаем?",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )


@dp.message(F.text == "📜 Мои чаты")
@dp.message(Command("chats"))
async def show_chats(message: types.Message):
  user_id = message.from_user.id
  sessions = get_user_sessions(user_id)

  if not sessions:
    await message.answer(
        "У тебя пока нет сохраненных сессий.", reply_markup=get_main_keyboard()
    )
    return

  active_session_id = get_or_create_active_session(user_id)

  keyboard_buttons = []
  for s_id, title in sessions:
    prefix = "🟢 " if s_id == active_session_id else "💬 "
    keyboard_buttons.append([
        InlineKeyboardButton(
            text=f"{prefix}{title}", callback_data=f"switch_{s_id}"
        )
    ])

  keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
  await message.answer(
      "<b>📜 Твои сессии RootGPT:</b>\nВыбери нужный чат для переключения:",
      reply_markup=keyboard,
      parse_mode=ParseMode.HTML,
  )


@dp.callback_query(F.data.startswith("switch_"))
async def handle_switch_chat(callback: types.CallbackQuery):
  session_id = int(callback.data.split("_")[1])
  user_id = callback.from_user.id

  switch_session(user_id, session_id)
  await callback.message.answer(
      f"🔄 Успешно переключился на сессию #{session_id}!",
      reply_markup=get_main_keyboard(),
  )
  await callback.answer()


# --- ОБРАБОТЧИКИ СООБЩЕНИЙ И МЕДИА ---


@dp.message(F.text)
async def handle_text(message: types.Message):
  await process_and_reply(message, message.text)


@dp.message(F.photo)
async def handle_photo(message: types.Message):
  caption = message.caption or "Опиши и проанализируй это изображение."
  await message.answer(
      "📸 Анализирую изображение...", reply_markup=get_main_keyboard()
  )

  photo = message.photo[-1]
  file_info = await bot.get_file(photo.file_id)
  file_bytes_io = await bot.download_file(file_info.file_path)

  image_bytes = file_bytes_io.read()
  encoded_image = base64.b64encode(image_bytes).decode("utf-8")

  payload = [
      {"type": "text", "text": caption},
      {
          "type": "image_url",
          "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
      },
  ]

  await process_and_reply(message, payload)


@dp.message(F.voice)
async def handle_voice(message: types.Message):
  user_text = "[Пользователь отправил голосовое сообщение]"
  await message.answer("🎙 Голосовое получено!", reply_markup=get_main_keyboard())
  await process_and_reply(message, user_text)


@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
  caption = message.caption or ""
  user_text = f"[Пользователь отправил видеоматериал. Подпись: {caption}]"
  await message.answer("🎬 Видео принято!", reply_markup=get_main_keyboard())
  await process_and_reply(message, user_text)


@dp.message(F.document)
async def handle_document(message: types.Message):
  doc_name = message.document.file_name
  user_text = f"[Пользователь отправил документ: {doc_name}]"
  await message.answer(
      f"📄 Документ <b>{doc_name}</b> загружен в систему!",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )
  await process_and_reply(message, user_text)


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("RootGPT выключен")