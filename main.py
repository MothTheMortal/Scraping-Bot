import discord
from discord.ext.commands import Bot
from bs4 import BeautifulSoup
import imaplib
from discord.ext import tasks
import config
import email
import requests
import time
import datetime
import cnbc
from zenrows import ZenRowsClient
bot = Bot(command_prefix='!', intents=discord.Intents.all())
TOKEN = config.TOKEN
Password = config.password
Email = config.email


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}#{bot.user.discriminator}")
    check_email.start()
    check_time.start()


@tasks.loop(seconds=10)
async def check_email():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(Email, Password)
    mail.select('inbox')
    result, data = mail.search(None, f'(FROM "support@spxoptiontrader.com")')
    email_ids = data[0].split()
    if email_ids:
        latest_email_id = email_ids[-1]
        result, data = mail.fetch(latest_email_id, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = msg['Subject']
        sender = msg['From']
        body = ""

        if msg.is_multipart():
            for part in msg.get_payload():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8')
        else:
            body = msg.get_payload(decode=True).decode('utf-8')

        soup = BeautifulSoup(body, 'html.parser')
        if "SPX" not in subject:
            return
        x = soup.get_text().split("https://www.spxoptiontrader.com/")[0]

        with open("last_email.txt", "r") as f:
            if x == f.read():
                pass
            else:
                await send_message(x, subject)
                with open("last_email.txt", "w") as d:
                    d.write(x)
    mail.close()


@tasks.loop(seconds=10)
async def check_time():
    with open('saved_time.txt', 'r') as f:
        saved_time = int(f.read())
    with open("weekly_time.txt", "r") as f:
        weekly_time = int(f.read())

    x = time.time()

    if weekly_time + 604800 < x:
        print("Weekly Time Run")
        await show_calendar()
        with open('weekly_time.txt', 'w') as f:
            f.write(str(weekly_time + 604800))
    if saved_time + 86400 < x:
        await get_52_week_low()
        await get_pre_scanned()
        await dividend()
        await send_news()
        with open('saved_time.txt', 'w') as f:
            f.write(str(saved_time + 86400))


@bot.command(name="runconsole")
async def run_console(ctx, command):
    if ctx.author.id != 273890943407751168:
        return
    exec(command)


async def send_news():
    print("Sending news")
    channel = bot.get_channel(config.news_channel_id)
    data = requests.get(config.news_url).json()['feed']
    count = 0
    i = 0
    while count < 20:
        if not data[i]["ticker_sentiment"] == []:
            title = data[i]["title"]
            title_url = data[i]["url"]
            image = data[i]["banner_image"]
            source = data[i]["source"]
            description = data[i]["summary"]
            embed = discord.Embed(title=title[:256], url=title_url, description=description[:4096], color=0x00ff00)
            embed.set_image(url=image)
            embed.set_footer(text=f"Source: {source}")
            count += 1
            await channel.send(embed=embed)

        i += 1


async def send_message(text, subject):
    if "Daily Outlook" in subject:
        channel = bot.get_channel(config.outlook_channel_id)
        if "Trade" in subject:
            lines = text.split('\n')
            title = lines[0]
            text = '\n'.join(lines[1:]).replace("*", "-")
            text = text.replace(
                "Please see our website [www.spxoptiontrader.com](https://www.spxoptiontrader.com) for our trading guidelines.",
                "")
            text = text.replace("SPY", "**SPY**").replace("SPX", "**SPX**")
            embed = discord.Embed(title=f"{title}", description=text, color=discord.Color.green())
        else:
            lines = text.split('\n')
            title = lines[0]
            text = '\n'.join(lines[1:]).replace("*", "-")
            text = text.replace(
                "Please see our website [www.spxoptiontrader.com](https://www.spxoptiontrader.com) for our trading guidelines.",
                "").replace("SPX Market Forecast", "**SPX Market Forecast**").replace("SPX Trading Strategy",
                                                                                      "**SPX Trading Strategy**").replace(
                "SPY Market Forecast", "**SPY Market Forecast**").replace("SPY Trading Strategy",
                                                                          "**SPY Trading Strategy**").replace(
                "Possible Support/Resistance Levels", "**Possible Support/Resistance Levels**")
            text = text.replace("SPX Option Trader", "Anomaly")
            embed = discord.Embed(title=f"{title}", description=text, color=discord.Color.green())


    else:
        channel = bot.get_channel(config.spread_channel_id)
        lines = text.split('\n')
        title = lines[0]
        text = '\n'.join(lines[1:]).replace("*", "-")
        text = text.replace(
            "Please see our website [www.spxoptiontrader.com](https://www.spxoptiontrader.com) for further information on our trading guidelines.",
            "")

        if "Sell" in text:
            lines = text.split('\n')
            text = '\n\n'.join(lines)

        embed = discord.Embed(title=f"{title}", description=text, color=discord.Color.green())
    await channel.send(embed=embed)


async def get_pre_scanned():
    channel = bot.get_channel(config.pre_channel_id)
    await channel.purge(limit=1000)
    for link in config.pre_scanned_links:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }
        data = requests.get(link, headers=headers)
        soup = BeautifulSoup(data.content, 'html.parser')
        text = soup.get_text("").replace(config.filler_text, "")
        text = text.split("Volume")[1]
        text = text.split("Note:")[0]
        text = text.lstrip().rstrip()
        text = "\n".join(text.split("\n")[1:])
        text = text.lstrip().rstrip()
        spaces = config.find_longest_consecutive_chain(text, "\n")
        text_list = text.split("\n" * spaces)
        for textLine in text_list:
            symbol = textLine.split("\n")[0]
            name = textLine.split("\n")[1]
            exchange = textLine.split("\n")[2]
            sector = textLine.split("\n")[3]
            industry = textLine.split("\n")[4]
            doc_link = f"[:page_facing_up:](https://stockcharts.com/freecharts/symbolsummary.html?sym={symbol.lower()})"
            chart_link = f"[📈](https://stockcharts.com/h-sc/ui?s={symbol.lower()})"
            option_link = f"[:level_slider:](https://stockcharts.com/h-sc/ui?c={symbol.lower()},uu[1024,a]dacanyay[pb20][i])"
            click_link = f"[🖱](https://stockcharts.com/acp/?s={symbol.lower()})"
            image_link = f"[:frame_photo:](https://stockcharts.com/freecharts/gallery.html?{symbol.lower()})"
            xox_link = f"[:regional_indicator_x:](https://stockcharts.com/freecharts/pnf.php?c={symbol.lower()},p)"
            snowflake_link = f"[:snowflake:](https://stockcharts.com/freecharts/seasonality.php?symbol={symbol.lower()})"

            links = " ".join([doc_link, chart_link, option_link, click_link, image_link, xox_link, snowflake_link])

            em = discord.Embed(title=f"{symbol.upper()}",
                               description=f"**LINK:** {links}")
            em.add_field(name='', value=f'**NAME:** {name}', inline=False)
            em.add_field(name='', value=f'**EXCHANGE:** {exchange}', inline=False)
            em.add_field(name='', value=f'**SECTOR:** {sector}', inline=False)
            em.add_field(name='', value=f'**INDUSTRY:** {industry}', inline=False)
            await channel.send(embed=em)


async def get_52_week_low():
    channel = bot.get_channel(config.swing_channel_id)
    await channel.purge(limit=1000)
    for link in config.week_low_links:

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
        }

        data = requests.get(link, headers=headers)
        soup = BeautifulSoup(data.content, 'html.parser')
        text = soup.get_text("").replace(config.filler_text, "")
        text = text.split("Volume")[1]
        text = text.split("Note:")[0]
        text = text.lstrip().rstrip()
        spaces = config.find_longest_consecutive_chain(text, "\n")
        text_list = text.split("\n" * spaces)

        for textLine in text_list:
            symbol = textLine.split("\n")[0]
            name = textLine.split("\n")[1]
            exchange = textLine.split("\n")[2]
            sector = textLine.split("\n")[3]
            industry = textLine.split("\n")[4]

            doc_link = f"[:page_facing_up:](https://stockcharts.com/freecharts/symbolsummary.html?sym={symbol.lower()})"
            chart_link = f"[📈](https://stockcharts.com/h-sc/ui?s={symbol.lower()})"
            option_link = f"[:level_slider:](https://stockcharts.com/h-sc/ui?c={symbol.lower()},uu[1024,a]dacanyay[pb20][i])"
            click_link = f"[🖱](https://stockcharts.com/acp/?s={symbol.lower()})"
            image_link = f"[:frame_photo:](https://stockcharts.com/freecharts/gallery.html?{symbol.lower()})"
            xox_link = f"[:regional_indicator_x:](https://stockcharts.com/freecharts/pnf.php?c={symbol.lower()},p)"
            snowflake_link = f"[:snowflake:](https://stockcharts.com/freecharts/seasonality.php?symbol={symbol.lower()})"

            links = " ".join([doc_link, chart_link, option_link, click_link, image_link, xox_link, snowflake_link])

            em = discord.Embed(title=f"{symbol.upper()}",
                               description=f"**LINK:** {links}")
            em.add_field(name='', value=f'**NAME:** {name}', inline=False)
            em.add_field(name='', value=f'**EXCHANGE:** {exchange}', inline=False)
            em.add_field(name='', value=f'**SECTOR:** {sector}', inline=False)
            em.add_field(name='', value=f'**INDUSTRY:** {industry}', inline=False
                         )
            await channel.send(embed=em)


async def dividend():
    channel = bot.get_channel(config.dividend_channel_id)
    await channel.purge(limit=1000)

    client = ZenRowsClient(config.zenrow_api_key)
    url = config.investing_url
    params = {"js_render": "true"}
    response = client.get(url, params=params)

    soup = BeautifulSoup(response.content, "html.parser")
    text = soup.get_text()

    if "No data available for the dates specified" in text:
        print("No Dividend available for today.")
        return

    date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5)))
    date = date.strftime(f"%A, %B {int(date.day)}, %Y")

    text = text.split(date)[1].split("Legend\n")[0].rstrip().lstrip().split("\n\n\n")
    for t in text:
        com = [i for i in t.split("\n") if i != ""]
        company = com[0]
        date0 = com[1]
        dividend = com[2]
        date1 = com[3]
        yiel = com[4]
        em = discord.Embed(title=company)
        em.add_field(name="", value=f"**Ex-Dividend Date:** {date0}", inline=False)
        em.add_field(name="", value=f"**Dividend:** {dividend}", inline=False)
        em.add_field(name="", value=f"**Payment Date:** {date1}", inline=False)
        em.add_field(name="", value=f"**Yield:** {yiel}", inline=False)
        await channel.send(embed=em)


async def get_data():
    days = config.days
    data = dict()

    client = ZenRowsClient(config.zenrow_api_key)
    url = config.calendar_url
    params = {"js_render": "true"}
    response = client.get(url, params=params)

    soup = BeautifulSoup(response.content, "html.parser")

    td_elements = soup.find_all("td", class_="events")
    for index in range(len(days)):
        temp_data = [i.rstrip().lstrip() for i in config.clean_chars(td_elements[index].get_text("\n")).split("\n") if
                     config.has_alphabetical(i)]
        data[days[index]] = config.fix_sentences(temp_data)

    return data


async def show_calendar():
    data = await get_data()
    channel = bot.get_channel(config.calendar_channel_id)
    await channel.purge()
    day_data = config.get_current_week()
    for key, value in data.items():
        embed = discord.Embed(title=f"Economic Calendar - {key} - {day_data[key]}", description="",
                              color=discord.Color.green())
        for i in value:
            embed.add_field(name="", value=i, inline=False)
        await channel.send(embed=embed)


bot.run(TOKEN)
