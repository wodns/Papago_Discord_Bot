import discord
from discord.ext import commands
from discord import app_commands

from googletrans import Translator

import json
import urllib

LANGUAGE = {
    'ko': ['KO', 'Ko', 'kO', 'kr', 'KR', 'Kr', 'kR'],
    'th': ['TH', 'Th', 'tH'],
    'en': ['EN', 'En', 'eN'],
}

#NOTE: TOKEN
with open("secrets.json") as f:
    secrets = json.load(f)

BOT_TOKEN = secrets['BOT_TOKEN']
CLIENT_ID = secrets['CLIENT_ID']
CLIENT_SECRET = secrets['CLIENT_SECRET']

#NOTE: PAPAGO
URL_TRANS = "https://openapi.naver.com/v1/papago/n2mt"
URL_DETECT = "https://openapi.naver.com/v1/papago/detectLangs"

#NOTE: GOOGLE
translator = Translator()

#NOTE: BOT
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.tree.sync() #WARN: sync tree with await
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("Translation"))

#TODO: Add menu for translate later
@bot.tree.context_menu(name="Translate to ko")
async def translate2ko(interaction: discord.Interaction, message: discord.Message):
    src = detector(message.system_content)
    result = translator.translate(message.system_content, src=src, dest='ko')
    await interaction.response.send_message(f"```{result.text}```", ephemeral=True) #WARN: message.content is not the message

@bot.tree.context_menu(name="Translate to th")
async def translate2th(interaction: discord.Interaction, message: discord.Message):
    src = detector(message.system_content)
    result = translator.translate(message.system_content, src=src, dest='th')
    await interaction.response.send_message(f"```{result.text}```", ephemeral=True)

@bot.tree.context_menu(name="Translate to en")
async def translate2en(interaction: discord.Interaction, message: discord.Message):
    src = detector(message.system_content)
    result = translator.translate(message.system_content, src=src, dest='en')
    await interaction.response.send_message(f"```{result.text}```", ephemeral=True)

#TODO: Add slash commands

#TODO: Seperate with functions (command, translation, embed)

@bot.command(aliases=['HELP'])
async def help(ctx):
    embed = discord.Embed()
    embed.title = ":robot: `!help`"
    embed.add_field(
        name="",
        value=">>> **!kr**\nTranslate `Thai` → `Korean`",
        inline=False,
    )
    embed.add_field(
        name="",
        value=">>> **!th**\nTranslate `Korean` → `Thai`",
        inline=False,
    )
    embed.add_field(
        name="",
        value=">>> **!!**\nTranslate `Auto` with `Google`",
        inline=False,
    )
    embed.add_field(
        name="",
        value=">>> **!?**\nTranslate `Auto` with `Papago`",
        inline=False,
    )
    embed.color = bot.application.owner.color
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=f"{bot.application.owner}", icon_url=bot.application.owner.avatar)
    await ctx.reply(embed=embed)

@bot.command(name="th", aliases=LANGUAGE['th'])
async def ko2th(ctx, *, msg):
    result = translator.translate(msg, src='ko', dest='th')
    embed = discord.Embed()
    embed.title = msg
    embed.description = f"```{result.text}```"
    embed.color = ctx.author.color
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Google_Translate_logo.svg/240px-Google_Translate_logo.svg.png")
    embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar)
    await ctx.reply(embed=embed)

@bot.command(name='ko', aliases=LANGUAGE['ko'])
async def th2ko(ctx, *, msg):
    result = translator.translate(msg, src='th', dest='ko')
    embed = discord.Embed()
    embed.title = msg
    embed.description = f"```{result.text}```"
    embed.color = ctx.author.color
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Google_Translate_logo.svg/240px-Google_Translate_logo.svg.png")
    embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar)
    await ctx.reply(embed=embed)

@bot.command(name="!")
async def google(ctx, *, msg):
    src = detector(msg)
    embed = discord.Embed()
    embed.title = msg
    if src not in LANGUAGE.keys():
        await ctx.send(src) #TODO: Add Error Embed
    for dest in LANGUAGE.keys():
        if dest == src:
            continue
        result = translator.translate(msg, src=src, dest=dest)
        embed.add_field(
            name="",
            value=f"```{result.text}```",
            inline=False,
        )
    embed.color = ctx.author.color
    embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Google_Translate_logo.svg/240px-Google_Translate_logo.svg.png")
    embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar)
    await ctx.reply(embed=embed)

def detector(msg):
    lang = translator.detect(msg)
    return lang.lang

@bot.command(name="?")
async def papago(ctx, *, msg):
    lang = detectLang(msg)
    embed = discord.Embed()
    embed.title = msg
    if lang not in LANGUAGE.keys():
        await ctx.send(lang)  #TODO: Add Error Embed
    text = urllib.parse.quote(msg)
    for target in LANGUAGE.keys():
        if lang == target:
            continue
        data = f"source={lang}&target={target}&text=" + text
        request = urllib.request.Request(URL_TRANS)
        request.add_header("X-Naver-Client-Id", CLIENT_ID)
        request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            result = json.loads(response_body.decode('utf-8'))
            embed.add_field(
                name="",
                value=f"```{result['message']['result']['translatedText']}```",
                inline=False,
            )
        else:
            result = "Error Code:" + rescode
            embed.add_field(
                name="",
                value=f"```{result}```",
                inline=False,
            )
    embed.color = ctx.author.color
    embed.set_thumbnail(url="https://papago.naver.com/static/img/papago_og.png")
    embed.set_footer(text=ctx.author, icon_url=ctx.author.avatar)
    await ctx.reply(embed=embed)

def detectLang(msg):
    text = urllib.parse.quote(msg)
    data = "query=" + text
    request = urllib.request.Request(URL_DETECT)
    request.add_header("X-Naver-Client-Id",CLIENT_ID)
    request.add_header("X-Naver-Client-Secret",CLIENT_SECRET)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if(rescode==200):
        response_body = response.read()
        result = json.loads(response_body.decode('utf-8'))
        return result['langCode']
    else:
        result = "Error Code:" + rescode
        return result

bot.run(BOT_TOKEN)