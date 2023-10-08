import asyncio.exceptions
import discord
from discord.ext import commands
import requests
import json
import datetime
from datetime import datetime, timedelta
import random

help_command = commands.DefaultHelpCommand(no_category='Commands')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=help_command)

cooldown_time = 1
currentIndex = 0
prev_time = datetime.now()
current_message = None
currentList = None

currentIndex_dict = {}
prev_time_dict = {}
current_message_dict = {}
currentList_dict = {}
cooldown_time_dict = {}

def set_up():
    for server in bot.guilds:
        currentList_dict.update({server.id: None})
        current_message_dict.update({server.id: None})
        currentIndex_dict.update({server.id: 0})
        prev_time_dict.update({server.id: datetime.now()})
        cooldown_time_dict.update({server.id: 1})

def change_prev_time(msg):
    global prev_time_dict
    prev_time_dict[msg.guild.id] = datetime.now()


def check_cooldown():
    def predicate(ctx):
        print(ctx.guild.id)
        return datetime.now() >= prev_time_dict[ctx.guild.id] + timedelta(seconds=cooldown_time_dict[ctx.guild.id])

    return commands.check(predicate)

def scroll_Left(reaction):
    global currentList_dict, currentIndex_dict
    if len(currentList_dict[reaction.message.guild.id]) <= 20:
        return
    if currentIndex_dict[reaction.message.guild.id] == 20:
        currentIndex_dict[reaction.message.guild.id] = 0
    elif currentIndex_dict[reaction.message.guild.id] - 20 < 0:
        currentIndex_dict[reaction.message.guild.id] = len(currentList_dict[reaction.message.guild.id]) - len(currentList_dict[reaction.message.guild.id]) % 20
    else:
        currentIndex_dict[reaction.message.guild.id] -= 20


def scroll_Right(reaction):
    global currentList_dict, currentIndex_dict
    if len(currentList_dict[reaction.message.guild.id]) <= 20:
        return
    if currentIndex_dict[reaction.message.guild.id] >= len(currentList_dict[reaction.message.guild.id]) - 20:
        currentIndex_dict[reaction.message.guild.id] = 0
    elif currentIndex_dict[reaction.message.guild.id] + 20 > len(currentList_dict[reaction.message.guild.id]):
        currentIndex_dict[reaction.message.guild.id] = len(currentList_dict[reaction.message.guild.id]) - len(currentList_dict[reaction.message.guild.id]) % 20
    else:
        currentIndex_dict[reaction.message.guild.id] += 20


def hardSearch(msg, key, criteria):
    url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?&' + key + "=" + criteria
    response = requests.get(url)
    print(response.status_code)
    change_prev_time(msg)
    if response.status_code == 200:
        json_data = json.loads(response.text)
        item = json_data['data'][0]
        return item
    else:
        return "no item found"


def softSearch(msg, key, criteria):
    global currentList_dict
    url = "https://db.ygoprodeck.com/api/v7/cardinfo.php?&" + key + "=" + criteria
    response = requests.get(url)
    print(response.status_code)
    change_prev_time(msg)
    if response.status_code == 200:
        json_data = json.loads(response.text)
        item = json_data['data']
        currentList_dict[msg.guild.id] = item
        return item
    else:
        currentList_dict[msg.guild.id] = "n/a"
        return "no item found"


def findAll(msg, keyword, arg):
    global currentList_dict
    if arg != 'keyword':
        key = keyword
        criteria = arg
        itemlist = softSearch(msg, key, concatenate_input(criteria))
        print('search type: ' + key)
        print('keywords: ' + criteria)
        return listing(itemlist, 0)
    else:
        currentList_dict[msg.guild.id] = 'n/a'
        return 'missing keyword(s)'


def listing(itemlist, index):
    string = ''
    maxIndex = index + 20 if len(itemlist) - index > 20 else len(itemlist)
    if itemlist != "no item found":
        print(str(index) + ' ' + str(maxIndex))
        for i in range(index, maxIndex):
            string += itemlist[i]['name'] + '\n'
        string += '\n \n' + str(index) + '-' + str(maxIndex) + ' of ' + str(len(itemlist))
        return string
    else:
        return itemlist


def concatenate_input(message):
    stars = message.count(" *")
    message1 = message.split(' *')[0]
    for i in range(1, stars + 1):
        message1 += '&' + message.split(' *')[i]
    spaces = message1.count(" ")
    keywords = message1.split(' ')[0]
    for i in range(1, spaces + 1):
        keywords += '%20' + message1.split(' ')[i]
    print(keywords)
    return keywords


def card_info(card):
    card_type = 1 if card['type'].lower().count("monster") > 0 else 0
    if card_type == 1:
        return ('name: ' + card['name'] + '\n' +
                str(card['level']) + ' star ' + card['type'] + '\n' +
                'attribute: ' + card['attribute'] + ', ' + 'race: ' + card['race'] + '\n' +
                'description: ' + card['desc'] + '\n' +
                'ATK: ' + str(card['atk']) + '          ' +
                'DEF: ' + str(card['def']))
    else:
        return ('name: ' + card['name'] + '\n' +
                card['race'] + ' ' + card['type'] + '\n' +
                'description: ' + card['desc'] + '\n')


@bot.command(brief='Replies Hello', description='Replies Hello')
async def hello(message):
    await message.reply('Hello {0}!'.format(message.author))


@bot.command(brief='Searches for cards using keywords', description='Searches for card names with keyword(s) in name')
@check_cooldown()
async def fname(message, *, arg='keyword'):
    global currentList_dict
    global currentIndex_dict
    global current_message_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'fname', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='Searches for cards with specified atk',
             description='-Searches for card names with specified attack \n -You can write lte(less than or equal) or '
                         'gte(more than or equal) before number (no space between) \n ex: !fattack gte1000')
@check_cooldown()
async def fattack(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'atk', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')

@bot.command(brief='Searches for cards with specified def',
             description='-Searches for card names with specified defense \n -You can write lte(less than or equal) or '
                         'gte(more than or equal) before number (no space between) \n ex: !fdefense lte1000')
@check_cooldown()
async def fdefense(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'def', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='Searches for cards with specified decription',
             description='-Searches for card names with specified words in description \n ex: !fdescription cannot be '
                         'destroyed by battle')
@check_cooldown()
async def fdescription(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'desc', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='Searches for cards with specified level/star',
             description='-Searches for card names with level/star \n ex: !flevel 4')
@check_cooldown()
async def flevel(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'level', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='Searches for cards with specified attribute',
             description='-Searches for card names with specific attribute \n ex: !fattribute dark')
@check_cooldown()
async def fattribute(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'attribute', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='Searches for cards with specified race',
             description='-Searches for card names with specific race \n ex: !frace dragon')
@check_cooldown()
async def frace(message, *, arg='keyword'):
    global current_message_dict
    global currentIndex_dict
    currentIndex_dict[message.guild.id] = 0
    current_message_dict[message.guild.id] = await message.reply(findAll(message, 'race', arg))
    if isinstance(currentList_dict[message.guild.id], list):
        await current_message_dict[message.guild.id].add_reaction('⏪')
        await current_message_dict[message.guild.id].add_reaction('⏩')


@bot.command(brief='gives info on how to search using multiple criterias', description='gives info on how to search '
                                                                                       'using multiple criterias')
async def fmultisearch(message):
    await message.reply('you can add multiple criterias to any command starting with !f \n just add a * before the '
                        'next criteria name \n ex: !fname dragon *atk=3000')


@bot.event
async def on_reaction_add(reaction, user):
    global currentList_dict
    global currentIndex_dict
    global current_message_dict
    if user != bot.user:
        if reaction.message == current_message_dict[reaction.message.guild.id]:
            if str(reaction.emoji) == '⏪':
                print('left')
                scroll_Left(reaction)
                await current_message_dict[reaction.message.guild.id].edit(content=listing(currentList_dict[reaction.message.guild.id], currentIndex_dict[reaction.message.guild.id]))
            elif str(reaction.emoji) == '⏩':
                print('right')
                scroll_Right(reaction)
                await current_message_dict[reaction.message.guild.id].edit(content=listing(currentList_dict[reaction.message.guild.id], currentIndex_dict[reaction.message.guild.id]))
            else:
                print('none')

@bot.event
async def on_reaction_remove(reaction, user):
    global currentList_dict
    global currentIndex_dict
    global current_message_dict
    if user != bot.user:
        if reaction.message == current_message_dict[reaction.message.guild.id]:
            if str(reaction.emoji) == '⏪':
                print('left')
                scroll_Left(reaction)
                await current_message_dict[reaction.message.guild.id].edit(content=listing(currentList_dict[reaction.message.guild.id], currentIndex_dict[reaction.message.guild.id]))
            elif str(reaction.emoji) == '⏩':
                print('right')
                scroll_Right(reaction)
                await current_message_dict[reaction.message.guild.id].edit(content=listing(currentList_dict[reaction.message.guild.id], currentIndex_dict[reaction.message.guild.id]))
            else:
                print('none')

#start here next time
@bot.command(brief='Gives info & stats about specified card', description='Gives info & stats about specified card')
@check_cooldown()
async def name(message, *, arg='card name'):
    if arg != 'card name':
        key = 'name'
        criteria = arg
        item = hardSearch(message, key, concatenate_input(criteria))
        if item != "no item found":
            print('search type: ' + key)
            print('keywords: ' + criteria)
            await message.reply(item['card_images'][0]['image_url'])
            await message.reply(card_info(item))
        else:
            await message.reply("no card found")
    else:
        await message.reply('missing card name')


@bot.command(brief='starts a round of guessing game', decription='starts a round of guessing game')
@check_cooldown()
async def sgame(message, *, arg=''):
    answer = ''
    global cooldown_time_dict
    def check(msg):
        return msg.content.lower() == answer.lower() and msg.guild.id == message.guild.id

    if arg != ' ' and arg.count(' ') >= 1:
        key = arg.split(' ')[0]
        criteria = arg.split(' ', 1)[1]
        item = (softSearch(message, key, criteria))
    else:
        item = softSearch(message, '', '')

    if item != "no item found":
        end_time = datetime.now() + timedelta(seconds=30)
        gamewin = False
        cooldown_time_dict[message.guild.id] = 30
        randomcard = item[random.randrange(0, len(item), 1)]
        await message.reply('Guess the name of the Card')
        await message.reply('https://images.ygoprodeck.com/images/cards_cropped/' +
                            randomcard['card_images'][0]['image_url'].split('/cards/', 1)[1])
        answer = randomcard['name']
        print(answer)
        while datetime.now() <= end_time and gamewin != True:
            try:
                msg = await bot.wait_for("message", check=check, timeout=1)
            except Exception:
                pass
            else:
                await message.reply(str(msg.author) + ' is correct!')
                gamewin = True
        cooldown_time_dict[message.guild.id] = 1
        if not gamewin:
            await message.send('Time ran Out!')
            await message.send('The answer was: ' + answer)

    else:
        await message.reply("no cards with that criteria")


# Error Handler
@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        # await ctx.send('command on cooldown(1s)')
        return
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        # await ctx.send('invalid command')
        return
    elif isinstance(error, discord.ext.commands.errors.CheckFailure):
        await ctx.send('command on cooldown(' + str(cooldown_time_dict[ctx.guild.id]) + ')')
        return
    # elif isinstance(error, discord.ext.commands.errors.CommandInvokeError):
    # return
    else:
        raise error

@bot.event
async def on_guild_join(guild):
    global prev_time_dict, current_message_dict, currentList_dict, currentIndex_dict
    currentList_dict.update({guild.id: None})
    current_message_dict.update({guild.id: None})
    currentIndex_dict.update({guild.id: 0})
    prev_time_dict.update({guild.id: datetime.now()})
    cooldown_time_dict.update({guild.id: 1})
    await guild.text_channels[0].send('Thanks for Adding Me!  use !help to get started')

@bot.event
async def on_ready():
    set_up()
    global currentList_dict
    print(len(currentList_dict))

bot.run('keyCode Here')
