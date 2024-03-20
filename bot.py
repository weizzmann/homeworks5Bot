import logging

from html import escape
from uuid import uuid4
import re

from telegram import InlineQueryResultArticle, InputTextMessageContent,ForceReply, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler
from telegram import LinkPreviewOptions

from pydnevnikruapi.dnevnik import dnevnik
import datetime
import operator
import dateutil.parser
import pytz
import random

from dotenv import load_dotenv
import os

load_dotenv()

DNEVNIKRU_LOGIN = os.getenv('DNEVNIKRU_LOGIN') or os.environ.get('DNEVNIKRU_LOGIN')
DNEVNIKRU_PASSWORD = os.getenv('DNEVNIKRU_PASSWORD') or os.environ.get('DNEVNIKRU_PASSWORD')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_TOKEN')

#import pprint
#from datetime import date, datetime, timedelta, tzinfo

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

prev_marks = []

emoji_dict = [
{
  'emoji': ["🇬🇧", "💂"],
  'id': 467366841189269,
  'id_str': '467366841189269',
  'knowledgeArea': 'Иностранный язык',
  'name': 'Англ. язык'},
 {
  'emoji': ["🐚", "🐯", "🐝", "🐞", "🐌", "🐍", "☘️", "🍄", "🌾", "🌻"],
  'id': 467371136156566,
  'id_str': '467371136156566',
  'knowledgeArea': 'Естествознание',
  'name': 'Биология'},
 {
  'emoji': ["🗺️", "🌏", "🗾"],
  'id': 467379726091160,
  'id_str': '467379726091160',
  'knowledgeArea': 'Социальные науки',
  'name': 'География'},
 {
  'emoji': ["🎨", "👨‍🎨", "🖍️"],
  'id': 467388316025754,
  'id_str': '467388316025754',
  'knowledgeArea': 'Искусство',
  'name': 'ИЗО'},
 {
  'emoji': ["🏛️", "⏳", "📜"],
  'id': 467401200927645,
  'id_str': '467401200927645',
  'knowledgeArea': 'Социальные науки',
  'name': 'История'},
 {
  'emoji': ["📖", "📘", "📑", "📚"],
  'id': 726933189714468,
  'id_str': '726933189714468',
  'knowledgeArea': 'Русский язык и литература',
  'name': 'Литература'},
 {
  'emoji': ["♾️", "🧮", "✖️", "➕", "➗", " ∯", " ∑", " 𝝅", " 𝝃"],
  'id': 467409790862239,
  'id_str': '467409790862239',
  'knowledgeArea': 'Математика',
  'name': 'Математика'},
 {
  'emoji': ["🎼", "🎶", "🎧", "🎷", "🎻", "🎺", "🎵", "🎸", "🥁", "🪗"],
  'id': 467414085829536,
  'id_str': '467414085829536',
  'knowledgeArea': 'Искусство',
  'name': 'Музыка'},
 {
  'emoji': ["❤️", "🩷", "💟", "💗", "🖤"],
  'id': 1986494286422360749,
  'id_str': '1986494286422360749',
  'knowledgeArea': 'Прочее',
  'name': 'о важном'},
 {
  'emoji': ["🛐", "🕍", "🕌", "☦️", "🕎", "✝️", "✡️", "🛕"],
  'id': 1852164339516844262,
  'id_str': '1852164339516844262',
  'knowledgeArea': 'Прочее',
  'name': 'ОДНКНР'},
 {
  'emoji': ["🗣️", "🗯️", "📵"],
  'id': 467448445567912,
  'id_str': '467448445567912',
  'knowledgeArea': 'Русский язык и литература',
  'name': 'Рус. язык'},
 {
  'emoji': ["🛠️", "🪓", "🪚", "🔨", "🗜️", "⚒️", "🔧", "🔩"],
  'id': 726937484681765,
  'id_str': '726937484681765',
  'knowledgeArea': 'Технология',
  'name': 'Технология'},
 {
  'emoji': ["🏐", "⚽️", "🚴‍♀️", "🤽‍♀️", "⛸️", "💪", "🎿", "🥊", "🏓", "⚾️", "🏀"],
  'id': 467457035502506,
  'id_str': '467457035502506',
  'knowledgeArea': 'Физическая культура',
  'name': 'Физкультура'}
]

homeworks_icon = "https://img.icons8.com/external-itim2101-lineal-color-itim2101/48/external-homework-back-to-school-itim2101-lineal-color-itim2101.png"
marks_icon="https://img.icons8.com/external-smashingstocks-outline-color-smashing-stocks/48/external-Grade-online-education-smashingstocks-outline-color-smashing-stocks.png"

def search_dictionaries(key, value, list_of_dictionaries):
    return [element for element in list_of_dictionaries if element[key] == value]

def different_dicts(first_array, new_array):
    unique_dicts = [dictionary for dictionary in new_array if dictionary not in first_array]
    return unique_dicts

def cleanhtml(raw_html):
  CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def mark_text(mark):
    if mark == "1":
        return "【1】"
    elif mark == "2":
        return "【2】"
    elif mark == "3":
        return "【3】"
    elif mark == "4":
        return "【4】"
    elif mark == "5":
        return "【5】"

def get_homeworks():
    dn = dnevnik.DiaryAPI(DNEVNIKRU_LOGIN, DNEVNIKRU_PASSWORD)

    context = dn.get_context()
    group_id = context["groupIds"][0]
    person_id = context["personId"]
    school_id = context["schoolIds"][0]
    schedule = dn.get_person_schedule(person_id, group_id, datetime.datetime.now(), datetime.datetime.now())
    next_date = schedule['days'][0]['nextDate']
    # next_date = '2023-12-14T00:00:00'
    next_date = datetime.datetime.strptime(next_date,"%Y-%m-%dT%H:%M:%S")
    schedule = dn.get_person_schedule(person_id, group_id, next_date, next_date )
    schedule = schedule['days'][0]
    homework_files = dn.get_person_homework(school_id, person_id, next_date, next_date)["files"]

    homeworks = []
    for lesson in sorted(schedule["lessons"], key=operator.itemgetter("number")):
        subject_id = lesson["subjectId"]
        subject = [subject for subject in schedule["subjects"] if subject["id"] == subject_id][0]
        subject_name = subject["name"]
        emoji = [random.choice(e["emoji"]) for e in emoji_dict if e["id"] == subject_id][0]
        work = [work for work in schedule["homeworks"] if work["subjectId"] == subject_id]
        if work:
            homework =  work[0]["text"][1:] if work[0]["text"][0] == "." else work[0]["text"]
            files = [{'name': file["name"], 'url': file["downloadUrl"]} for file in homework_files if file["id"] in work[0]["files"]]
        else:
            homework = "не требуется"
            files = []
            
        homeworks.append({
            'date': next_date.strftime('%d.%m.%Y'),
            'subject_name': subject_name,
            'emoji': emoji,
            'homework': homework,
            'files': files
        })
    return homeworks

def get_marks():
    dn = dnevnik.DiaryAPI(DNEVNIKRU_LOGIN, DNEVNIKRU_PASSWORD)

    context = dn.get_context()
    group_id = context["groupIds"][0]
    person_id = context["personId"]
    recentmarks = dn.get(f"persons/{person_id}/group/{group_id}/recentmarks", params={"limit": 1, "fromDate": datetime.datetime.now(),})
    marks = recentmarks["marks"]
    works = recentmarks["works"]
    lessons = recentmarks["lessons"]
    subjects = recentmarks["subjects"]
    work_types = recentmarks["workTypes"]

    recentmarks = []
    for mark in marks[:5]:
        work = search_dictionaries('id', mark['work'], works)
        subject = search_dictionaries('id', work[0]['subjectId'], subjects)
        work_type = search_dictionaries('id', mark['workType'], work_types)
        lesson = search_dictionaries('id', mark['lesson'], lessons)
        date_send = dateutil.parser.parse(mark['date']).strftime('%d.%m.%Y %H:%M:%S')
        subject_name = subject[0]['name']
        mark_value = mark['value']
        work_type_name = work_type[0]['name']
        date_target = dateutil.parser.parse(work[0]['targetDate']).strftime('%d.%m')
        lesson_title = ' '.join(lesson[0]['title'].split()) if lesson else ""

        recentmarks.append({
            'date_send': date_send,
            'subject_name': subject_name,
            'mark_value': mark_text(mark_value),
            'work_type_name': work_type_name,
            'date_target': date_target,
            'lesson_title': lesson_title
        })
    return recentmarks

def homeworks_to_text(homeworks):
    date = homeworks[0]['date']
    text = f'<u><b>Уроки на {date}</b></u>\n'
    # text +="".join(f'''<code>{homework['subject_name']}<tg-emoji emoji-id="1">{homework['emoji']}</tg-emoji></code>\n<pre>{homework['homework']}</pre>\n''' for homework in homeworks)
    text_list = []
    for i, homework in enumerate(homeworks):
         if homework['files']: 
            files = '\n'.join([f'<a href="{file["url"]}"><tg-emoji emoji-id="2">📎</tg-emoji>{file["name"]}</a>' for file in homework['files']])
            # files = '\n> '.join([f'📎{file["name"]} - {file["url"]}' for file in homework['files']])
            if homework['homework']:
                # hw = f"{homework['homework']}\n{files}"
                hw = f'''<code>{i + 1}. {homework['subject_name']}{homework['emoji']}</code>\n<pre>{homework['homework']}</pre>\n{files}\n'''
            else:
                hw = f'''<code>{i + 1}. {homework['subject_name']}{homework['emoji']}</code>\n{files}\n'''
         else:
            hw = f'''<code>{i + 1}. {homework['subject_name']}{homework['emoji']}</code>\n<pre>{homework['homework'] if homework['homework'] else "не требуется"}</pre>\n'''
         text_list.append(hw)
    text += ''.join(text_list)
    return text[:-1]

def marks_to_text(marks):
    marks_text = []
    for mark in marks:
        code = f"<code>{mark['subject_name']}:{mark['mark_value']}</code>\n"
        if mark['work_type_name'] == 'Оценка за период' or mark['work_type_name'] == 'Итоговая оценка':
            pre = f"<pre>{mark['work_type_name']}</pre>\n"
        else:
            pre = f"<pre>{mark['work_type_name']} за {mark['date_target']}\nТема: {mark['lesson_title']}</pre>\n"
        marks_text.append(code + pre)
    #text = "".join(f'''<code>{mark['subject_name']}: {mark['mark_value']}</code>\n<pre>{mark['work_type_name']} за {mark['date_target']}\nТема: {mark['lesson_title']}</pre>\n''' for mark in marks)
    return ''.join(marks_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

async def homeworks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   await update.message.reply_html(text = homeworks_to_text(get_homeworks()), disable_web_page_preview=True)

async def marks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   await update.message.reply_html(text=marks_to_text(get_marks()))

async def new_marks(context):
    global prev_marks

    last_marks = get_marks()
    result = different_dicts(prev_marks, last_marks)
    prev_marks = last_marks
    if result:
        await context.bot.send_message(chat_id = 877694178, 
                                       text=marks_to_text(result), 
                                       parse_mode=ParseMode.HTML)

async def daily_homeworks(context):
    await context.bot.send_message(chat_id = 877694178, 
                                   text = homeworks_to_text(get_homeworks()), 
                                   parse_mode=ParseMode.HTML,
                                   disable_web_page_preview=True)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query. This is run when you type: @botusername <query>"""
    #query = update.inline_query.query
    homeworks = homeworks_to_text(get_homeworks())
    marks = marks_to_text(get_marks())
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Домашнее задание",
            description=cleanhtml(homeworks),
            thumbnail_url=homeworks_icon, 
            thumbnail_width=48,
            thumbnail_height=48,
            input_message_content=InputTextMessageContent(
                homeworks, parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True),
            ),
        ),
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Последние 5 оценок",
            description=cleanhtml(marks),
            thumbnail_url=marks_icon, 
            thumbnail_width=48, 
            thumbnail_height=48,
            input_message_content=InputTextMessageContent(
                marks, parse_mode=ParseMode.HTML,
            ),
        ),
    ]

    await update.inline_query.answer(results)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    job_queue = application.job_queue
    job_queue.run_repeating(new_marks, interval=60*15, first=10)
    job_queue.run_daily(daily_homeworks, datetime.time(hour=15, minute=0, tzinfo=pytz.timezone('Asia/Vladivostok')),days=(0, 1, 2, 3, 4, 5, 6))

    # on different commands - answer in Telegram
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("homeworks", homeworks))
    application.add_handler(CommandHandler("marks", marks))

    # on inline queries - show corresponding inline results
    application.add_handler(InlineQueryHandler(inline_query))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

#homeworks - Домашнее задание
#marks - Последние 5 оценок