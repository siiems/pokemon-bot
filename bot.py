from twitchio.ext import commands
import time
import random
from general import *
import requests




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
    

def addUser(userid : str) -> None:
    if (getUserIndex(userid) != -1):return
    userdata = getJsonData('./users.json')
    newdata = basic_userdata
    newdata['userid'] = userid
    userdata.append(newdata)
    writeJsonData('./users.json', userdata)


def getUserIndex(userid : str) -> int:
    userdata = getJsonData('./users.json')
    for i in range(len(userdata)):
            if (userdata[i]['userid'] == userid):return i  
    return -1

def getToken() -> str:
    tokendata = getJsonData('./token.json')
    return tokendata[1]["access_token"]

def getClientID() -> str:
    tokendata = getJsonData('./token.json')
    return tokendata[0]['clientid']

async def getUserData(userid : str = None, userlogin : str = None) -> dict:
    if userid != None:
        data = f'?id={userid}'
    elif userlogin != None:
        data = f'?login={userlogin}'
    else:
        return None
    
    token = getToken()
    clientid = getClientID()
    twitch_headers = {
        'Authorization': f'Bearer {token}',
        'Client-Id': f'{clientid}'
        }
    res = requests.get(f'https://api.twitch.tv/helix/users{data}', headers=twitch_headers)
    if res.status_code != 200:
        print(f'Error while getting user data | {res.status_code} {res.json()}')
        return None
    return res.json()



oauth_token = refreshToken()

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=f'oauth:{oauth_token}', prefix='*', initial_channels=['siiems'])

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
            await ctx.send(f'@{ctx.author.name} that user has no data! mad')
            return
        if (len(userdata[userIndex]['cards']) < 1):
            await ctx.send(f'@{ctx.author.display_name} {refer} have 0 cards! mad')
            return
        cards = ""
        originallen = 0
        for card in userdata[userIndex]['cards']:
            if card['amount'] > 0:
                cards += f'| {card["name"].capitalize()} {card["amount"]} '
        if (len(cards) == originallen):
            await ctx.send(f'@{ctx.author.display_name} {refer} have 0 cards! mad')
            return
        money = userdata[userIndex]['money']
        await ctx.send(f'${money:,.2f} {cards}')
        


    

bot = Bot()
bot.run()