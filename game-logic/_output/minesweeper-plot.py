from random import randint
import numpy as np
from collections import defaultdict 
import constraint
import matplotlib.pyplot as plt

def surrounding_cells(x, y, rows, cols):
  cells = []
  for i in range(max(x-1, 0), min(x+2, rows)):
    for j in range(max(y-1, 0), min(y+2, cols)):
      if i==x and j==y:
        continue
      cells.append([i, j])
  return cells

def create_board(rows, cols, n):
  board = [[0]*cols for _ in range(rows)]
  mines = []
  while len(mines) != n:
    new_mine = (randint(0, rows-1), randint(0, cols-1))
    if new_mine not in mines:
      mines.append(new_mine)
      x = new_mine[0]
      y = new_mine[1]
      board[x][y] = 9
      for i, j in surrounding_cells(x, y, rows, cols):
        board[i][j] += 1
  return board, mines

def display_state(state):
  rows, cols = len(state[0]), len(state[0][0])
  rows_spacing, cols_spacing = len(str(rows)) + 1, len(str(cols)) + 1
  print('{:>{rs}}'.format(' ', rs=rows_spacing), end='')
  for i in range(cols):
    print('{:>{cs}}'.format(i, cs=cols_spacing), end='')
  print('')
  for i in range(rows):
    print('{:>{rs}}'.format(i, rs=rows_spacing), end='')
    for j in range(cols):
      print('{:>{cs}}'.format(state[0][i][j], cs = cols_spacing), end='')
    print('')

def play(row, col, state, board, flag=False):
  rows, cols = len(board), len(board[0])
  x, y = row, col
  if x < 0 or x > rows or y < 0 or y > cols:
    print('Invalid coordinates!')
    return False
  if board[x][y] > 8: # clicked on mine
    state[0][x][y] = 'X' if not flag else 'F'
    if flag:
      state[2] += 1
    return True #not flag # game over only if mine clicked not flagged
  if flag:
    print('No mine here!')
    return False
  queue = [[x, y]]
  while queue:
    x, y = queue.pop(0)
    if state[0][x][y] != '#': # previously clicked/recursively visited cell
      continue
    state[1] += 1
    if board[x][y] > 0: # clicked on numbered cell
      state[0][x][y] = str(board[x][y])
      continue
    # cell has no mine surrounding it 
    state[0][x][y] = ''
    # click on surrounding 8 cells
    queue += surrounding_cells(x, y, rows, cols)
  return False

def ai_player(state, board):
  numbered_cell_neighbors = defaultdict(float)
  rows, cols = len(state[0]), len(state[0][0])
  # for i, j in itertools.product(range(rows), range(cols)):
  for i, j in np.ndindex((rows, cols)):
    if state[0][i][j].isdigit():
      n = int(state[0][i][j])
      flags = [(x, y) for x, y in surrounding_cells(i, j, rows, cols) if state[0][x][y] == 'F']
      safe_factor = -20 if n == len(flags) else 1
      neighbors = [(x, y) for x, y in surrounding_cells(i, j, rows, cols) if state[0][x][y] == '#']
      if (n - len(flags)) == len(neighbors) and len(neighbors) > 0:
        for x, y in neighbors:
          play(x, y, state, board, True)
        return ai_player(state, board)
      for x, y in neighbors:
        numbered_cell_neighbors[(x, y)] += safe_factor * n/len(neighbors)
  print(len(numbered_cell_neighbors), numbered_cell_neighbors)
  if numbered_cell_neighbors:
    x, y = min(numbered_cell_neighbors, key=numbered_cell_neighbors.get)
    return x, y
  print('Choosing random cell')
  return randint(0, rows-1), randint(0, cols-1) # stuck, unable to choose next best cell

num_mines = 0
mines = []

def ai_player_csp(state, board):
  csp = constraint.Problem()
  rows, cols = len(state[0]), len(state[0][0])
  fringe_cells = set()
  for i, j in np.ndindex((rows, cols)):
    if state[0][i][j].isdigit():
      n = int(state[0][i][j])
      neighbors = [(x, y) for x, y in surrounding_cells(i, j, rows, cols) if state[0][x][y] == '#']
      fringe_cells.update(neighbors)
      csp.addConstraint(constraint.ExactSumConstraint(n), neighbors)
  csp.addVariables(fringe_cells, [0, 1])
  solutions = csp.getSolutions()
  print(len(solutions))
  if solutions:
    fringe_dict = defaultdict(float)
    for solution in solutions:
      for cell in solution.keys():
        fringe_dict[cell] += solution[cell]
    safe = min(fringe_dict, key=fringe_dict.get)
    mine = max(fringe_dict, key=fringe_dict.get)
    if fringe_dict[safe] != fringe_dict[mine]:
      return safe
  return ai_player(state, board)

random_fails = 0

def autoplay(rows, cols, n):
  global random_fails, mines
  board, mines = create_board(rows, cols, n)
  num_mines = len(mines)
  display_state([board])
  print(mines)
  print('-'*30)
  state = [[['#']*cols for _ in range(rows)], 0, 0] # exposed grid, number of exposed cells, flagged mines
  done = False
  x, y = randint(0, rows-1), randint(0, cols-1)
  is_random_fail = True
  while not done:
    print('Computer plays', (x, y), 'Mines flagged: ', state[2])
    done = play(x, y, state, board)
    display_state(state)
    if done:
      if is_random_fail:
        random_fails += 1
      print('Game Over!')
      return False
    if (rows*cols - state[1]) == num_mines:# or state[2] == num_mines:
      print('Winner!')
      return True
    is_random_fail = False
    x, y = ai_player(state, board)
    # For 1000 runs of 10x10 board with 20 mines
    # win percentage for
    #   ai_player_csp: 24.72% overall, 30.19% excluding games over at first try
    #   ai_player: 11.01% overall, 13.78% excluding games over at first try

def main():
  rates=[]
  mines=40
  for m in range(mines):
      n = 200
      wins = 0
      losses = 0
      for i in range(n):
        if autoplay(10,10,m):
          wins += 1
        else:
          losses += 1
        if (i % 100) == 0 and i != 0:
          print(wins, losses, wins / i)
      print("total",wins, losses, wins/n)
      rates.append(wins/n)
  plt.plot(np.arange(mines),rates)
  plt.ylabel("win rates over 200 trials")
  plt.xlabel("mines")
  plt.savefig('output.png')

# def main():
#   n = 100
#   wins = 0
#   losses = 0
#   for i in range(n):
#     if autoplay(10, 10, 20):
#       wins += 1
#     else:
#       losses += 1
#     if i>0: print(wins, losses, wins / i)
#   print(wins, losses, wins/n)
#   print('Game over at first try:', random_fails)
#   print('Excluding them, win percentage:', 100*wins/(n-random_fails))

if __name__ == '__main__':
  main()