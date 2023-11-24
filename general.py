import json
import requests


def getJsonData(jsonFile):
    with open(jsonFile, 'r') as file:
        data = json.load(file)
    file.close()
    return data


def writeJsonData(jsonFile, data):
    data = json.dumps(data, indent=4)
    with open(jsonFile, 'w') as file:
        file.write(data)


def refreshToken():
    twitch_url = 'https://id.twitch.tv/oauth2/token'
    twitch_headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    tokenData = getJsonData('token.json')

    clientid = tokenData[0]['clientid']
    clientsecret = tokenData[0]['clientsecret']
    refreshToken = tokenData[1]["refresh_token"]

    twitch_data = f'grant_type=refresh_token&refresh_token={refreshToken}&client_id={clientid}&client_secret={clientsecret}'

    twitch_response = requests.post(twitch_url, headers=twitch_headers, data=twitch_data)
    newTokenData = json.loads(twitch_response.text)

    tokenData[1] = newTokenData

    writeJsonData('token.json', tokenData)

    tokenData = getJsonData('token.json')
    accessToken = tokenData[1]["access_token"]
    return accessToken



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
    
def getUserIndex(userid : str) -> int:
    userdata = getJsonData('./users.json')
    for i in range(len(userdata)):
            if (userdata[i]['userid'] == userid):
                return i  
    return -1


def addUser(userid : str) -> None:
    if (getUserIndex(userid) != -1):
        return
    userdata = getJsonData('./users.json')
    newdata = basic_userdata
    newdata['userid'] = userid
    userdata.append(newdata)
    writeJsonData('./users.json', userdata)




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

def fixdata() -> int:
    users = getJsonData('./users.json')
    prevUsers = []
    fuckups = 0
    for i in range(len(users)):
        if (users[i]['userid'] not in prevUsers):
            prevUsers.append(users[i]['userid'])
        else:
            users[i] = {}
            fuckups += 1
            continue
        prevCards = []
        for j in range(len(users[i]['cards'])):
            if (users[i]['cards'][j]['name'] not in prevCards):
                prevCards.append(users[i]['cards'][j]['name'])
            else:
                users[i]['cards'][j] = {}
                fuckups += 1
        users[i]['cards'] = list(filter(lambda a: a != {}, users[i]['cards']))
    users = list(filter(lambda a: a != {}, users))
    writeJsonData('./users.json', users)
    return fuckups
