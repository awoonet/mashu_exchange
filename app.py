import requests
import json

from apscheduler.schedulers.background import BackgroundScheduler

from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

flag = {"UAH": "🇺🇦", "USD": "🇺🇸", "EUR": "🇪🇺", "RUB": "🇷🇺", "BYN": "🇧🇾", "PLN": "🇵🇱"}
rates = {}
date = ""

api_id = 930791
api_hash = "cfe0d80d2649b68284cb101483a87652"
bot_token = "1819158364:AAGgNfcQL-7JnDgaJyhnS_ZmbeU8XGCv6TE"


app = Client(":memory:", api_id, api_hash, bot_token=bot_token)


def require_rates():
    link = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    with requests.get(link) as response:
        global rates, date
        information = json.loads(response.text)
        date = information[18]["exchangedate"]
        for i in information:
            if i["cc"] in flag.keys():
                rates[i["cc"]] = i["rate"]


require_rates()

scheduler = BackgroundScheduler()
scheduler.add_job(require_rates, "interval", hours=8)

to_uah = lambda cur, num: round(num * rates[cur], 2)
count = lambda cur, num: f"\n{flag[cur]} {round(num/rates[cur], 2)}"


def format_message(main_currency, num):
    result = ""
    for cur in flag.keys():
        if cur != "UAH":
            local = count(cur, num)
        else:
            local = f"{flag[cur]} {num}"

        if cur == main_currency:
            local = f"**{local}**"
        result += local

    return result


def reply_to_message(func):
    def wrapper(app, msg):
        num = float(msg.command[1])
        text = format_message(*func(msg, num))
        msg.reply(text)

    return wrapper


@app.on_message(filters.command(["uah", "UAH"]))
@reply_to_message
def uah(msg, num):
    return "UAH", num


@app.on_message(
    filters.command(
        ["usd", "USD", "eur", "EUR", "rub", "RUB", "byn", "BYN", "pln", "PLN"]
    )
)
@reply_to_message
def foreign(msg, num):
    cur = msg.command[0].upper()
    return cur, to_uah(cur, num)


@app.on_message(filters.command(["date"]))
def datefunc(app, msg):
    msg.reply(f"Курсы валют на: {date}")


def results(num):
    result = []

    def make_article(title, num):
        result.append(
            InlineQueryResultArticle(
                title=f"{flag[title]} {title}",
                input_message_content=InputTextMessageContent(
                    format_message(title, num)
                ),
            )
        )

    make_article("UAH", num)
    for cur in rates.keys():
        make_article(cur, to_uah(cur, num))

    return result


@app.on_inline_query()
def inline(app, inline_query):
    if inline_query.query is not "":
        num = float(inline_query.query)
        inline_query.answer(results=results(num))


scheduler.start()
app.run()
