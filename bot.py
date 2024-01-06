from twitchio.ext import commands
import time
import random
from general import *
import requests
import math
import random

oauth_token = refreshToken()
cardnames = getCardNames()
cardByRarity = getRarityCards()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=f'oauth:{oauth_token}', prefix=')', initial_channels=['flekyu'])

    async def event_ready(self):
        print(f'Bot connected to Twitch')

    async def event_message(self, message):
        if (message.echo): return
        await self.handle_commands(message)
        


    @commands.command() # flekyu: !open
    async def open(self, ctx: commands.Context):
        addUser(ctx.author.id)

        username = ctx.author.name.lower()
        userIndex = getUserIndex(ctx.author.id)
        userdata = getJsonData('./users.json')
        carddata = getJsonData('./cards.json')
        now = time.time()
        configdata = getJsonData('./config.json')
        cooldown = configdata['cooldown_minutes'] * 60

        if now - userdata[userIndex]['last_opened'] < cooldown:
            await ctx.send(f"/me @{username}, you can open another pack in {round(((userdata[userIndex]['last_opened']+cooldown)-now) / 60,2)} minutes. mad")
            return 
        
        cardRarity = random.choices(
            population=['Common','Uncommon','Rare','Legendary'],
            weights=[0.5, 0.35, 0.15, 0.01],
        )[0]

        card = random.choice(cardByRarity[cardRarity])

        userdata[userIndex]['last_opened'] = now
        cardinvIndex = -1

        if (len(userdata[userIndex]['cards']) > 0):
            for i in range(len(userdata[userIndex]['cards'])):
                if (userdata[userIndex]['cards'][i]['name']) == card['name']:
                    cardinvIndex = i
                    break

        if (cardinvIndex == -1):
            userdata[userIndex]['cards'].append({
                "name": card['name'],
                "amount": 1
            })
        else:
            userdata[userIndex]['cards'][cardinvIndex]['amount'] += 1

        writeJsonData('./users.json',userdata)
        await ctx.send(f"/me @{username}, you unpacked a {card['rarity']} {card['name']} . Type !sell to sell it for {card['value']} coins woah") 

    @commands.command()
    async def sell(self, ctx: commands.Context):
        addUser(ctx.author.id)
        
        args = ctx.message.content.lower().split(' ')
        args.pop(0)

        if len(args) < 1: return

        username = ctx.author.name.lower()
        cards = args[0].split(',')
        amounts = ['1']

        if len(args) > 1:
            amounts = args[1].split(',')
            if (len(amounts) < len(cards)):
                amounts += ['1'] * (len(cards) - len(amounts))
                
        if (len(cards) < 1) or (len(amounts) < 1): 
            await ctx.send(f'/me @{ctx.author.name} invalid params doid')
            return
        
        for card in cards:
            if not (card in cardnames):
                await ctx.send(f'/me @{username} unknown card entered mad')
                return
        
        carddata = getJsonData('./cards.json')
        userdata = getJsonData('./users.json')
        userIndex = getUserIndex(ctx.author.id)

        cardIndexs = []
        for i in range(len(cards)):
            cardIndexs.append(cardnames.index(cards[i]))

        usercardIndexs = [-1] * len(cards)
        usercards = []

        for i in range(len(userdata[userIndex]['cards'])):
            usercards.append(userdata[userIndex]['cards'][i]['name'].lower())
        
        for i in range(len(cards)):
            usercardIndexs[i] = usercards.index(cards[i])

        if -1 in usercardIndexs:
            await ctx.send(f'/me @{username} you have no {cards[cards.index(-1)]} cards! doid')
            return
        

        for i in range(len(amounts)):
            if (not amounts[i].isnumeric() and amounts[i] != 'all'):
                amounts[i] = 1
            elif (amounts[i] == 'all'):
                amounts[i] = userdata[userIndex]['cards'][usercardIndexs[i]]['amount']
            else:
                amounts[i] = int(amounts[i])
            if (amounts[i] > userdata[userIndex]['cards'][usercardIndexs[i]]['amount']):
                print(amounts[i], userdata[userIndex]['cards'][usercardIndexs[i]]['amount'])
                await ctx.send(f"/me @{username} you don't have {amounts[i]} {cards[i]} cards doid")
                return
        
        revenue = 0
        for i in range(len(cards)):
            userdata[userIndex]['cards'][usercardIndexs[i]]['amount'] -= amounts[i]
            revenue += carddata[cardIndexs[i]]['value'] * amounts[i]
        
        userdata[userIndex]['money'] += revenue

        writeJsonData('./users.json', userdata)
        if (len(amounts) == 1): outputAmount = amounts[0]
        else: outputAmount = 'a bunch of'

        outputCards = ''
        for card in cards:
            outputCards += f'{card.title()}, '
        outputCards[:-2]
        await ctx.send(f'/me @{username} succesfully sold {outputAmount} {outputCards} cards for {revenue:,.2f} woah')

    @commands.command()
    async def col(self, ctx: commands.Context):
        addUser(ctx.author.id)
        args = ctx.message.content.lower().split(' ')
        args.pop(0)
        if (len(args) > 0):
            if args[0].isnumeric(): targetUser = args[0]
            else:
                if args[0].startswith('@'): args[0] = args[0][1:]
                targetUserJSON = await getUserData(userlogin=args[0])
                if not targetUserJSON:
                    print('Error while fetching user data in "col" command!')
                    return
                targetUser = targetUserJSON['data'][0]['id']
        else:
            targetUser = ctx.author.id

        refer = 'you'
        if targetUser != ctx.author.id: refer = 'they'
        userdata = getJsonData('./users.json')
        userIndex = getUserIndex(targetUser)
        if userIndex == -1:
            await ctx.send(f'/me @{ctx.author.name} that user has no data! mad')
            return
        if (len(userdata[userIndex]['cards']) < 1):
            await ctx.send(f'/me @{ctx.author.display_name} {refer} have 0 cards! mad')
            return
        cards = ""
        originallen = 0
        for card in userdata[userIndex]['cards']:
            if card['amount'] > 0:
                cards += f'| {card["name"].capitalize()} {card["amount"]} '
        if (len(cards) == originallen):
            await ctx.send(f'/me @{ctx.author.display_name} {refer} have 0 cards! mad')
            return
        money = userdata[userIndex]['money']
        output = f'${money:,.2f} {cards}'
        if (len(output) < 500):
            await ctx.send(f'/me ${money:,.2f} {cards}')
        else:
            cards = cards.split('|')
            cards.pop(0)
            cardsA, cardsB = '', ''
            for i in range(math.ceil(len(cards) / 2)):
                cardsA += (f'| {cards[i]} ')
            for i in range(math.floor(len(cards) / 2)):
                i += math.ceil(len(cards) / 2)
                cardsB += (f'| {cards[i]} ')
            await ctx.send(f'/me ${money:,.2f} {cardsA}')
            await ctx.send(f'/me {cardsB}')
        

    @commands.command()
    async def trade(self, ctx: commands.Context):
        addUser(ctx.author.id)

        args = ctx.message.content.lower()
        
        now = time.time()

    @commands.command()
    async def fixdata(self, ctx: commands.Context):
        fuckups = fixdata()
        await ctx.send(f'/me There were {fuckups} problems in the data! more')    

    @commands.command()
    async def spam(self, ctx: commands.Context):
        if ((not ctx.author.id == '185142151') and (not ctx.author.id == '179656579')): 
            return
        message = ctx.message.content
        args = message.split(' '); args.pop(0)
        
        if (len(args) < 1): 
            print(f'Error while executing [spam] command: enter how much you want to spam dumbass')
            return
        
        try: 
            amount = int(args.pop(0))
        except:
            print(f'Error while executing [spam] command: invalid number dumbass')
            return
        

        for i in range(amount):
            await ctx.send(' '.join(args))
        


    

bot = Bot()
bot.run()