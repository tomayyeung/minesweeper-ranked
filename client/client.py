import pygame, asyncio, websockets, json

WIDTH, HEIGHT = 400, 500
# ROWS, COLS = 10, 10
# CELL_SIZE = WIDTH // COLS

# Colors
BG_COLOR = (40, 40, 40)
REVEALED_COLOR = (200, 200, 200)
HIDDEN_COLOR = (100, 100, 100)
FONT_COLOR = (0, 0, 0)

async def handle_server(uri):
    async with websockets.connect(uri) as ws:
        print("Connected to server!")

        # Wait for board from server
        data = json.loads(await ws.recv())
        print("Waiting, players:", data.get("players", 0))

        # waiting for start message
        while True:
            data = json.loads(await ws.recv())
            if data.get("event") == "start":
                break
        rows, cols, mines = data["rows"], data["cols"], data["mines"]
        to_be_found = rows * cols - mines

        cell_size = WIDTH // cols

        # Setup pygame
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("1v1 Minesweeper")

        font = pygame.font.SysFont(None, 36)
        clock = pygame.time.Clock()

        board = [[-1]*cols for _ in range(rows)] # -1 means hidden
        revealed = [[False]*cols for _ in range(rows)] # used for drawing
        found = 0

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    row, col = y // cell_size, x // cell_size
                    # send click to server
                    await ws.send(json.dumps({"type": "click", "row": row, "col": col}))

            # Non-blocking receive
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                event = json.loads(msg)

                # Reveal cells
                if event["type"] == "reveal":
                    for r, c, value in event["data"]:
                        board[r][c] = value
                        revealed[r][c] = True
                    found = event["found_count"]
                # End game
                elif event["type"] == "end":
                    finish_time = event.get("time", None)
                    if finish_time:
                        print(event["result"], "Time:", finish_time)
                    else:
                        print(event["result"], "Time: N/A")
                    running = False
            except asyncio.TimeoutError:
                pass

            # Draw the board
            screen.fill(BG_COLOR)
            for r in range(rows):
                for c in range(cols):
                    rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
                    color = REVEALED_COLOR if revealed[r][c] else HIDDEN_COLOR
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, (50, 50, 50), rect, 1)

                    # Label revealed cells
                    if revealed[r][c]:
                        text = font.render(str(board[r][c]), True, FONT_COLOR)
                        screen.blit(text, (c * cell_size + 10, r * cell_size + 5))

            # Display "found" count
            found_text = font.render(f"Found: {found} / {to_be_found}", True, (255, 255, 255))
            screen.blit(found_text, (10, HEIGHT - 40))

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    asyncio.run(handle_server("ws://localhost:8765/ws/testroom"))
