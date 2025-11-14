import random, time

class GameState:
    def __init__(self, width, height, mines, players, seed=None):
        self.width = width
        self.height = height
        self.mines = mines
        self.board = self.generate_board(width, height, mines, seed)

        self.revealed = [set() for _ in range(players)]
        self.start_time = time.time()


    @staticmethod
    def generate_board(width, height, mines, seed=None):
        if seed is not None:
            random.seed(seed)
        cells = [[0 for _ in range(width)] for _ in range(height)]
        mine_positions = random.sample(range(width * height), mines)
        for pos in mine_positions:
            x, y = pos % width, pos // width
            cells[y][x] = -1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and cells[ny][nx] != -1:
                        cells[ny][nx] += 1
        return cells

    def reveal_from_square(self, r, c):
        """Return list of revealed squares starting from (r, c).

        Each entry is [row, col, value]. Uses an explicit visited set and
        correct row/col indexing to avoid infinite loops and index errors.
        """
        board = self.board

        if not board:
            return []

        height = len(board)
        width = len(board[0])
        revealed = []
        visited = set()
        stack = [(r, c)]

        while stack:
            row, col = stack.pop()
            if (row, col) in visited:
                continue

            # guard against out-of-bounds coords
            if not (0 <= row < height and 0 <= col < width):
                continue

            visited.add((row, col))
            value = board[row][col]
            revealed.append([row, col, value])

            # only expand neighbours for zero-value squares
            if value == 0:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        nr, nc = row + dy, col + dx
                        if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in visited:
                            stack.append((nr, nc))
        print(len(revealed))
        return revealed
