import asyncio
import socketio
import json
from random_user_agent.user_agent import UserAgent

#loop = asyncio.get_event_loop()
sio = socketio.AsyncClient()

@sio.event
async def connect():
    global django_matches, subscribed_matches

    django_matches = [2389587]
    subscribed_matches = []

    #if not redis:
    #    await sio.disconnect()
    sio.start_background_task(get_live_matches)


@sio.event
async def score(data):
    #global redis
    print("stored new live data for {}".format(data.get('listId')))
    print("dump: {}".format(json.dumps(data)))
    #await redis.hset('live_results', data.get('listId'), json.dumps(data))

@sio.event
async def scoreboard(data):
    for p in data.get('TERRORIST'):
        print("set TERRORIST: {}".format(p))
    #    await redis.hset('steamid_db', p.get('dbId'), p.get('steamId'))
    #for p in data.get('CT'):
    #    await redis.hset('steamid_db', p.get('dbId'), p.get('steamId'))


@sio.event
async def connect_error(data):
    print("The connection failed!")

@sio.event
async def disconnect():
    #global redis
    #redis.close()
    #await redis.wait_closed()
    print("I'm disconnected!")


async def start_server(loop):    
    user_agent_rotator = UserAgent()
    headers = {}
    headers['User-Agent'] = user_agent_rotator.get_random_user_agent()
    await sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="websocket")
    #await sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="socket.io")
    #await sio.connect('https://scorebot-secure.hltv.org')
    await sio.wait()


async def get_live_matches():
    while True:
        print("checking for new live_matches")
        global django_matches, subscribed_matches
        for m in django_matches:
            if m not in subscribed_matches:
                await sio.emit("readyForScores",
                                data=json.dumps({"token": "", "listIds": [m]}))
                await sio.emit("readyForMatch", data=json.dumps({"token": "", "listId": m}))
                print("emitted match subscription for {}".format(m))
                subscribed_matches.append(m)

        await sio.sleep(60)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(start_server(loop=loop))
    except KeyboardInterrupt:
        pass

#loop.run_until_complete(start_server())