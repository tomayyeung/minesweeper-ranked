we are recreating this in next because you can't deploy a docker image on vercel and i don't want to spend money on a different website

https://github.com/tomayyeung/minesweeper-ranked-online


testing: `uvicorn server.main:app --host 0.0.0.0 --port 8765 --reload`

client: `SERVER_WS="wss://minesweeper-ranked.onrender.com" python3 client/client.py {room_name}`