from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from server.game import GameState
import asyncio, json

app = FastAPI()
rooms = {} # room_name: {"board": [[...]], "players": [WebSocket, ...]}

@app.websocket("/ws/{room_name}")
async def websocket_endpoint(ws: WebSocket, room_name: str):
    await ws.accept()

    # temporary default board size
    rows = 10  # number of rows
    cols = 10  # number of columns
    mines = 10

    game = GameState(cols, rows, mines, 2, seed=42)

    # Create room if not exists
    if room_name not in rooms:
        # generate_board(width, height, mines)
        rooms[room_name] = {
            "board": game.board,
            "players": []
        }
    room = rooms[room_name]
    room["players"].append(ws)
    player_num = len(room["players"]) - 1

    # Send board metadata to player
    await ws.send_text(json.dumps({
        "type": "board",
        "rows": rows,
        "cols": cols,
        "mines": mines,
    }))

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "click":
                r, c = msg.get("row"), msg.get("col")

                # validate coords
                if not (0 <= r < rows and 0 <= c < cols):
                    await ws.send_text(json.dumps({"type": "error", "message": "invalid coordinates"}))
                    continue

                if room["board"][r][c] == -1:
                    # Player clicked on a mine
                    print("Player hit a mine!")
                    await ws.send_text(json.dumps({"type": "end", "result": "lose"}))

                    # Notify other players; iterate over a copy to allow removals
                    for player in list(room["players"]):
                        res = "lose" if player is ws else "win"

                        try:
                            await player.send_text(json.dumps({"type": "end", "result": res}))
                        except Exception:
                            # if send fails, remove the player
                            try:
                                room["players"].remove(player)
                            except ValueError:
                                pass
                else:
                    # Reveal cells
                    revealed = game.reveal_from_square(r, c)
                    for square in revealed:
                        game.revealed[player_num].add((square[0], square[1]))
                    await ws.send_text(json.dumps({"type": "reveal", "data": revealed, "found_count": len(game.revealed[player_num])}))

                    # Check for win
                    if len(game.revealed[player_num]) == rows * cols - mines:
                        print("Player has found all safe squares!")
                        await ws.send_text(json.dumps({"type": "end", "result": "win"}))

                        # Notify other players; iterate over a copy to allow removals
                        for player in list(room["players"]):
                            res = "win" if player is ws else "lose"

                            try:
                                await player.send_text(json.dumps({"type": "end", "result": res}))
                            except Exception:
                                # if send fails, remove the player
                                try:
                                    room["players"].remove(player)
                                except ValueError:
                                    pass

    except WebSocketDisconnect:
        # clean up player
        try:
            room["players"].remove(ws)
        except ValueError:
            pass
        # if room is empty remove it
        if not room["players"]:
            try:
                del rooms[room_name]
            except KeyError:
                pass

async def notify_win(room, winner_ws):
    """Notify all players in the room of the game result."""
    for player in list(room["players"]):
        res = "win" if player is winner_ws else "lose"

        try:
            await player.send_text(json.dumps({"type": "end", "result": res}))
        except Exception:
            # if send fails, remove the player
            try:
                room["players"].remove(player)
            except ValueError:
                pass