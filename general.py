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