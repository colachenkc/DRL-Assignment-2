# Remember to adjust your student ID in meta.xml
import numpy as np
import pickle
import random
import gym
from gym import spaces
import matplotlib.pyplot as plt
import copy
import random
import math


class Game2048Env(gym.Env):
    def __init__(self):
        super(Game2048Env, self).__init__()

        self.size = 4  # 4x4 2048 board
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.score = 0

        # Action space: 0: up, 1: down, 2: left, 3: right
        self.action_space = spaces.Discrete(4)
        self.actions = ["up", "down", "left", "right"]

        self.last_move_valid = True  # Record if the last move was valid

        self.reset()

    def reset(self):
        """Reset the environment"""
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.score = 0
        self.add_random_tile()
        self.add_random_tile()
        return self.board

    def add_random_tile(self):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = list(zip(*np.where(self.board == 0)))
        if empty_cells:
            x, y = random.choice(empty_cells)
            self.board[x, y] = 2 if random.random() < 0.9 else 4

    def compress(self, row):
        """Compress the row: move non-zero values to the left"""
        new_row = row[row != 0]  # Remove zeros
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')  # Pad with zeros on the right
        return new_row

    def merge(self, row):
        """Merge adjacent equal numbers in the row"""
        for i in range(len(row) - 1):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                row[i + 1] = 0
                self.score += row[i]
        return row

    def move_left(self):
        """Move the board left"""
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            new_row = self.compress(self.board[i])
            new_row = self.merge(new_row)
            new_row = self.compress(new_row)
            self.board[i] = new_row
            if not np.array_equal(original_row, self.board[i]):
                moved = True
        return moved

    def move_right(self):
        """Move the board right"""
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            # Reverse the row, compress, merge, compress, then reverse back
            reversed_row = self.board[i][::-1]
            reversed_row = self.compress(reversed_row)
            reversed_row = self.merge(reversed_row)
            reversed_row = self.compress(reversed_row)
            self.board[i] = reversed_row[::-1]
            if not np.array_equal(original_row, self.board[i]):
                moved = True
        return moved

    def move_up(self):
        """Move the board up"""
        moved = False
        for j in range(self.size):
            original_col = self.board[:, j].copy()
            col = self.compress(self.board[:, j])
            col = self.merge(col)
            col = self.compress(col)
            self.board[:, j] = col
            if not np.array_equal(original_col, self.board[:, j]):
                moved = True
        return moved

    def move_down(self):
        """Move the board down"""
        moved = False
        for j in range(self.size):
            original_col = self.board[:, j].copy()
            # Reverse the column, compress, merge, compress, then reverse back
            reversed_col = self.board[:, j][::-1]
            reversed_col = self.compress(reversed_col)
            reversed_col = self.merge(reversed_col)
            reversed_col = self.compress(reversed_col)
            self.board[:, j] = reversed_col[::-1]
            if not np.array_equal(original_col, self.board[:, j]):
                moved = True
        return moved

    def is_game_over(self):
        """Check if there are no legal moves left"""
        # If there is any empty cell, the game is not over
        if np.any(self.board == 0):
            return False

        # Check horizontally
        for i in range(self.size):
            for j in range(self.size - 1):
                if self.board[i, j] == self.board[i, j+1]:
                    return False

        # Check vertically
        for j in range(self.size):
            for i in range(self.size - 1):
                if self.board[i, j] == self.board[i+1, j]:
                    return False

        return True

    def step(self, action):
        """Execute one action"""
        assert self.action_space.contains(action), "Invalid action"

        if action == 0:
            moved = self.move_up()
        elif action == 1:
            moved = self.move_down()
        elif action == 2:
            moved = self.move_left()
        elif action == 3:
            moved = self.move_right()
        else:
            moved = False

        self.last_move_valid = moved  # Record if the move was valid

        if moved:
            self.add_random_tile()

        done = self.is_game_over()

        return self.board, self.score, done, {}

    def render(self, mode="human", action=None):
        """
        Render the current board using Matplotlib.
        This function does not check if the action is valid and only displays the current board state.
        """
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(-0.5, self.size - 0.5)
        ax.set_ylim(-0.5, self.size - 0.5)

        for i in range(self.size):
            for j in range(self.size):
                value = self.board[i, j]
                color = COLOR_MAP.get(value, "#3c3a32")  # Default dark color
                text_color = TEXT_COLOR.get(value, "white")
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=color, edgecolor="black")
                ax.add_patch(rect)

                if value != 0:
                    ax.text(j, i, str(value), ha='center', va='center',
                            fontsize=16, fontweight='bold', color=text_color)
        title = f"score: {self.score}"
        if action is not None:
            title += f" | action: {self.actions[action]}"
        plt.title(title)
        plt.gca().invert_yaxis()
        plt.show()

    def simulate_row_move(self, row):
        """Simulate a left move for a single row"""
        # Compress: move non-zero numbers to the left
        new_row = row[row != 0]
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')
        # Merge: merge adjacent equal numbers (do not update score)
        for i in range(len(new_row) - 1):
            if new_row[i] == new_row[i + 1] and new_row[i] != 0:
                new_row[i] *= 2
                new_row[i + 1] = 0
        # Compress again
        new_row = new_row[new_row != 0]
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')
        return new_row

    def is_move_legal(self, action):
        """Check if the specified move is legal (i.e., changes the board)"""
        # Create a copy of the current board state
        temp_board = self.board.copy()

        if action == 0:  # Move up
            for j in range(self.size):
                col = temp_board[:, j]
                new_col = self.simulate_row_move(col)
                temp_board[:, j] = new_col
        elif action == 1:  # Move down
            for j in range(self.size):
                # Reverse the column, simulate, then reverse back
                col = temp_board[:, j][::-1]
                new_col = self.simulate_row_move(col)
                temp_board[:, j] = new_col[::-1]
        elif action == 2:  # Move left
            for i in range(self.size):
                row = temp_board[i]
                temp_board[i] = self.simulate_row_move(row)
        elif action == 3:  # Move right
            for i in range(self.size):
                row = temp_board[i][::-1]
                new_row = self.simulate_row_move(row)
                temp_board[i] = new_row[::-1]
        else:
            raise ValueError("Invalid action")

        # If the simulated board is different from the current board, the move is legal
        return not np.array_equal(self.board, temp_board)

class Node:
    def __init__(self, state, parent=None, action=None):
        self.state = state  # Tuple (board, score)
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.total_reward = 0

    def is_fully_expanded(self, env):
        return len(self.children) == len([a for a in range(4) if env.is_move_legal(a)])

    def best_child(self, c_param=1.4):
        choices_weights = [
            (child.total_reward / child.visits) + c_param * math.sqrt(math.log(self.visits) / child.visits)
            for child in self.children
        ]
        return self.children[np.argmax(choices_weights)]

# SIMULATION (IMPROVED HEURISTIC POLICY)
def evaluate_board(board, score):
    empty_tiles = np.sum(board == 0)
    max_tile = np.max(board)
    corner_bonus = 0

    # Encourage max tile in corner
    if max_tile in [board[0, 0], board[0, -1], board[-1, 0], board[-1, -1]]:
        corner_bonus = max_tile * 0.1

    # Simple monotonicity score (row/col smoothness)
    mono_score = 0
    for row in board:
        mono_score += np.sum(np.diff(row) <= 0) + np.sum(np.diff(row[::-1]) <= 0)
    for col in board.T:
        mono_score += np.sum(np.diff(col) <= 0) + np.sum(np.diff(col[::-1]) <= 0)

    return score + 0.1 * empty_tiles + corner_bonus + 0.2 * mono_score
def get_action(state, score, simulations=10):
    env = Game2048Env()
    env.board = state.copy()
    env.score = score

    root = Node((env.board.copy(), env.score))

    for _ in range(simulations):
        node = root
        env_sim = copy.deepcopy(env)

        # SELECTION
        while node.children and node.is_fully_expanded(env_sim):
            node = node.best_child()
            _, _, done, _ = env_sim.step(node.action)
            if done:
                break

        # EXPANSION
        if not env_sim.is_game_over():
            legal_actions = [a for a in range(4) if env_sim.is_move_legal(a)]
            tried_actions = [child.action for child in node.children]
            untried = [a for a in legal_actions if a not in tried_actions]

            if untried:
                action = random.choice(untried)
                _, reward, done, _ = env_sim.step(action)
                new_node = Node((env_sim.board.copy(), env_sim.score), parent=node, action=action)
                node.children.append(new_node)
                node = new_node

        # SIMULATION
        # total_reward = env_sim.score
        # while not env_sim.is_game_over():
        #     legal = [a for a in range(4) if env_sim.is_move_legal(a)]
        #     if not legal:
        #         break
        #     a = random.choice(legal)
        #     _, r, done, _ = env_sim.step(a)
        #     total_reward = r
        #     if done:
        #         break
        # SIMULATION (HEURISTIC POLICY)
        # total_reward = env_sim.score
        # while not env_sim.is_game_over():
        #     legal = [a for a in range(4) if env_sim.is_move_legal(a)]
        #     if not legal:
        #         break

        #     # Heuristic: evaluate each legal move
        #     move_scores = []
        #     for a in legal:
        #         # Backup state
        #         old_board = env_sim.board.copy()
        #         old_score = env_sim.score

        #         _, temp_score, _, _ = env_sim.step(a)
        #         empty_tiles = np.sum(env_sim.board == 0)
        #         gain = temp_score - old_score
        #         heuristic_score = gain + 0.1 * empty_tiles
        #         move_scores.append((heuristic_score, a))

        #         # Restore state
        #         env_sim.board = old_board
        #         env_sim.score = old_score


        #     # Choose best move by heuristic
        #     _, best_action = max(move_scores, key=lambda x: x[0])
        #     _, r, done, _ = env_sim.step(best_action)
        #     total_reward = r
        #     if done:
        #         break
        total_reward = env_sim.score
        while not env_sim.is_game_over():
            legal = [a for a in range(4) if env_sim.is_move_legal(a)]
            if not legal:
                break

            # Heuristic: evaluate each legal move
            move_scores = []
            for a in legal:
                old_board = env_sim.board.copy()
                old_score = env_sim.score

                _, temp_score, _, _ = env_sim.step(a)
                h_score = evaluate_board(env_sim.board, temp_score)
                move_scores.append((h_score, a))

                env_sim.board = old_board
                env_sim.score = old_score

            _, best_action = max(move_scores, key=lambda x: x[0])
            _, r, done, _ = env_sim.step(best_action)
            total_reward = r
            if done:
                break
        # BACKPROPAGATION
        while node is not None:
            node.visits += 1
            node.total_reward += total_reward
            node = node.parent

    # Choose the action with the most visits
    best_move = max(root.children, key=lambda child: child.visits).action
    return best_move
