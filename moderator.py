import random
import math
import sys


class Strategy:
    immortals = set()
    directions = [1, -1, 10, -10, 11, -11, 9, -9]
    corners = {11, 18, 81, 88}
    near_corners = {12, 17, 21, 22, 27, 28, 71, 72, 77, 78, 82, 87}
    edges = {12, 13, 14, 15, 16, 17, 21, 28, 31, 38, 41, 48, 51, 58, 61, 68, 71, 78, 82, 83, 84, 85, 86, 87}

    # Finds the possible moves on a board based on Othello's rules and the argument token (@ or o)
    @staticmethod
    def legal_moves(board, token):
        # Finds the opponent's token
        opp_token = {'o': '@', '@': 'o'}[token]
        # Finds all the empty spots on the board
        blank_spaces = [square_index for square_index in range(100) if board[square_index] == "."]
        valid_moves = list()
        # Checks every square index for validity
        for square_index in blank_spaces:
            check_index = square_index
            # Checks for validity in all directions
            for direction in Strategy.directions:
                opp_token_found = False
                # Moves in a particular direction until a token that is not the opponent's token is found
                while board[check_index + direction] == opp_token:
                    check_index = check_index + direction
                    opp_token_found = True
                # If one of your token's is found at end, it's a valid spot given that opposing tokens are in between
                if board[check_index + direction] == token and opp_token_found:
                    valid_moves.append(square_index)
                    break
                check_index = square_index
        return valid_moves

    # Places a token at the specified position and flips over all tokens
    @staticmethod
    def make_move(board, token, position):
        opp_token = ("o" if token == "@" else "@")
        # Flips over opposing tokens and adds token to position
        for direction in Strategy.directions:
            check_index = position
            opposite_token_found = False
            # Checks to see whether opposing tokens in a certain direction can be flipped over
            while board[check_index + direction] == opp_token:
                check_index = check_index + direction
                opposite_token_found = True
            if board[check_index + direction] == token and opposite_token_found:
                # Flips over tokens in the direction
                board = list(board)
                for square_index in range(position, check_index + direction, direction):
                    board[square_index] = token
                board = ''.join(board)
        return board

    # Finds the next player (checks to see if input player can move and if opponent can move)
    def get_next_player(self, board, player):
        if len(self.legal_moves(board, player)) != 0:
            return player
        opponent = {'o': '@', '@': 'o'}[player]
        if len(self.legal_moves(board, opponent)) != 0:
            return opponent
        return None

    # Scores a board state; higher number means better for black, lower means better for white
    def score_board(self, board):
        # Mobility (number of moves each player can make)
        black_mobility = len(self.legal_moves(board, "@"))
        white_mobility = len(self.legal_moves(board, 'o'))
        # If the game is over (prioritize winning)
        if black_mobility == white_mobility == 0:
            black_count = board.count('@')
            white_count = board.count('o')
            # If black wins
            if black_count > white_count:
                score = 10000 + black_count - white_count
            # If white wins
            elif white_count > black_count:
                score = -10000 + black_count - white_count
            # If tie
            else:
                score = 0
        # Otherwise, score based on mobility
        else:
            # Weighted board score
            board_score = 0
            # Difference between black and white tokens
            white_count = board.count('o')
            black_count = board.count('@')
            change = -math.inf
            visited = set()
            # Need this loop to ensure that all immortal squares are found
            while change != 0:
                change = 0
                for square_index in range(100):
                    if square_index not in visited:
                        square = board[square_index]
                        if square == "@" or square == "o":
                            multiplier = {"@": 1, "o": -1}[square]
                            # Prioritize corners the most
                            if square_index in Strategy.corners:
                                board_score += 1000*multiplier
                                Strategy.immortals.add(square_index)
                                visited.add(square_index)
                                change += 1
                            else:
                                immortal_surrounding = 0
                                for direction in Strategy.directions:
                                    new_square_index = square_index + direction
                                    if new_square_index in Strategy.immortals and board[new_square_index] == square:
                                        # Prioritize edges that can't be taken back
                                        if square_index in Strategy.edges:
                                            Strategy.immortals.add(square_index)
                                            board_score += 100*multiplier
                                            visited.add(square_index)
                                            change += 1
                                            break
                                        immortal_surrounding += 1
                                # Pieces surrounded by 4 immortal pieces are immortal (includes "out of board" pieces)
                                if immortal_surrounding >= 4:
                                    Strategy.immortals.add(square_index)
                                    visited.add(square_index)
                                    board_score += 25*multiplier
                                    change += 1
            # Heavily prioritize limiting opponent's mobility
            if black_mobility == 0:
                board_score -= 1000
            elif white_mobility == 0:
                board_score += 1000
            # Value mobility less in late game, value count less in early game
            # Q2: During the early game, my code emphasizes mobility and de-emphasizes count. When the game is halfway
            # through, or when there are 32 total tokens on the board, the code switches to slightly
            # prioritizing count, and when there are more than 60 tokens on the board, the algorithm switches
            # to prioritizing count instead of mobility.
            if black_count + white_count > 60:
                score = (black_count - white_count) * .1 + board_score
            elif black_count + white_count > 32:
                score = (black_mobility - white_mobility) * .5 + (black_count - white_count) * 0.1 + board_score
            else:
                score = (black_mobility - white_mobility) * .5 + (black_count - white_count) * -0.1 + board_score
        return score

    # Minimax algorithm (black is trying to maximize, white is trying to minimize)
    def minimax(self, board, player, depth, alpha, beta):
        opponent = {'o': '@', '@': 'o'}[player]
        best = {'o': min, '@': max}
        if depth == 0:
            score = self.score_board(board)
            return None, score
        possibles = []
        for move in self.legal_moves(board, player):
            new_board = self.make_move(board, player, move)
            next_player = self.get_next_player(new_board, opponent)
            # If the game is over
            if next_player is None:
                score = self.score_board(new_board)
                possibles.append((move, score))
            # If the game can continue
            else:
                possibles.append((move, self.minimax(new_board, next_player, depth-1, alpha, beta)[1]))
            best_possible = best[player](possibles, key=lambda x: x[1])
            # Q1: My implementation constantly looks at the best possible move for either black or white
            # given the current board state, and updates beta or alpha appropriately. If alpha is greater than beta,
            # then the code doesn't look at future board states of the branch being examined by minimax.
            if player == 'o':
                beta = min(beta, best_possible[1])
            else:
                alpha = max(alpha, best_possible[1])
            if alpha >= beta:
                break
        return best[player](possibles, key=lambda x: x[1])

    # Main method (run by server)
    def best_strategy(self, board, player):
        # First value is random at first
        print(random.choice(self.legal_moves(board, player)))
        depth = 1
        # Iterative deepening with minimax; chooses best moves with increasing depth until cut off
        while True:
            print(self.minimax(board, player, depth, -math.inf, math.inf)[0])
            depth += 1


input_board = sys.argv[1]
input_token = sys.argv[2]
othello = Strategy()
othello.best_strategy(input_board, input_token)
