from os import getenv as env
import requests
import json

from apscheduler.schedulers.background import BackgroundScheduler

from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

flag = {"UAH": "πΊπ¦", "USD": "πΊπΈ", "EUR": "πͺπΊ", "RUB": "π·πΊ", "BYN": "π§πΎ", "PLN": "π΅π±"}
rates = {}
date = ""


app = Client(
    "session/mashu",
    api_id=env("API_ID"),
    api_hash=env("API_HASH"),
    bot_token=env("BOT_TOKEN"),
)


def require_rates():
    link = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
    with requests.get(link) as response:
        global rates, date
        information = json.loads(response.text)
        date = information[18]["exchangedate"]
        for i in information:
            if i["cc"] in flag.keys():
                rates[i["cc"]] = i["rate"]
    print("Rates acquired!")


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
def uah(_, num):
    return "UAH", num


currencies = ["usd", "USD", "eur", "EUR", "rub", "RUB", "byn", "BYN", "pln", "PLN"]


@app.on_message(filters.command(currencies))
@reply_to_message
def foreign(msg, num):
    cur = msg.command[0].upper()
    return cur, to_uah(cur, num)


@app.on_message(filters.command(["date"]))
def datefunc(_, msg):
    msg.reply(f"ΠΡΡΡΡ Π²Π°Π»ΡΡ Π΄ΠΎΡΡΡΠΏΠ½Ρ Π½Π° Π΄Π°ΡΡ: {date}")


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
