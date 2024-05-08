from _client_network import Network
import pygame as pg
import _thread


COLOURS = {0: "White", 1: "Black"}
IMAGE_DIR = "pieces/"
n = Network()


def trans_not(sqr):
    """translates alphanumeric notation to x, y and viceversa"""
    ltrs = ["a", "b", "c", "d", "e", "f", "g", "h"]
    if type(sqr) == str:
        return ltrs.index(sqr[0].lower()), int(sqr[1]) - 1
    elif type(sqr) in (list, tuple):
        return ltrs[sqr[0]] + str(sqr[1] + 1)


def vec_add(*addends):
    """adds vectors"""
    vec = (0, 0)
    for addend in addends:
        vec = (vec[0] + addend[0], vec[1] + addend[1])
    return vec


def vec_mult(vec, mult):
    """multiplies vectors"""
    return (vec[0] * mult, vec[1] * mult)


class Board:
    def __init__(self, fen, player, board_size, n):
        """create board object"""
        self.n = n
        self.width = board_size[0]
        self.height = board_size[1]
        self.player = player
        self.update(fen)

        self.screen = pg.display.set_mode((self.width, self.height), pg.RESIZABLE)
        pg.display.set_caption(f"PyChess: You are {COLOURS[player]}!")

    def display(self):
        """displays the board"""
        background = pg.Rect((0, 0), (self.width, self.height))
        pg.draw.rect(self.screen, (0, 0, 0), background)

        limit = self.height if self.width > self.height else self.width
        sqrsz = int(limit / 8)
        self.sqrs = []

        for x in range(8):

            blitX = (self.width - limit) / 2 + x * sqrsz

            for y in range(8):
                
                blitY = (self.height - limit) / 2 + y * sqrsz
                sqr = pg.Rect((blitX, blitY), (sqrsz, sqrsz))
                colour = [0, 0, 0] if (x + y) % 2 == 0 else [150, 150, 150]
                
                if self.selected:
                    if (x, y) in [
                        move.shift[self.selected] for move in self.selected.moves()
                    ]:
                        colour[1] += 100

                if (x, y) in self.highlighted:
                    colour[2] += 100

                pg.draw.rect(self.screen, colour, sqr)
                piece = self._find_piece((x, y))

                if piece:
                    img = pg.image.load(IMAGE_DIR + f"{piece.colour}/{piece.type}.png")
                    img = pg.transform.scale(img, (sqrsz, sqrsz))
                    self.screen.blit(img, (blitX, blitY))

                self.sqrs.append((sqr, (x, y)))

    def _find_piece(self, pos):
        """finds pieces on the board"""
        for piece in self.pieces:
            if piece.pos == pos:
                return piece

    def click(self, event):
        """detects clicks on the board"""

        clickPos = pg.mouse.get_pos()

        for sqr in self.sqrs:
            if pg.Rect.collidepoint(sqr[0], clickPos):
                if event.button == 1:
                    self.highlighted = []
                    piece = self._find_piece(sqr[1])

                    if self.selected:
                        legal = False
                        for move in self.selected.moves():
                            if sqr[1] == move.shift[self.selected]:
                                move.execute()
                                legal = True
                                self.selected = None
                                n.send(self.to_fen())
                                break
                        if not legal:
                            if piece:
                                if self.turn == piece.colour:
                                    self.selected = piece
                                else:
                                    self.selected = None
                            else:
                                self.selected = None

                    elif piece:
                        if self.turn == piece.colour and self.turn == self.player:
                            self.selected = piece
                        else:
                            self.selected = None

                    else:
                        self.selected = None

                elif event.button == 3:
                    if sqr[1] in self.highlighted:
                        self.highlighted.remove(sqr[1])
                    else:
                        self.highlighted.append(sqr[1])
                break

    def to_fen(self):
        """converts the board back into a fen form"""
        board = []
        for y in range(8):
            line = []
            gap = 0
            for x in range(8):
                piece = self._find_piece((x, y))
                if piece:
                    if gap != 0:
                        line.append(str(gap))
                        gap = 0
                    if piece.colour == 0:
                        symbol = piece.type.upper()
                    else:
                        symbol = piece.type
                    line.append(symbol)
                else:
                    gap += 1
            if gap != 0:
                line.append(str(gap))
            board.append("".join(line))
        board = "/".join(board)

        castling = ""
        if self.castling[0]["k"]:
            castling += "K"
        if self.castling[0]["q"]:
            castling += "Q"
        if self.castling[1]["k"]:
            castling += "k"
        if self.castling[1]["q"]:
            castling += "q"
        if castling == "":
            castling = "-"

        turn = "w" if self.turn == 0 else "b"

        return f"{board} {turn} {castling} - \
{self.move_count} {int(self.move_count/2) + 1}"

    def update(self, fen):
        """converts fen to 2d list"""
        self.highlighted = []
        self.selected = None
        fen = fen.split(" ")
        self.pieces = []
        x, y = 0, 0
        for char in fen[0]:
            if char == "/":
                y += 1
                x = 0
            else:
                try:
                    x += int(char)
                except:
                    self.pieces.append(Piece(char, (x, y), self))
                    x += 1
        self.turn = 0 if fen[1] == "w" else 1
        self.castling = {
            0: {"k": "K" in fen[2], "q": "Q" in fen[2]},
            1: {"k": "k" in fen[2], "q": "q" in fen[2]},
        }
        self.en_passant = None if fen[3] == "-" else trans_not(fen[3])
        self.move_count = int(fen[4])

    def run(self):
        """runs the game"""
        _thread.start_new_thread(self.listen, ())
        self.run = True
        while self.run:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.run = False
                elif event.type == pg.VIDEORESIZE:
                    self.width, self.height = event.size
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.click(event)
            self.display()
            pg.display.update()
        pg.quit()
        print('game over')

    def listen(self):
        """listens for updates from the server"""
        while True:
            data = n.recv()
            if data == "game over":
                self.run = False
            elif data != self.to_fen():
                self.update(data)


class Piece:
    def __init__(self, piece, pos, board):
        """creates piece object"""
        self.type = piece.lower()
        self.colour = 1 if piece.islower() else 0
        self.pos = pos
        self.board = board

    def moves(self):
        """creates list of possible moves"""
        moves = []

        if self.type == "p":
            vec = {0: -1, 1: 1}
            rank = {0: 6, 1: 1}
            for i in (1, 2):
                move = Move(self)
                move.shift[self] = vec_add(self.pos, vec_mult((0, i), vec[self.colour]))
                if not self.board._find_piece(move.shift[self]) and (
                    i != 2 or (i == 2 and self.pos[1] == rank[self.colour])
                ):
                    moves.append(move)
                else:
                    break

            sides = [1, -1]
            for side in sides:
                shift = vec_add(self.pos, (side, 0), (0, vec[self.colour]))
                move = Move(self)
                move.shift[self] = shift

                piece = self.board._find_piece(shift)
                if piece:
                    if piece.colour != self.colour:
                        move.take.append(piece)
                        moves.append(move)


        elif self.type == "n":
            for vec in (
                (1, 2),
                (-1, 2),
                (1, -2),
                (-1, -2),
                (2, 1),
                (2, -1),
                (-2, 1),
                (-2, -1),
            ):
                move = Move(self)
                move.shift[self] = vec_add(self.pos, vec)
                piece = self.board._find_piece(move.shift[self])
                if piece:
                    if piece.colour != self.colour:
                        move.take.append(piece)
                        moves.append(move)
                else:
                    moves.append(move)


        elif self.type == "b":
            for vec in ((-1, 1), (-1, -1), (1, -1), (1, 1)):
                for i in range(1, 8):
                    move = Move(self)
                    move.shift[self] = vec_add(vec_mult(vec, i), self.pos)
                    piece = self.board._find_piece(move.shift[self])
                    if piece:
                        if piece.colour != self.colour:
                            move.take.append(piece)
                            moves.append(move)
                        break
                    else:
                        moves.append(move)


        elif self.type == "r":
            for vec in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                for i in range(1, 8):
                    move = Move(self)
                    move.shift[self] = vec_add(vec_mult(vec, i), self.pos)
                    piece = self.board._find_piece(move.shift[self])
                    if piece:
                        if piece.colour != self.colour:
                            move.take.append(piece)
                            moves.append(move)
                        break
                    else:
                        moves.append(move)


        elif self.type == "q":
            for vec in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, 1),
                (-1, -1),
                (1, -1),
                (1, 1),
            ):
                for i in range(1, 8):
                    move = Move(self)
                    move.shift[self] = vec_add(vec_mult(vec, i), self.pos)
                    piece = self.board._find_piece(move.shift[self])
                    if piece:
                        if piece.colour != self.colour:
                            move.take.append(piece)
                            moves.append(move)
                        break
                    else:
                        moves.append(move)


        elif self.type == "k":
            for vec in (
                (-1, 1),
                (-1, -1),
                (1, -1),
                (1, 1),
                (0, 1),
                (0, -1),
                (1, 0),
                (-1, 0),
            ):
                move = Move(self)
                move.shift[self] = vec_add(vec, self.pos)
                piece = self.board._find_piece(move.shift[self])
                if piece:
                    if piece.colour != self.colour:
                        move.take.append(piece)
                        moves.append(move)
                else:
                    moves.append(move)

        return [
            move
            for move in moves
            if [
                shift
                for shift in move.shift
                if move.shift[shift][0] in range(8) and move.shift[shift][1] in range(8)
            ]
        ]


class Move:
    def __init__(self, piece):
        """creates move object"""
        self.piece = piece
        self.shift = {}
        self.take = []

    def execute(self):
        """executes the move of the piece and passes on the turn"""

        for piece in self.shift:
            piece.pos = self.shift[piece]

        for piece in self.take:
            self.piece.board.pieces.remove(piece)

        self.piece.board.turn = 0 if self.piece.board.turn == 1 else 1


# python3 client.py

# gets username and password and sends to the server
username = ''
while username == '':
    username = str(input("Enter your username: "))
    print(30*'\n')

n.send(username)
joinInfo = n.recv()
player = joinInfo["colour"]
fen = joinInfo["fen"]
print(player, fen)
width, height = 500, 500
board = Board(fen, player, (height, width), n)
board.run()
