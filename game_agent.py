"""This file contains all the classes you must complete for this project.

You can use the test cases in agent_test.py to help during development, and
augment the test suite with your own test cases to further test your code.

You must test your agent's strength against a set of agents with known
relative strength using tournament.py and include the results in your report.
"""

import random
import math

class Timeout(Exception):
    """Subclass base exception for code clarity."""
    pass

def lecture_heuristic(own_moves, opp_moves):
    return float(own_moves - opp_moves)

# penalize opp move harder and take into account remaining moves
def lecture_heuristic_improved(own_moves, opp_moves, remaining_moves):
    return (own_moves - 2*opp_moves)/remaining_moves

# only cares about its own survival
# red alert when remaining moves < 3
def survival_heuristic(own_moves, remaining_moves):
    return 3*(own_moves-3)/remaining_moves

# prioritize moves closer to center at the beginning
def positional_heuristic(location, center, remaining_moves):
    distance = abs(location[0]-center[0])+abs(location[1]-center[1])
    return remaining_moves/(distance*5) if distance is not 0 else float("inf")

# too long --> timeout
# check back to see what's wrong
def endgame_heuristic(game, player):
    count = 0
    for m in game.get_legal_moves(player):
        # note: can minus number of opponent moves
        count += game.forecast_move(m).get_legal_moves(player)
    return count

def custom_score(game, player):
    if game.is_loser(player):
        return float("-inf")

    if game.is_winner(player):
        return float("inf")

    own_moves = len(game.get_legal_moves(player))
    opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
    move_count = game.move_count
    remaining_moves = game.width*game.height - game.move_count
    location = game.get_player_location(player)
    center = (game.width//2, game.height//2)

    lecture_score_improved = lecture_heuristic_improved(own_moves, opp_moves, remaining_moves)
    survival_score = survival_heuristic(own_moves, remaining_moves)
    positional_score = positional_heuristic(location, center, remaining_moves)

    return lecture_score_improved + survival_score + positional_score
    

class CustomPlayer:
    """Game-playing agent that chooses a move using your evaluation function
    and a depth-limited minimax algorithm with alpha-beta pruning. You must
    finish and test this player to make sure it properly uses minimax and
    alpha-beta to return a good move before the search time limit expires.

    Parameters
    ----------
    search_depth : int (optional)
        A strictly positive integer (i.e., 1, 2, 3,...) for the number of
        layers in the game tree to explore for fixed-depth search. (i.e., a
        depth of one (1) would only explore the immediate sucessors of the
        current state.)

    score_fn : callable (optional)
        A function to use for heuristic evaluation of game states.

    iterative : boolean (optional)
        Flag indicating whether to perform fixed-depth search (False) or
        iterative deepening search (True).

    method : {'minimax', 'alphabeta'} (optional)
        The name of the search method to use in get_move().

    timeout : float (optional)
        Time remaining (in milliseconds) when search is aborted. Should be a
        positive value large enough to allow the function to return before the
        timer expires.
    """

    def __init__(self, search_depth=3, score_fn=custom_score,
                 iterative=True, method='minimax', timeout=10.):
        self.search_depth = search_depth
        self.iterative = iterative
        self.score = score_fn
        self.method = method
        self.time_left = None
        self.TIMER_THRESHOLD = timeout

    def get_move(self, game, legal_moves, time_left):
        """Search for the best move from the available legal moves and return a
        result before the time limit expires.

        This function must perform iterative deepening if self.iterative=True,
        and it must use the search method (minimax or alphabeta) corresponding
        to the self.method value.

        **********************************************************************
        NOTE: If time_left < 0 when this function returns, the agent will
              forfeit the game due to timeout. You must return _before_ the
              timer reaches 0.
        **********************************************************************

        Parameters
        ----------
        game : `isolation.Board`
            An instance of `isolation.Board` encoding the current state of the
            game (e.g., player locations and blocked cells).

        legal_moves : list<(int, int)>
            A list containing legal moves. Moves are encoded as tuples of pairs
            of ints defining the next (row, col) for the agent to occupy.

        time_left : callable
            A function that returns the number of milliseconds left in the
            current turn. Returning with any less than 0 ms remaining forfeits
            the game.

        Returns
        -------
        (int, int)
            Board coordinates corresponding to a legal move; may return
            (-1, -1) if there are no available legal moves.
        """

        self.time_left = time_left

        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()

        if not legal_moves:
            return (-1,-1)

        if game.move_count == 1:
            return math.floor(game.height / 2), math.floor(game.width / 2)

        best_move = legal_moves[random.randint(0, len(legal_moves) - 1)]
        best_score = float("-inf")

        # Perform any required initializations, including selecting an initial
        # move from the game board (i.e., an opening book), or returning
        # immediately if there are no legal moves

        try:
            # The search method call (alpha beta or minimax) should happen in
            # here in order to avoid timeout. The try/except block will
            # automatically catch the exception raised by the search method
            # when the timer gets close to expiring

            if self.method == "minimax":
                search_method = self.minimax
            else:
                search_method = self.alphabeta

            depth = 1
            while (True):
                if self.time_left() < self.TIMER_THRESHOLD:
                    raise Timeout()
                score, move = search_method(game, depth)
                if score > best_score:
                    best_score = score
                    best_move = move
                if not self.iterative:
                    return best_move
                depth += 1
                # if self.search_depth != -1 and depth > self.search_depth:
                #     break

        except Timeout:
            # Handle any actions required at timeout, if necessary
            return best_move

        # Return the best move from the last completed search iteration
        return best_move

    # The overall purpose of alphabeta pruning is: 
    # - For MAX player to gradually find the move that yields highest utility (best choice by MAX player definition)
    #   starting from the theoretical worst utility (minus infinity).
    # - For MIN player to gradually find the move that yields lowest utility (best choice by MIN player definition)
    #   starting from the theoretical worst utility (plus infinity).
    # - Therefore, in MAX player's turn, prune branches that can yield a worse (means higher) utility than current best choice 
    #   (lowest so far) for MIN player since they will be ignored by the predecessor MIN player anyway.
    def max_value(self, game, depth, toPrune=False, alpha=float("-inf"), beta=float("inf")):
        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()
        if depth==0 or not game.get_legal_moves():  # Terminal state --> return utility
            return self.score(game, self),(-1,-1)

        best_move = (-1,-1)
        v = float("-inf")

        if not toPrune: # Just recursively go deeper with no worry about pruning
            for move in game.get_legal_moves():
                if self.time_left() < self.TIMER_THRESHOLD:
                    raise Timeout()
                v,best_move = max((v,best_move), (self.min_value(game.forecast_move(move), depth-1)[0],move))
            return v,best_move

        for move in game.get_legal_moves():
            if self.time_left() < self.TIMER_THRESHOLD:
                raise Timeout()
            v,best_move = max((v,best_move), (self.min_value(game.forecast_move(move), depth-1, True, alpha, beta)[0],move))
            if v >= beta:
                return v,best_move
            alpha = max(alpha, v)
        return v,best_move

    # The overall purpose of alphabeta pruning is: 
    # - For MAX player to gradually find the move that yields highest utility (best choice by MAX player definition)
    #   starting from the theoretical worst utility (minus infinity).
    # - For MIN player to gradually find the move that yields lowest utility (best choice by MIN player definition)
    #   starting from the theoretical worst utility (plus infinity).
    # - Therefore, in MIN player's turn, prune branches that can yield a worse (means lower) utility than current best choice 
    #   (highest so far) for MAX player since they will be ignored by the predecessor MAX player anyway.
    def min_value(self, game, depth, toPrune=False, alpha=float("-inf"), beta=float("inf")):
        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()
        if depth==0 or not game.get_legal_moves():  # Terminal state --> return utility
            return self.score(game, self),(-1,-1)

        best_move = (-1,-1)
        v = float("inf")

        if not toPrune: # Just recursively go deeper with no worry about pruning
            for move in game.get_legal_moves():
                if self.time_left() < self.TIMER_THRESHOLD:
                    raise Timeout()
                v,best_move = min((v,best_move), (self.max_value(game.forecast_move(move), depth-1)[0],move))
            return v,best_move

        for move in game.get_legal_moves():
            if self.time_left() < self.TIMER_THRESHOLD:
                raise Timeout()
            v,best_move = min((v,best_move), (self.max_value(game.forecast_move(move), depth-1, True, alpha, beta)[0],move))
            if v <= alpha:
                return v,best_move
            beta = min(beta, v)
        return v,best_move

    def minimax(self, game, depth, maximizing_player=True):
        """Implement the minimax search algorithm as described in the lectures.

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        maximizing_player : bool
            Flag indicating whether the current search depth corresponds to a
            maximizing layer (True) or a minimizing layer (False)

        Returns
        -------
        float
            The score for the current search branch

        tuple(int, int)
            The best move for the current branch; (-1, -1) for no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project unit tests; you cannot call any other
                evaluation function directly.
        """
        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()

        if maximizing_player:
            return self.max_value(game, depth)
        else:
            return self.min_value(game, depth)

    def alphabeta(self, game, depth, alpha=float("-inf"), beta=float("inf"), maximizing_player=True):
        """Implement minimax search with alpha-beta pruning as described in the
        lectures.

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        alpha : float
            Alpha limits the lower bound of search on minimizing layers

        beta : float
            Beta limits the upper bound of search on maximizing layers

        maximizing_player : bool
            Flag indicating whether the current search depth corresponds to a
            maximizing layer (True) or a minimizing layer (False)

        Returns
        -------
        float
            The score for the current search branch

        tuple(int, int)
            The best move for the current branch; (-1, -1) for no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project unit tests; you cannot call any other
                evaluation function directly.
        """
        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()

        if maximizing_player:
            return self.max_value(game, depth, True, alpha, beta)
        else:
            return self.min_value(game, depth, True, alpha, beta)
