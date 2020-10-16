# Maven Kim
from random import choice
from math import inf
import sys
directions = [1, -1, 10, -10, 11, -11, 9, -9]  # Represents all traversal directions (up, left, right, down, diagonals)


# Finds the possible moves on a board based on Othello's rules and the argument token (@ or o)
def possible_moves(board, token):
    # Finds the opponent's token
    if token == "@":
        opp_token = "o"
    else:
        opp_token = "@"
    # Finds all the empty spots on the board
    blank_spaces = [square_index for square_index in range(100) if board[square_index] == "."]
    valid_moves = list()
    # Checks every square index for validity
    for square_index in blank_spaces:
        check_index = square_index
        # Checks for validity in all directions
        for direction in directions:
            opp_token_found = False
            # Moves in a particular direction until a token that is not the opponent's token is found
            while board[check_index + direction] == opp_token:
                check_index = check_index+direction
                opp_token_found = True
            # If one of your token's is found at the end, it's a valid spot given that opposing tokens are in between
            if board[check_index + direction] == token and opp_token_found:
                valid_moves.append(square_index)
                break
            check_index = square_index
    return valid_moves


# Places a token at the specified position and flips over all tokens
def move(board, token, position):
    opp_token = ("o" if token == "@" else "@")
    tokens_changed = 0
    # Flips over opposing tokens and adds token to position
    for direction in directions:
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
                tokens_changed += 1
            # Tokens_changed represents the number of turned over tokens, so the initial move doesn't count
            tokens_changed -= 1
            board = ''.join(board)
    return board, tokens_changed


# Displays the board as a 10 by 10 grid
def display(board):
    print(board[0:10] + "\n" + board[10:20] + "\n" + board[20:30] + "\n" + board[30:40] + "\n" + board[40:50] + "\n"
          + board[50:60] + "\n" + board[60:70] + "\n" + board[70:80] + "\n" + board[80:90] + "\n" + board[90:100])


# Each player randomly chooses a spot on the board to play until the end
def random_run():
    board = "???????????........??........??........??...o@...??...@o...??........??........??........???????????"
    white_score = 2
    black_score = 2
    current_player = "@"
    last_move = 0
    double_pass = False
    all_moves = list()
    while not double_pass:
        display(board)
        print("White's Score:", white_score)
        print("Black's Score:", black_score)
        moves = possible_moves(board, current_player)
        print("List of valid moves:", moves)
        # Picks a random move and changes the board or passes if there are no possible moves
        if len(moves) == 0:
            # If the opponent just recently passed, and if the current player has to pass, then the game is over
            if last_move == -1:
                double_pass = True
            last_move = -1
            tokens_changed = 0
        else:
            last_move = choice(moves)
            board, tokens_changed = move(board, current_player, last_move)
        # Changes number of tokens each player has and prints the move of the current player (or pass)
        # Switches the current player to the opposing player
        if current_player == "@":
            if last_move != -1:
                print("Black places a token at index", last_move)
                black_score = black_score + tokens_changed + 1
                white_score = white_score - tokens_changed
            else:
                print("Black passes")
            current_player = "o"
        else:
            if last_move != -1:
                print("White places a token at index", last_move)
                black_score = black_score - tokens_changed
                white_score = white_score + tokens_changed + 1
            else:
                print("White passes")
            current_player = "@"
        all_moves.append(last_move)
        print()
    # Finals stats
    print("White's Final Score:", white_score)
    print("Black's Final Score:", black_score)
    print("Percentage of White Tokens:", white_score/(white_score+black_score))
    print("Percentage of Black Tokens:", black_score/(white_score+black_score))
    print("Every index chosen:")
    print(all_moves)


# Gets a board and token from the command line and attempts to determine the best move for the token
# def best_possible_move():
#     file_directory, board, token = sys.argv
#     moves = possible_moves(board, token)


# Heuristic: chooses move that grants the most tokens
def max_tokens_heuristic(board, token, moves):
    max_tokens_changed = 0
    best_move = -1
    for square in moves:
        new_board, tokens_changed = move(board, token, square)
        if tokens_changed > max_tokens_changed:
            max_tokens_changed = tokens_changed
            best_move = square
    return best_move


# Heuristic: chooses move that grants the least tokens
def min_tokens_heuristic(board, token, moves):
    min_tokens_changed = inf
    best_move = -1
    for square in moves:
        new_board, tokens_changed = move(board, token, square)
        if tokens_changed < min_tokens_changed:
            min_tokens_changed = tokens_changed
            best_move = square
    return best_move


# Heuristic: move that grants the most tokens
# If a corner can be chosen, choose the corner
# If edges can be chosen, picks the edge move that gives the most tokens
def heuristic(board, token, moves):
    max_tokens_changed = 0
    best_move = -1
    new_moves_list = list()
    for square in moves:
        # Corners (highest priority)
        if square == 11 or square == 18 or square == 81 or square == 88:
            best_move = square
            break
        # Edges (secondary priority)
        elif square % 10 == 1 or square % 10 == 8 or square // 10 == 1 or square // 10 == 8:
            new_moves_list.append(square)
        if len(new_moves_list) > 0:
            continue
        # Central squares (lower priority)
        new_board, tokens_changed = move(board, token, square)
        if tokens_changed > max_tokens_changed:
            max_tokens_changed = tokens_changed
            best_move = square
    # If there are edge moves, then get the best one out of them
    if len(new_moves_list) > 0:
        return max_tokens_heuristic(board, token, new_moves_list)
    return best_move


# Black runs heuristic, white runs random
def heuristic_run():
    board = "???????????........??........??........??...o@...??...@o...??........??........??........???????????"
    white_score = 2
    black_score = 2
    current_player = "@"
    last_move = 0
    double_pass = False
    all_moves = list()
    while not double_pass:
        display(board)
        print("White's Score:", white_score)
        print("Black's Score:", black_score)
        moves = possible_moves(board, current_player)
        print("List of valid moves:", moves)
        # Picks a random move and changes the board or passes if there are no possible moves
        if len(moves) == 0:
            # If the opponent just recently passed, and if the current player has to pass, then the game is over
            if last_move == -1:
                double_pass = True
            last_move = -1
            tokens_changed = 0
        else:
            if current_player == "@":
                last_move = min_tokens_heuristic(board, current_player, moves)
            else:
                last_move = choice(moves)
            board, tokens_changed = move(board, current_player, last_move)
        # Changes number of tokens each player has and prints the move of the current player (or pass)
        # Switches the current player to the opposing player
        if current_player == "@":
            if last_move != -1:
                print("Black places a token at index", last_move)
                black_score = black_score + tokens_changed + 1
                white_score = white_score - tokens_changed
            else:
                print("Black passes")
            current_player = "o"
        else:
            if last_move != -1:
                print("White places a token at index", last_move)
                black_score = black_score - tokens_changed
                white_score = white_score + tokens_changed + 1
            else:
                print("White passes")
            current_player = "@"
        all_moves.append(last_move)
        print()
    # Finals stats
    print("White's Final Score:", white_score)
    print("Black's Final Score:", black_score)
    print("Percentage of White Tokens:", white_score/(white_score+black_score))
    print("Percentage of Black Tokens:", black_score/(white_score+black_score))
    print("Every index chosen:")
    print(all_moves)


heuristic_run()
# PROBLEM: PRIORITIZING MOST TOKENS MEANS OPPONENT HAS A HIGHER CHANCE OF GETTING A LOT OF TOKENS WITH A RANDOM MOVE
# SOLUTION: Choose move that overturns least number of tokens
