import asyncio, json

from game import GameState
import time

ROOM = {} # player_id: websocket
GAME_STARTED = False
STATE = None  # game state object we'll define later

async def handle_main(ws):
    global ROOM, GAME_STARTED, STATE

    # Add new player
    id = time.time()
    ROOM[id] = ws
    print("Player joined, total =", len(ROOM))

    # Tell the client what’s happening
    await ws.send(json.dumps({"event": "waiting", "players": len(ROOM)}))

    # Start game when we have 2 players
    if len(ROOM) == 2 and not GAME_STARTED:
        GAME_STARTED = True
        STATE = GameState(width=10, height=10, mines=10, players=list(ROOM.keys()), seed=42)

        # Send start + board to both players
        start_msg = json.dumps({
            "event": "start",
            "rows": STATE.height,
            "cols": STATE.width,
            "mines": STATE.mines,
        })
        await asyncio.gather(*(player_ws.send(start_msg) for player_ws in ROOM.values()))

    # Listen for that client's messages
    try:
        async for message in ws:
            data = json.loads(message)
            await handle_game_message(ws, id, data, STATE)

    finally:
        ROOM.pop(id, None)
        print("Player left.")

async def handle_game_message(ws, player_id, data, game):
    if data["type"] == "click":
        x, y = data["row"], data["col"]
        # await handle_reveal(player_id, x, y)

        # validate coords
        if not (0 <= x < game.width and 0 <= y < game.height):
            await ws.send(json.dumps({"type": "error", "message": "invalid coordinates"}))
            return

        if game.board[x][y] == -1:
            # Player clicked on a mine
            print("Player hit a mine!")
            await handle_loss(player_id)
        else:
            # Reveal cells
            revealed = game.reveal_from_square(x, y)
            for square in revealed:
                game.revealed[player_id].add((square[0], square[1]))
            await ws.send(json.dumps({"type": "reveal", "data": revealed, "found_count": len(game.revealed[player_id])}))

            # Check for win
            if game.check_win(player_id):
                await handle_win(player_id)

async def handle_loss(player_id, finish_time=None):
    """Handle win/loss

    This adds functionality for more than 2 players, eg if a player hits a mine they lose, last player standing wins
    """
    if not STATE:
        return

    loser_ws = ROOM[player_id]
    await loser_ws.send(json.dumps({"type": "end", "result": "lose", "time": finish_time}))

    STATE.players_left.remove(player_id)
    if len(STATE.players_left) == 1:
        winner_id = STATE.players_left[0]
        # winner_ws = ROOM[winner_id]
        await handle_win(winner_id, complete=False)


async def handle_win(player_id, complete=True):
    """Handle win

    complete: whether the win is by completing the game (True) or by being last player standing (False)
    """
    if not STATE:
        return

    winner_ws = ROOM[player_id]

    finish_time = None
    if complete:
        finish_time = time.time() - STATE.start_time
        await winner_ws.send(json.dumps({"type": "end", "result": "win", "time": finish_time}))
        for id in ROOM.keys():
            if id != player_id:
                await handle_loss(id, finish_time)
        # print("Finish time:", finish_time)
    else:
        await winner_ws.send(json.dumps({"type": "end", "result": "win"}))