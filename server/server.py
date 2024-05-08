import _thread
from _server_network import Network

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
waiting = []
games = {}
n = Network()
print("listening...")


def player(conn, colour, game):
    """new thread for each player within a game"""
    n.send(conn[0], {"gameNum": game.ID, "colour": colour, "fen": game.fen})
    while True:
        data = n.recv(conn[0])
        if data == "disconnected":
            game.update("game over")
            break
        else:
            print(f"On board {game.ID} {conn[1]} played " + data)
            game.update(data)
    print("Lost connection")
    conn[0].close()


class Game:
    def __init__(self, players, fen, ID):
        """creates game object"""
        self.ID = ID
        self.players = players
        self.fen = fen

    def update(self, data):
        """sends an update of the board to both players"""
        try:
            if "k" not in data.split(" ")[0] or "K" not in data.split(" ")[0]:
                data = "game over"
            for player1 in self.players:
                n.send(self.players[player1][0], data)
        except:
            pass


def game(players, fen, gameID):
    """new thread for each game"""
    print("new game created")
    games[gameID] = Game(players, fen, gameID)
    for player1 in players:
        _thread.start_new_thread(
            player,
            (
                players[player1],
                player1,
                games[gameID],
            ),
        )


def user(conn):
    """lobby area waiting for players"""
    username = n.recv(conn)
    if not waiting:
        waiting.append((conn, username))
    else:
        _thread.start_new_thread(
            game,
            (
                {0: (conn, username), 1: waiting.pop(0)},
                fen,
                len(games),
            ),
        )


# loop to waiting for new players to join
while True:
    conn, addr = n.acpt()
    print("Connected to:", addr)
    _thread.start_new_thread(user, (conn,))
