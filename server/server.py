import time
import asyncio, json
import logging

from game import GameState

class Room:
    def __init__(self):
        self.game = GameState(0,0,0,[])  # placeholder
        self.game_started = False
        self.players = {}  # player_id: websocket

ROOMS = {}

async def handle_main(ws):
    # top-level try/except so we log any unexpected errors and close the socket
    try:
        global ROOMS
        path = ws.request.path
        logging.debug(f"Path: {path}")

        room_name = (path or "/").strip("/") or "default"
        if room_name not in ROOMS:
            ROOMS[room_name] = Room()
        logging.info(f"Client connected to room: {room_name}")

        await handle_room(ws, ROOMS[room_name])

    except Exception:
        logging.error("Unhandled exception in handle_main:", exc_info=True)
        try:
            await ws.close(code=1011, reason="server error")
        except Exception:
            pass

async def handle_room(ws, ROOM):
    # Add new player
    id = time.time()
    ROOM.players[id] = ws
    logging.info(f"Player joined, total = {len(ROOM.players)}")

    # Tell the client what’s happening
    await ws.send(json.dumps({"event": "waiting", "players": len(ROOM.players)}))

    # Start game when we have 2 players
    if len(ROOM.players) == 2 and not ROOM.game_started:
        ROOM.game_started = True
        ROOM.game = GameState(width=10, height=10, mines=10, players=list(ROOM.players.keys()), seed=42)
        # Send start + board to both players
        start_msg = json.dumps({
            "event": "start",
            "rows": ROOM.game.height,
            "cols": ROOM.game.width,
            "mines": ROOM.game.mines,
        })
        await asyncio.gather(*(player_ws.send(start_msg) for player_ws in ROOM.players.values()))

    # Listen for that client's messages
    try:
        async for message in ws:
            try:
                data = json.loads(message)
                await handle_game_message(ws, id, data, ROOM)
            except Exception:
                logging.error("Error handling message from client:", exc_info=True)
                # continue or optionally close on bad message
    except Exception:
        logging.error("Connection loop error:", exc_info=True)
    finally:
        ROOM.players.pop(id, None)
        logging.info("Player left.")

async def handle_game_message(ws, player_id, data, ROOM: Room):
    if data["type"] == "click":
        x, y = data["row"], data["col"]

        # validate coords
        if not (0 <= x < ROOM.game.width and 0 <= y < ROOM.game.height):
            await ws.send(json.dumps({"type": "error", "message": "invalid coordinates"}))
            return

        if ROOM.game.board[x][y] == -1:
            # Player clicked on a mine
            logging.info("Player hit a mine!")
            await handle_loss(player_id, ROOM)
        else:
            # Reveal cells
            revealed = ROOM.game.reveal_from_square(x, y)
            for square in revealed:
                ROOM.game.revealed[player_id].add((square[0], square[1]))
            await ws.send(json.dumps({"type": "reveal", "data": revealed, "found_count": len(ROOM.game.revealed[player_id])}))

            # Check for win
            if ROOM.game.check_win(player_id):
                await handle_win(player_id, ROOM)

async def handle_loss(player_id, ROOM: Room, finish_time=None):
    """Handle win/loss

    This adds functionality for more than 2 players, eg if a player hits a mine they lose, last player standing wins
    """

    loser_ws = ROOM.players[player_id]
    await loser_ws.send(json.dumps({"type": "end", "result": "lose", "time": finish_time}))

    ROOM.game.players_left.remove(player_id)
    if len(ROOM.game.players_left) == 1:
        winner_id = ROOM.game.players_left[0]
        await handle_win(winner_id, ROOM, complete=False)

async def handle_win(player_id, ROOM: Room, complete=True):
    """Handle win

    complete: whether the win is by completing the game (True) or by being last player standing (False)
    """

    winner_ws = ROOM.players[player_id]

    finish_time = None
    if complete:
        finish_time = time.time() - ROOM.game.start_time
        await winner_ws.send(json.dumps({"type": "end", "result": "win", "time": finish_time}))
        for id in ROOM.players.keys():
            if id != player_id:
                await handle_loss(id, ROOM, finish_time)
    else:
        await winner_ws.send(json.dumps({"type": "end", "result": "win"}))