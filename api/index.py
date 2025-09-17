import requests
import random
from flask import Flask, jsonify, request
from datetime import datetime, timedelta, timezone
import hmac
import hashlib
import base64
import time
import secrets
import os

authweb = "https://discord.com/api/webhooks/1417532904489095168/CJ0ma3BQr5TjyJIfln60CnBMdZlUVFBTgron3S_ihk6Wxc1bYEt7AY-9X9lvJ4UQYGNN"
namecheckweb = "https://discord.com/api/webhooks/1417532904489095168/CJ0ma3BQr5TjyJIfln60CnBMdZlUVFBTgron3S_ihk6Wxc1bYEt7AY-9X9lvJ4UQYGNN"
normalweb = "https://discord.com/api/webhooks/1417532904489095168/CJ0ma3BQr5TjyJIfln60CnBMdZlUVFBTgron3S_ihk6Wxc1bYEt7AY-9X9lvJ4UQYGNN"
Photonweb = "https://discord.com/api/webhooks/1417532904489095168/CJ0ma3BQr5TjyJIfln60CnBMdZlUVFBTgron3S_ihk6Wxc1bYEt7AY-9X9lvJ4UQYGNN"

class GameInfo:
    def __init__(self):
        self.TitleId = "1D8CA4"
        self.SecretKey = "EN4U5Q5MPJPD1PX79ONM486X9GRN1QDNDYFQZ37T3J3P6JZOX8"
        self.ApiKey = "OC|10055646007818382|ae59d45104c34e9d4d38d147d4c307f2"
        self.HmacSecret = os.getenv("7AUTHIresthebutpoopper") or secrets.token_urlsafe(32)


        if not os.getenv("7AUTHIresthebutpoopper"):
            print(f"Generated new HMAC secret: {self.HmacSecret}")
            print("trust me, save this somewhere safe, you will need it to validate signed tokens gng..")

    def GetAuthHeaders(self) -> dict:
        return {
            "content-type": "application/json",
            "X-SecretKey": self.SecretKey
        }

    def GetTitle(self) -> str:
        return self.TitleId

settings = GameInfo()
app = Flask(__name__)
playfabCache = {}
muteCache = {}

settings.TitleId = "BLABLABLA"
settings.SecretKey = "BLABLABLA"
settings.ApiKey = "BLABLABLA"

def ReturnFunctionJson(data, funcname, funcparam={}):
    rjson = data.get("FunctionParameter", {})
    userId = rjson.get("CallerEntityProfile", {}).get("Lineage", {}).get("TitlePlayerAccountId")

    req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/ExecuteCloudScript",
        json={
            "PlayFabId": userId,
            "FunctionName": funcname,
            "FunctionParameter": funcparam
        },
        headers=settings.GetAuthHeaders()
    )

    if req.status_code == 200:
        return jsonify(req.json().get("data").get("FunctionResult")), req.status_code
    else:
        return jsonify({}), req.status_code

def GetIsNonceValid(nonce: str, oculusId: str):
    req = requests.post(
        url=f'https://graph.oculus.com/user_nonce_validate?nonce={nonce}&user_id={oculusId}&access_token={settings.ApiKey}',
        headers={
            "content-type": "application/json"
        }
    )
    return req.json().get("is_valid")

def send_discord_webhook(webhook_url, embed_data):
    """Send Discord webhook with embed"""
    try:
        if webhook_url and "REPLACE" not in webhook_url:
            payload = {
                "content": None,
                "embeds": [embed_data],
                "attachments": []
            }
            requests.post(webhook_url, json=payload, timeout=5)
        else:
            print(f"Discord webhook: {embed_data}")
    except Exception as e:
        print(f"Discord webhook error: {e}")
def generate_signed_token(user_id: str, expiration_minutes: int = 60) -> str:
    timestamp = int(time.time())
    payload = f"{user_id}|{timestamp + (expiration_minutes * 60)}"
    signature = hmac.new(settings.HmacSecret.encode(), payload.encode(), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(f"{payload}|{signature.hex()}".encode()).decode()
    return token
def validate_signed_token(token: str) -> bool:
    try:
        decoded = base64.urlsafe_b64decode(token).decode()
        user_id, expiration, signature = decoded.split("|")
        payload = f"{user_id}|{expiration}"
        expected_signature = hmac.new(settings.HmacSecret.encode(), payload.encode(), hashlib.sha256).digest().hex()
        if signature != expected_signature:
            return False
        if int(time.time()) > int(expiration):
            return False
        return True
    except:
        return False

@app.route("/", methods=["POST", "GET"])
def main():
    return "it workie"

@app.route("/api/PlayFabAuthentication", methods=["POST", "GET"])
def playfabauthentication():
    rjson = request.get_json()

    if rjson.get("CustomId") is None:
        return jsonify({"Message": "missing customid", "Error": "no customId"})
    if rjson.get("Nonce") is None:
        return jsonify({"Message": "missing nonce", "Error": "no nonce"})
    if rjson.get("AppId") is None:
        return jsonify({"Message": "missing appid", "Error": "no appId"})
    if rjson.get("Platform") is None:
        return jsonify({"Message": "missing platform", "Error": "no platform"})
    if rjson.get("OculusId") is None:
        return jsonify({"Message": "missing oculusid", "Error": "no oculusId"})

    oculus_id = rjson.get("OculusId")
    nonce = rjson.get("Nonce")
    if not GetIsNonceValid(nonce, oculus_id):
        return jsonify({"Message": "invalid nonce", "Error": "bruh invalid nonce"}), 401

    org_req = requests.get(
        f"https://graph.oculus.com/{oculus_id}?access_token={settings.ApiKey}&fields=org_scoped_id",
        headers={"Content-Type": "application/json"}
    )
    OrgScope = org_req.json().get("org_scoped_id")
    CustomId = f"OCULUS{OrgScope}"

    alias_req = requests.get(
        f"https://graph.oculus.com/{oculus_id}?access_token={settings.ApiKey}&fields=alias",
        headers={"Content-Type": "application/json"}
    )
    meta_alias = alias_req.json().get("alias")

    if OrgScope is None:
        return jsonify({"Message": "missing orgscope", "Error": "no orgScopedId"})
    if meta_alias is None:
        return jsonify({"Message": "missing meta alias", "Error": "no metaAlias"})

    if rjson.get("AppId") != settings.TitleId:
        return jsonify({"Message": "Request sent for the wrong App ID", "Error": "BadRequest-AppIdMismatch"})
    if not rjson.get("CustomId").startswith("OC") and not rjson.get("CustomId").startswith("PI"):
        return jsonify({"Message": "Bad request", "Error": "BadRequest-No OC or PI Prefix"})

    if rjson.get("Platform") == "Windows":
        return jsonify({"Message": "scary hacker", "Error": "Forbidden-Platform"}), 403

    original_custom_id = rjson.get("CustomId")
    if original_custom_id == "OCULUS0":
        ban_req = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Admin/BanUsers",
            json={
                "Bans": [
                    {
                        "PlayFabId": rjson.get("currentPlayerId"),
                        "DurationInHours": None, 
                        "Reason": "CHEATING."
                    }
                ]
            },
            headers=settings.GetAuthHeaders()
        )
        if ban_req.status_code == 200:
            return jsonify({"Message": "bro was banned for: Lemonloader", "Error": "Banned"}), 403
        else:
            return jsonify({"Message": "Failed to ban user", "Error": "InternalError"}), 500

    url = f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId"
    login_request = requests.post(
        url=url,
        json={
            "ServerCustomId": CustomId,
            "CreateAccount": True
        },
        headers=settings.GetAuthHeaders()
    )

    if login_request.status_code == 200:
        data = login_request.json().get("data")
        sessionTicket = data.get("SessionTicket")
        entityToken = data.get("EntityToken").get("EntityToken")
        playFabId = data.get("PlayFabId")
        entityType = data.get("EntityToken").get("Entity").get("Type")
        entityId = data.get("EntityToken").get("Entity").get("Id")

        print(requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Client/LinkCustomID",
            json={
                "ForceLink": True,
                "CustomId": CustomId
            },
            headers=settings.GetAuthHeaders()
        ).json())
        signed_token = generate_signed_token(playFabId)

        embed = {
            "color": 3447003,
            "fields": [{
                "name": "PLAYFAB AUTH: PLAYER LOGGED IN",
                "value": f"```ini\n[PlayFab ID]: {playFabId}\n[Custom ID]: {CustomId}\n[IP Address]: {request.headers.get('X-Real-IP', request.remote_addr)}\n[Meta Quest Username]: {meta_alias}```"
            }],
            "author": {
                "name": "PLAYFAB AUTH"
            },
            "footer": {
                "text": "RATPOOP"
            }
        }
        send_discord_webhook(authweb, embed)

        return jsonify({
            "PlayFabId": playFabId,
            "SessionTicket": sessionTicket,
            "EntityToken": entityToken,
            "EntityId": entityId,
            "EntityType": entityType,
            "SignedToken": signed_token 
        })
    else:
        if login_request.status_code == 403:
            ban_info = login_request.json()
            if ban_info.get('errorCode') == 1002:
                ban_message = ban_info.get('errorMessage', "BRO, you didn't provide a ban message!")
                ban_details = ban_info.get('errorDetails', {})
                ban_expiration_key = next(iter(ban_details.keys()), None)
                ban_expiration_list = ban_details.get(ban_expiration_key, [])
                ban_expiration = ban_expiration_list[0] if len(ban_expiration_list) > 0 else "No expiration date found cuh."
                print(ban_info)
                return jsonify({
                    'BanMessage': ban_expiration_key,
                    'BanExpirationTime': ban_expiration
                }), 403
            else:
                error_message = ban_info.get('errorMessage', 'no ban info found')
                return jsonify({
                    'Error': 'PlayFab Error',
                    'Message': error_message
                }), 403
        else:
            error_info = login_request.json()
            error_message = error_info.get('errorMessage', 'error.')
            return jsonify({
                'Error': 'PlayFab Error',
                'Message': error_message
            }), login_request.status_code

@app.route("/api/CachePlayFabId", methods=["POST", "GET"])
def cacheplatfabid():
    rjson = request.get_json()
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    playfabCache[rjson.get("PlayFabId")] = rjson

    return jsonify({"Message": "Success"}), 200

@app.route('/api/TitleData', methods=['POST'])
def titled_data():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    return jsonify({"MOTD": "pp"})

@app.route("/api/CheckForBadName", methods=["POST", "GET"])
def checkforbadname():
    rjson = request.get_json()
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    function_result = rjson["FunctionArgument"]
    playfab_id = rjson["CallerEntityProfile"]["Lineage"]["MasterPlayerAccountId"]
    name = function_result["name"].upper()
    forRoom = function_result["forRoom"]
    embed = {
        "color": 16776960,
        "fields": [{
            "name": "CHECK FOR BAD NAME",
            "value": f"```ini\n[PlayFab ID]: {playfab_id}\n[Display Name]: {name}\n[For Room]: {forRoom}\n[IP Address]: {request.headers.get('X-Real-IP', request.remote_addr)}```"
        }],
        "author": {
            "name": "CFBN"
        },
        "footer": {
            "text": "CREDITS TO IRES"
        }
    }
    send_discord_webhook(namecheckweb, embed)

    if forRoom == True:
        return jsonify({"result": 0})

    link_response = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Admin/UpdateUserTitleDisplayName",
        json={
            "DisplayName": name,
            "PlayFabId": playfab_id,
        },
        headers=settings.GetAuthHeaders(),
    ).json()
    return jsonify({"result": 0})

@app.route("/api/GetAcceptedAgreements", methods=['POST', 'GET'])
def GetAcceptedAgreements():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    data = request.json

    return jsonify({"PrivacyPolicy": "1.1.67", "TOS": "11.05.22.2"}), 200

@app.route("/api/SubmitAcceptedAgreements", methods=['POST', 'GET'])
def SubmitAcceptedAgreements():

    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    data = request.json

    return jsonify({"PrivacyPolicy": "1.1.67", "TOS": "11.05.22.2"}), 200

@app.route('/api/GetName', methods=['POST', 'GET'])
def GetName():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    return jsonify({"result": f"GORILLA{random.randint(1000,9999)}"})

@app.route("/api/ConsumeOculusIAP", methods=["POST", "GET"])
def consumeoculusiap():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    rjson = request.get_json()

    accessToken = rjson.get("userToken")
    userId = rjson.get("userID")
    playFabId = rjson.get("playFabId")
    nonce = rjson.get("nonce")
    platform = rjson.get("platform")
    sku = rjson.get("sku")
    debugParams = rjson.get("debugParemeters")
    if not GetIsNonceValid(nonce, userId):
        return jsonify({"Message": "Invalid Nonce", "Error": "Unauthorized-InvalidNonce"}), 401

    req = requests.post(
        url=f"https://graph.oculus.com/consume_entitlement?nonce={nonce}&user_id={userId}&sku={sku}&access_token={settings.ApiKey}",
        headers={
            "content-type": "application/json"
        }
    )

    if bool(req.json().get("success")):
        return jsonify({"result": True})
    else:
        return jsonify({"error": True})

@app.route("/api/ReturnMyOculusHashV2")
def returnmyoculushashv2():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    return ReturnFunctionJson(request.get_json(), "ReturnMyOculusHash")

@app.route("/api/ReturnCurrentVersionV2", methods=["POST", "GET"])
def returncurrentversionv2():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    return ReturnFunctionJson(request.get_json(), "ReturnCurrentVersion")

@app.route("/api/TryDistributeCurrencyV2", methods=["POST"])
def TryDistributeCurrencyV2():
    if request.method != "POST":
        return "", 404

    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token", "Error": "Unauthorized"}), 401

    rjson = request.json
    sr_a_day = 500  # You can change, I don't really care.
    current_player_id = rjson.get("CallerEntityProfile", {}).get("Lineage", {}).get("MasterPlayerAccountId")

    get_data_response = requests.post(
        f"https://{settings.TitleId}.playfabapi.com/Server/GetUserReadOnlyData",
        headers=settings.GetAuthHeaders(),
        json={
            "PlayFabId": current_player_id,
            "Keys": ["DailyLogin"]
        }
    )

    daily_login_value = get_data_response.json().get("data").get("Data").get("DailyLogin", {}).get("Value", None)

    last_login_date = None
    if daily_login_value:
        last_login_date = datetime.fromisoformat(daily_login_value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    if not last_login_date or last_login_date < datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc):
        requests.post(
            f"https://{settings.TitleId}.playfabapi.com/Server/AddUserVirtualCurrency",
            headers=settings.GetAuthHeaders(),
            json={
                "PlayFabId": current_player_id,
                "VirtualCurrency": "SR",
                "Amount": sr_a_day
            }
        )

        requests.post(
            f"https://{settings.TitleId}.playfabapi.com/Server/UpdateUserReadOnlyData",
            headers=settings.GetAuthHeaders(),
            json={
                "PlayFabId": current_player_id,
                "Data": {
                    "DailyLogin": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc).isoformat()
                }
            }
        )

    return "", 200

@app.route("/api/BroadCastMyRoomV2", methods=["POST", "GET"])
def broadcastmyroomv2():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token!", "Error": "Unauthorized"}), 401

    rjson = request.get_json()
    function_param = rjson.get("FunctionParameter", {})
    
    
    embed = {
        "color": 16384229,
        "fields": [{
            "name": "GORILLA BOT BRODCAST",
            "value": f"```ini\n[Room ID]: {function_param.get('GameId', 'Unknown')}\n[Region]: {function_param.get('Region', 'Unknown').upper()}\n[Creator]: {function_param.get('CreatorName', 'Unknown')}\n[IP Address]: {request.headers.get('X-Real-IP', request.remote_addr)}```"
        }],
        "author": {
            "name": "ROOM LOG"
        },
        "footer": {
            "text": "CATBUT"
        }
    }
    send_discord_webhook(normalweb, embed)

    return ReturnFunctionJson(request.get_json(), "BroadCastMyRoom", request.get_json()["FunctionParameter"])

@app.route("/api/ShouldUserAutomutePlayer", methods=["POST", "GET"])
def shoulduserautomuteplayer():
    signed_token = request.headers.get("X-Signed-Token")
    if not signed_token or not validate_signed_token(signed_token):
        return jsonify({"Message": "Invalid or expired token get a valid token dumbass", "Error": "Unauthorized"}), 401

    return jsonify(muteCache)
@app.route("/api/photon", methods=["POST"])
def photonauth():
    print(f"Received {request.method} at /api/photon")
    getjson = request.get_json()
    Ticket = getjson.get("Ticket")
    Nonce = getjson.get("Nonce")
    Platform = getjson.get("Platform")
    UserId = getjson.get("UserId")
    nickName = getjson.get("username")

    if Nonce and UserId and not GetIsNonceValid(Nonce, UserId):
        return jsonify({"Message": "Invalid Nonce", "Error": "Unauthorized-InvalidNonce"}), 401

    if UserId:
        org_req = requests.get(
            f"https://graph.oculus.com/{UserId}?access_token={settings.ApiKey}&fields=org_scoped_id",
            headers={"Content-Type": "application/json"}
        )
        OrgScope = org_req.json().get("org_scoped_id")
        CustomId = f"OCULUS{OrgScope}"

        alias_req = requests.get(
            f"https://graph.oculus.com/{UserId}?access_token={settings.ApiKey}&fields=alias",
            headers={"Content-Type": "application/json"}
        )
        meta_alias = alias_req.json().get("alias")

    signed_token = request.headers.get("X-Signed-Token")
    if signed_token and not validate_signed_token(signed_token):
        return jsonify({"Message": "FAILED", "Error": "Unauthorized"}), 401

    if request.method.upper() == "GET":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        userId = Ticket.split('-')[0] if Ticket else None
        print(f"userid: {UserId}")

        if userId is None or len(userId) != 16:
            print("fuh, no good userid")
            return jsonify({
                'resultCode': 2,
                'message': 'FUH',
                'userId': None,
                'nickname': None
            })

        if Platform != 'Quest':
            return jsonify({'Error': 'Bad request', 'Message': 'bro Invalid platform!'}),403

        if Nonce is None:
            return jsonify({'Error': 'Bad request', 'Message': 'HAHA, YOU ARE NOT AUTHENTICATED!'}),304

        req = requests.post(
            url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
            json={"PlayFabId": userId},
            headers={
                "content-type": "application/json",
                "X-SecretKey": settings.SecretKey
            })

        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
            nickname = req.json().get("data", {}).get("UserInfo", {}).get("TitleInfo", {}).get("DisplayName")
            if not nickname:
                nickname = None

           
            embed = {
                "color": 65280,
                "fields": [{
                    "name": "PHOTON AUTH",
                    "value": f"```ini\n[User ID]: {userId.upper()}\n[Nickname]: {nickname or 'None'}\n[Platform]: {Platform}\n[IP Address]: {request.headers.get('X-Real-IP', request.remote_addr)}```"
                }],
                "author": {
                    "name": "PHOTON AUTH LOGS SIGMER"
                },
                "footer": {
                    "text": "CREDITS TO IRES"
                }
            }
            send_discord_webhook(Photonweb, embed)

            print(
                f"user authed {userId.lower()} Nickname: {nickname}"
            )

            return jsonify({
                'resultCode': 1,
                'message':
                f'Authed {userId.lower()} Title {settings.TitleId.lower()}',
                'userId': f'{userId.upper()}',
                'nickname': nickname
            })
        else:
            print("Failed!")
            return jsonify({
                'resultCode': 0,
                'message': "Something is wrong",
                'userId': None,
                'nickname': None
            })

    elif request.method.upper() == "POST":
        rjson = request.get_json()
        print(f"{request.method} : {rjson}")

        ticket = rjson.get("Ticket")
        userId = ticket.split('-')[0] if ticket else None
        print(f"UserId: {userId}")

        if userId is None or len(userId) != 16:
            print("fuh, no good userid")
            return jsonify({
                'resultCode': 2,
                'message': 'FUH',
                'userId': None,
                'nickname': None
            })

        req = requests.post(
             url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
             json={"PlayFabId": userId},
             headers={
                 "content-type": "application/json",
                 "X-SecretKey": settings.SecretKey
             })

        print(f"Authenticated user {userId.lower()}")
        print(f"Request to PlayFab returned status code: {req.status_code}")

        if req.status_code == 200:
             nickname = req.json().get("data", {}).get("UserInfo", {}).get("TitleInfo", {}).get("DisplayName")
             if not nickname:
                 nickname = None

            
             embed = {
                 "color": 65280,
                 "fields": [{
                     "name": "PHOTON AUTH",
                     "value": f"```ini\n[User ID]: {userId.upper()}\n[Nickname]: {nickname or 'None'}\n[Platform]: Quest\n[IP Address]: {request.headers.get('X-Real-IP', request.remote_addr)}```"
                 }],
                 "author": {
                     "name": "PHOTON AUTH LOGS SIGMER"
                 },
                 "footer": {
                     "text": "CREDITS TO IRES"
                 }
             }
             send_discord_webhook(Photonweb, embed)

             return jsonify({
                 'resultCode': 1,
                 'message':
                 f'Authenticated user {userId.lower()} title {settings.TitleId.lower()}',
                 'userId': f'{userId.upper()}',
                 'nickname': nickname
             })
        else:
             print("Failed to get user account info from PlayFab")
             successJson = {
                 'resultCode': 0,
                 'message': "Something went wrong",
                 'userId': None,
                 'nickname': None
             }
             authPostData = {}
             for key, value in authPostData.items():
                 successJson[key] = value
             print(f"Returning successJson: {successJson}")
             return jsonify(successJson)
    else:
         print(f"Invalid method: {request.method.upper()}")
         return jsonify({
             "Message":
             "use post or get method instead of " + request.method.upper()
         })


if __name__ == "__main__":
    app.run("0.0.0.0", 8080) # Made by ires. Gave to l1rson! Please do not steal or skid this.
