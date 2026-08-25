import asyncio
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
    Update,
)
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from groq import AsyncGroq
import uvicorn

load_dotenv()

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PORT = int(os.environ.get("PORT", 10000))
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://root-gpt.onrender.com")
WEBHOOK_PATH = f"/bot/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# FastAPI & Groq Bot Initialization
app = FastAPI()
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

INSTRUCTIONS = (
    "You are RootGPT, an elite AI Architect and Senior Full-Stack Engineer created personally by @Azamc1kk. "
    "No other companies, startups, or third-party corporations exist behind your back. "
    "Your code must be flawless, clean, and production-ready.\n\n"
    "CODE OF 101 STRICT RULES AND INSTRUCTIONS:\n"
    "1. Always automatically detect the user's language and reply strictly in the same language they addressed you in (Russian, English, Uzbek, etc.).\n"
    "2. Never generate code if the user simply greeted you or is making small talk.\n"
    "3. Create files and code exclusively upon direct user request.\n"
    "4. If a website or web interface is requested, write it as a single unified HTML file with a slant toward a premium cyberpunk / dark hacker style unless specified otherwise.\n"
    "5. Be sure to embed current Tailwind CSS via CDN in the <head> section.\n"
    "6. Write clean Vanilla JavaScript directly inside the <script> tag before the closing </body>.\n"
    "7. Use a trendy premium design with deep dark tones (slate-900 / zinc-950), soft neon accents, and shadow-2xl shadows.\n"
    "8. Apply deep element rounding radii like rounded-2xl or rounded-3xl.\n"
    "9. Add smooth interactive animations and transitions using transition duration-300.\n"
    "10. Strictly use verified Unsplash image links matching products:\n"
    "    - Watch: https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80\n"
    "    - Shoes: https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80\n"
    "    - Bags: https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600&auto=format&fit=crop&q=80\n"
    "    - Headphones: https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80\n"
    "11. Wrap all generated code into exactly one single code block ```html ... ```.\n"
    "12. Prohibited to use any additional code blocks in the same message.\n"
    "13. Do not add unsolicited features; do strictly what the user asked.\n"
    "14. When modifying existing code, it is strictly forbidden to delete working blocks.\n"
    "15. Carefully inject new features over old ones while preserving the architecture.\n"
    "16. When reporting an error, first explain its essence in 1-2 sentences.\n"
    "17. Be sure to output a changelog before the new file.\n"
    "18. Do not generate files for regular questions requiring text answers.\n"
    "19. Do not create separate files (.css, .js) unless explicitly ordered.\n"
    "20. Ensure markup validity by closing absolutely all open HTML tags.\n"
    "21. Write compact code, eliminating the risk of generation cutoff due to token limits.\n"
    "22. Add error protection (null-check) in JS before binding event listeners to the DOM.\n"
    "23. Layout must be adaptive (Mobile-First) using Tailwind breakpoints.\n"
    "24. Account for dialog context memory to understand previous edits.\n"
    "25. Exclude introductory sentimental phrases like 'Here is your ready code'.\n"
    "26. Use only working links from reliable image hosting services.\n"
    "27. Do not change unique IDs and element classes if script logic is bound to them.\n"
    "28. Remember that your creator is @Azamc1kk and demonstrate an elite level of engineering.\n"
    "29. Do not use obsolete tags like <center> or <font>.\n"
    "30. Ensure text contrast to meet readability standards.\n"
    "31. Add viewport meta tag for correct scaling on smartphones.\n"
    "32. Assign meaningful alt attributes for all image tags.\n"
    "33. Assign pointer cursor on hover to interactive elements.\n"
    "34. Avoid horizontal scrolling on mobile screen resolutions.\n"
    "35. Structure JavaScript using clear functions and blocks.\n"
    "36. Handle empty cart states with correct interface messages.\n"
    "37. Implement counter increments and decrements without calculation bugs.\n"
    "38. Ensure absence of browser console warnings and errors.\n"
    "39. Apply a unified color scheme across all application screens.\n"
    "40. Use flexbox and grid for UI element alignment.\n"
    "41. Do not leave empty event handlers in code.\n"
    "42. Clear input fields after submitting forms or adding products.\n"
    "43. Add smooth transitions when changing control element states.\n"
    "44. Verify the correctness of price numeric values before displaying them.\n"
    "45. Create intuitive navigation with a fixed or sticky header.\n"
    "46. Optimize font sizes for different screens via text-sm/lg/xl classes.\n"
    "47. Apply semantic tags like <header>, <main>, <section>, <footer>.\n"
    "48. Exclude global namespace pollution in JavaScript.\n"
    "49. Document complex code sections with brief comments.\n"
    "50. Check for duplicate IDs on the page.\n"
    "51. Use safe DOM manipulation methods.\n"
    "52. Implement product card scaling on mouse hover.\n"
    "53. Maintain clean indentation and formatting inside the HTML file.\n"
    "54. Do not use heavy external frameworks besides Tailwind and Vanilla JS.\n"
    "55. Handle clicks on 'Add to Cart' buttons with visual feedback.\n"
    "56. Ensure the search bar is visually integrated into the overall concept.\n"
    "57. Guarantee correct UTF-8 encoding in all created files.\n"
    "58. Exclude interface clutter with redundant elements.\n"
    "59. Verify correct paths to external scripts and stylesheets.\n"
    "60. Implement stable UI behavior during rapid user clicks.\n"
    "61. Prevent element overlap due to incorrect z-index values.\n"
    "62. Use modern sans-serif fonts by default.\n"
    "63. Ensure correct behavior of modal close buttons (if any).\n"
    "64. Provide focus states for keyboard navigation accessibility.\n"
    "65. Do not leave commented garbage and old unused code.\n"
    "66. Check the logic of product filters and sorting buttons.\n"
    "67. Ensure the mobile menu does not break the site grid.\n"
    "68. Apply background transparency (backdrop-blur) to create a premium glassmorphism effect.\n"
    "69. Limit maximum content width with max-w-7xl container.\n"
    "70. Avoid hardcoded element heights where content can overflow.\n"
    "71. Ensure smooth page scrolling when clicking anchor links.\n"
    "72. Write bot messages politely, professionally, and to the point.\n"
    "73. Forbidden to reference any external instructions of third-party AI companies.\n"
    "74. Control the volume of transmitted context, avoiding system rule resets.\n"
    "75. Check the correct syntax of JavaScript template strings.\n"
    "76. Prevent broken links in the navigation menu.\n"
    "77. Optimize image loading via lazy attributes when necessary.\n"
    "78. Ensure product prices are always displayed with a currency symbol.\n"
    "79. Prevent submission of empty order or search forms.\n"
    "80. Maintain a consistent variable and function naming style in scripts.\n"
    "81. Do not duplicate identical code blocks within the same file.\n"
    "82. Verify correct product counter logic when removing items.\n"
    "83. Use correct mathematical operators when calculating totals.\n"
    "84. Guarantee that the interface displays correctly in Firefox and other browsers.\n"
    "85. Exclude unexpected horizontal scrollbars.\n"
    "86. Apply Clean Code standards in all aspects of generation.\n"
    "87. Verify layout compliance with user's initial task.\n"
    "88. Implement protection against injecting incorrect characters into search fields.\n"
    "89. Do not disrupt existing event handlers when adding new ones.\n"
    "90. Provide instant visual feedback from the interface to user actions.\n"
    "91. Maintain strict h1, h2, h3 header hierarchy on the page.\n"
    "92. Exclude memory leaks in JavaScript timers and event listeners.\n"
    "93. Check presence of all necessary closing script and style tags.\n"
    "94. Maintain a high level of aesthetics for every generated layout.\n"
    "95. Ensure correct operation of 'Add to Cart' buttons for each product card.\n"
    "96. Do not distort image proportions via object-cover.\n"
    "97. Implement notification logic for successful item addition.\n"
    "98. Check code stability when resizing the browser window.\n"
    "99. Execute all developer @Azamc1kk requirements implicitly and accurately.\n"
    "100. Take pride in the quality of created code and strive for an ideal user experience.\n"
    "101. Always verify the file name and markup before delivery so each language is in its correct file."
)

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


# --- DATABASE SETUP ---
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
      (user_id, "New Chat"),
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
      (user_id, "New Chat"),
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
      "UPDATE sessions SET title = ? WHERE session_id = ? AND title = 'New"
      " Chat'",
      (title, session_id),
  )
  conn.commit()
  conn.close()


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


# Robust Groq Query with Clean Error Handling
async def query_groq(session_id, current_payload):
  try:
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id"
        " ASC",
        (session_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    # Build messages array for Groq
    messages = [{"role": "system", "content": INSTRUCTIONS}]
    for r, c in rows:
      role = "user" if r == "user" else "assistant"
      messages.append({"role": role, "content": str(c)})

    # Append current message
    messages.append({"role": "user", "content": str(current_payload)})

    chat_completion = await groq_client.chat.completions.create(
        model="llama-3.1-8b-versatile",
        messages=messages,
        temperature=0.5,
        max_tokens=4096,
    )
    return chat_completion.choices[0].message.content
  except Exception as e:
    err_str = str(e)
    if "rate_limit" in err_str.lower() or "429" in err_str:
      return (
          "⚠️ <b>Groq Rate Limit Reached:</b> You have hit the limits for your"
          " Groq API key. Please wait a moment or check your Groq console."
      )
    return f"⚠️ An error occurred while communicating with Groq AI: {err_str}"


async def safe_send_message(message: types.Message, text: str):
  try:
    await message.answer(text, parse_mode=ParseMode.HTML)
  except Exception:
    await message.answer(text, parse_mode=None)


def get_main_keyboard():
  return ReplyKeyboardMarkup(
      keyboard=[
          [KeyboardButton(text="➕ New Chat"), KeyboardButton(text="📜 My Chats")]
      ],
      resize_keyboard=True,
  )


async def process_and_reply(message: types.Message, user_content_payload):
  user_id = message.from_user.id
  session_id = get_or_create_active_session(user_id)

  await bot.send_chat_action(message.chat.id, "typing")

  text_for_db = (
      str(user_content_payload)
      if not isinstance(user_content_payload, list)
      else user_content_payload[0]
  )

  update_session_title(session_id, text_for_db)
  add_to_db(session_id, "user", text_for_db)

  response = await query_groq(session_id, user_content_payload)

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
        caption=f"📁 Project file: <b>{filename}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(),
    )
  else:
    if len(response) > 3500:
      for i in range(0, len(response), 3500):
        await safe_send_message(message, response[i : i + 3500])
    else:
      await safe_send_message(message, response)


# --- COMMANDS ---


@dp.message(Command("start"))
async def start(message: types.Message):
  user_id = message.from_user.id
  create_new_session(user_id)
  await message.answer(
      "⚡ <b>RootGPT (Groq Llama 3.3 Edition) initialized via Webhooks!</b>\n\n"
      "• Powered by ultra-fast Groq Llama 3.3 70B.\n"
      "• Creates clean frontend code and architecture.\n"
      "• <b>«➕ New Chat»</b> — start fresh.\n"
      "• <b>«📜 My Chats»</b> — view and switch chat history.",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )


@dp.message(F.text == "➕ New Chat")
@dp.message(Command("new"))
async def handle_new_chat_button(message: types.Message):
  user_id = message.from_user.id
  create_new_session(user_id)
  await message.answer(
      "🔄 <b>New RootGPT session started!</b>\n\nSystem is ready. What are we"
      " building?",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )


@dp.message(F.text == "📜 My Chats")
@dp.message(Command("chats"))
async def show_chats(message: types.Message):
  user_id = message.from_user.id
  sessions = get_user_sessions(user_id)

  if not sessions:
    await message.answer(
        "You don't have any saved sessions yet.",
        reply_markup=get_main_keyboard(),
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
      "<b>📜 Your RootGPT Sessions:</b>\nSelect a chat to switch:",
      reply_markup=keyboard,
      parse_mode=ParseMode.HTML,
  )


@dp.callback_query(F.data.startswith("switch_"))
async def handle_switch_chat(callback: types.CallbackQuery):
  session_id = int(callback.data.split("_")[1])
  user_id = callback.from_user.id

  switch_session(user_id, session_id)
  await callback.message.answer(
      f"🔄 Successfully switched to session #{session_id}!",
      reply_markup=get_main_keyboard(),
  )
  await callback.answer()


# --- MESSAGE & MEDIA HANDLERS ---


@dp.message(F.text)
async def handle_text(message: types.Message):
  await process_and_reply(message, message.text)


@dp.message(F.photo)
async def handle_photo(message: types.Message):
  caption = message.caption or "Analyze this image."
  await message.answer(
      "📸 Image received (Groq text model active).",
      reply_markup=get_main_keyboard(),
  )
  await process_and_reply(message, f"[User sent an image with caption: {caption}]")


@dp.message(F.voice)
async def handle_voice(message: types.Message):
  await message.answer(
      "🎙 Voice message received!", reply_markup=get_main_keyboard()
  )
  await process_and_reply(message, "[User sent a voice message]")


@dp.message(F.video | F.video_note)
async def handle_video(message: types.Message):
  caption = message.caption or ""
  await message.answer("🎬 Video received!", reply_markup=get_main_keyboard())
  await process_and_reply(
      message, f"[User sent a video. Caption: {caption}]"
  )


@dp.message(F.document)
async def handle_document(message: types.Message):
  doc_name = message.document.file_name
  await message.answer(
      f"📄 Document <b>{doc_name}</b> uploaded!",
      reply_markup=get_main_keyboard(),
      parse_mode=ParseMode.HTML,
  )
  await process_and_reply(message, f"[User sent a document: {doc_name}]")


# --- FASTAPI WEBHOOK ROUTES & SERVER STARTUP ---


@app.on_event("startup")
async def on_startup():
  """Automatically sets up the Telegram webhook on app startup"""
  try:
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    print(f"Webhook successfully set to: {WEBHOOK_URL}")
  except Exception as e:
    print(f"⚠️ Webhook setup warning: {e}")


@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
  """Receives updates from Telegram and feeds them into aiogram"""
  json_data = await request.json()
  update = Update.model_validate(json_data, context={"bot": bot})
  await dp.feed_update(bot, update)
  return {"status": "ok"}


@app.get("/")
async def index():
  """Health-check endpoint for Render"""
  return {"status": "Root-GPT Groq Webhook Server is running"}


if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=PORT)
# Комментарий можно писать и в конце строки кода