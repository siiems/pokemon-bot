from twitchio.ext import commands
import time
import random
from general import *




def getCardNames():
    carddata = getJsonData('./cards.json')
    cardnames = []
    for card in carddata:
        cardnames.append(card['name'].lower())
    return cardnames

cardnames = getCardNames()



basic_userdata = {
        "userid": "",
        "money": 0,
        "last_opened": 0.0,
        "cards":[

        ]
    }
    

def addUser(userid):
    if (getUserIndex(userid) == None):return
    userdata = getJsonData('./users.json')
    newdata = basic_userdata
    newdata['userid'] = userid
    userdata.append(newdata)
    writeJsonData('./users.json', userdata)


def getUserIndex(userid):
    userdata = getJsonData('./users.json')
    for i in range(len(userdata)):
            if (userdata[i]['userid'] == userid):return i  
    return None




oauth_token = refreshToken()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=f'oauth:{oauth_token}', prefix='!', initial_channels=['flekyu','dluxpup','oshgay','siiems'])

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
            await ctx.send(f"@{username}, you can open another pack in {round(((userdata[userIndex]['last_opened']+cooldown)-now) / 60,2)} minutes. mad")
            return 
        card = random.choice(carddata)  # Randomly select a card from the list
        userdata[userIndex]['last_opened'] = now


        cardinvIndex = False

        if (len(userdata[userIndex]['cards']) > 0):
            for i in range(len(userdata[userIndex]['cards'])):
                if (userdata[userIndex]['cards'][i]['name']) == card['name']:
                    cardinvIndex = i

        if (not cardinvIndex):
            userdata[userIndex]['cards'].append({
                "name": card['name'],
                "amount": 1
            })
        else:
            userdata[userIndex]['cards'][cardinvIndex]['amount'] += 1

        writeJsonData('./users.json',userdata)
        await ctx.send(f"@{username}, you unpacked a {card['rarity']} {card['name']}. Type !sell to sell it for {card['value']} coins woah") 




    @commands.command() # flekyu: !sell [card_name]
    async def sell(self, ctx: commands.Context):
        addUser(ctx.author.id)

        args = ctx.message.content.lower().split(' ')
        amount = 0
        if (len(args) < 2): return
        

        username = ctx.author.name.lower()


        card_name = args[1]


        if (not (card_name in cardnames)): 
            await ctx.send(f'@{username} unknown card mad')
            return

        carddata = getJsonData('./cards.json')
        userdata = getJsonData('./users.json')
        userIndex = getUserIndex(ctx.author.id)

        for i in range(len(carddata)):
            if (carddata[i]['name'].lower() == card_name):
                cardIndex = i


        usercardIndex = None
        for i in range(len(userdata[userIndex]['cards'])):
            if (userdata[userIndex]['cards'][i]['name'].lower() == card_name):
                usercardIndex = i
                break

        if (usercardIndex == None): 
            await ctx.send(f'@{username} you have no {card_name.capitalize()} cards! doid')
            return

        if (len(args) == 2): amount = 1
        else:
            if (not args[2].isnumeric()):
                if (args[2] == 'all'):
                    amount = userdata[userIndex]['cards'][usercardIndex]['amount']
                else:
                    return
            else:
                amount = int(args[2])

        if (amount < 1):
            return

        if (amount > userdata[userIndex]['cards'][usercardIndex]['amount']): 
            await ctx.send(f"@{username} you don't have {amount} {card_name.capitalize()} cards doid")
            return
        
        userdata[userIndex]['cards'][usercardIndex]['amount'] -= amount
        revenue = carddata[cardIndex]['value'] * amount
        userdata[userIndex]['money'] += revenue

        writeJsonData('./users.json', userdata)
        await ctx.send(f'@{username} succesfully sold {amount} {card_name.capitalize()} cards for {revenue:,.2f} woah') 

    @commands.command()
    async def collection(self, ctx: commands.Context):
        addUser(ctx.author.id)

        userdata = getJsonData('./users.json')
        userIndex = getUserIndex(ctx.author.id)

        if (len(userdata[userIndex]['cards']) < 1):
            await ctx.send(f'@{ctx.author.display_name} you have 0 cards! mad')
            return
        
        originallen = len(f"@{ctx.author.display_name}'s cards: ")
        cards = f"@{ctx.author.display_name}'s cards: "
        for card in userdata[userIndex]['cards']:
            if card['amount'] > 0:
                cards += f'| {card["name"].capitalize()}: {card["amount"]} '

        if (len(cards) == originallen):
            await ctx.send(f'@{ctx.author.display_name} you have 0 cards! mad')
            return
        
        await ctx.send(f'{cards} Smile')
        


    

bot = Bot()
bot.run()