#!/usr/bin/python3
#### Othello Shell
#### Updated by P. Gabor Jan 28, 2018
#### Originally by P. White 2016-2018

import random, sys, os
import re
import time
import multiprocessing
import subprocess


def findIdx(lst, pattern):
  # returns the first index where the rgex matches, else -1
  for i, v in enumerate(lst):
    if re.search(pattern, v): return i
  return -1


def findIdxs(lst, pattern):
  # returns the indeces where the rgex matches, else []
  return [i for i, v in enumerate(lst) if re.search(pattern, v)]


def findFile(*fileSpec):
  mypath = os.getcwd()
  for fs in fileSpec:
    if fs == "random": return {"random"}
    if fs[-3:]==".py":               # If explicit filename is provided, then we must mean that one without capitalization
      if os.path.isfile(fs): return {fs}
    else:                            # If unique prefix is provided
      fs = fs.lower()
      for (dirpath, dirnames, filenames) in os.walk(mypath):
        setOfScripts = {*filenames}  # Gets all files in the path
        break
      setOfScripts = {s for s in setOfScripts if s[:len(fs)].lower()==fs and s[-3:]==".py"}
      if len(setOfScripts)==1: return setOfScripts
  return set()


def rngLim(c, d, n):
  if (abs(d) - 1) % (n-1):    # if diagonal direction
    return n-max(n-1-c%n if (d-1)%n else c%n, n-1-c//n if d<0 else c//n)
  return (n if d>0 else 1) - (d // abs(d)) * (c%n if d%n else c//n)


def legalMoves(othelloBoard, token):
  moves = {}
  for idx in [idx for idx,tkn in enumerate(othelloBoard) if tkn==dot]:
    for dir, lim in dirrng[idx]:
      for p in range(idx+dir,lim,dir):
        if othelloBoard[p]==".": break
        if othelloBoard[p]==token:
          if p==idx+dir: break
          if idx not in moves: moves[idx] = set()
          moves[idx].update(range(idx+dir,p,dir))
          break
  return moves
    

def makeMove(board, token, mv, affects):
  # affects are the positions of enemy tokens which flip
  for i in affects:
    board = board[:i] + token + board[i+1:]
  return board[:mv] + token + board[mv+1:]


def showBoard(board, mvNum, players, tokens, player, token, mv):
  if token:
    print("Game {}, Move {}; Player {} as {} vs. Player {} as {}".format(
           gameNum, mvNum, players[0], tokens[0], players[1], tokens[1]))
    print("Token {} moves to {} => X={} vs. O={}".format(token, mv, board.count('X'), board.count('O')))
  print("\n".join([str(i+1) + "  " + " ".join(board[i*sL:i*sL+sL]) for i in range(sL)]))
  print("\n   A B C D E F G H\n")





def parseArgs():
  # determine the board (defaults to standard starting board)
  # determine the token to play.  Defaults to X or O as board.count('.') unless only one side has a legal move
  # determine the contestants - one must be specified.
  # the second defaults to BaselineRandom, if it exists, else to first player
  # rounds to play, defaults to 1 (ie. 2 games)
  # secondsPerMove specified by prefixing a number with an s, defaults to 5
  args = sys.argv[1:]
  idxBrd = findIdx(args, "^[xXoO.]$")
  board = "."*27 + "OX......XO" + "."*27
  if idxBrd>=0:
    board = args[idxBrd].upper()
    del args[idxBrd]

  idxToken = findIdx(args, "^[xXoO]$")
  token = "XO"[board.count('.') % 2] if idxToken < 1 else args[idxToken].upper()
  if not legalMoves(board, token): token = "XO"["OX".find(token)]   # {'O':'X', 'X':'O'}[token]

  idxContestants = findIdxs(args, "^(.{3,}|[^sS.0-9]|[sS][^0-9.])")
  help = "Usage: contest [board] contestant1pfx [contestant2pfx] [rndsToPlay=1] [s+secsPerMove]"
  if not idxContestants or len(idxContestants)>2: exit(help)

  scripts = findFile(args[idxContestants[0]])
  if not len(scripts): exit("Contestant1 not found\n" + help)
  if len(scripts)>2:   exit("Contestant1 prefix not unique: {}\n{}".format(scripts, help))
  contestant1 = scripts.pop()

  if len(idxContestants)==1:
    contestant2 = "random"     #   "BaselineRandom.py" if os.path.isfile("BaselineRandom.py") else contestant1
  else:
    scripts = findFile(args[idxContestants[1]])
    if not len(scripts): exit("Contestant2 not found\n" + help)
    if len(scripts)>2:   exit("Contestant2 prefix not unique: {}\n{}".format(scripts, help))
    contestant2 = scripts.pop()

  idxRounds = findIdx(args, "^(\\d+[.]?\\d*|[.]\\d+)$")
  gameCt = 2 if idxRounds < 0 else int(2*float(args[idxRounds])+.5)

  idxSecsPerMove = findIdx(args, "^[sS](\\d+[.]?\\d*|[.]\\d+)$")
  secsPerMove = 5 if idxSecsPerMove < 0 else float(args[idxSecsPerMove][1:])

  return board, token, ["A-"+contestant1, "B-"+contestant2], gameCt, secsPerMove


def getMove(board, playerScript, token, secsPerMove):
  # Preparation
  timedOut = False
  errOut, actualOut = "", ""
  #  myargs = [ sys.executable , "-u", '"{}"'.format(playerScript) , board, token, ">out.txt", "2>err.txt" ]
  # myargs = [ sys.executable , "-u", '"{}"'.format(playerScript) , board, token, ">{}".format(OUTFILE), "2>{}".format(ERRFILE) ]

  running     = multiprocessing.Value('i', 1)
  best_shared = multiprocessing.Value('i', -99)
  brd = '?'*11 + '??'.join([board[i:i+8] for i in range(0,64,8)]) + '?'*11
  brd = brd.replace('X', '@').replace('O', 'o')

  po = multiprocessing.Process(target=dctContestants[playerScript].best_strategy, \
                               args=(brd, "@o"["XO".find(token)], best_shared, running))
  t1 = time.time()
  po.start()
  if po.is_alive():
    print ("Putting time limit on move for {} ".format(playerScript), end='')
    po.join(secsPerMove)
    running.value = 0
    time.sleep(0.1)
    timedOut = po.is_alive()
    po.terminate()
    time.sleep(0.1)
  move = best_shared.value
  print ("The raw best value found was '{}'".format(move))
  if move > 0: move = 8 * (move // 10) + (move % 10) - 1 - 8
  print("In %4.2f secs, got move = %i" % (time.time() - t1, move))

  if po.is_alive():
#    timedOut = True
#    errOut = "Timed out"
    if os.name != "posix":
      print ("Initiating TASKKILL of {}".format(po.pid))
      pok = subprocess.Popen("TASKKILL /F /PID {} /T".format(po.pid))
      pok.wait(20)    # waiting for TASKKILL to finish
    else:
      print("Process still alive at termination attempt")

  if timedOut and not errOut: errOut = txtTimedOut
  print ("playerScript: {} as {} ==> {}".format(playerScript, token, move))
  return move, errOut, actualOut





def playGame(board, contestants, tokens, secsPerMove):
  # returns board, moveTranscript, mostRecentMove, errMsg, actualOut
  
  playerNum = 0                                 # index of player to move
  moves = []                                    # transcript of game
  lm = legalMoves(board, tokens[playerNum])     # possible moves

  while lm:                                                          # While a move is possible ...
    print ("About to get move for {} ({}) from among {}".format(tokens[playerNum], contestants[playerNum], {*lm.keys()}))
#    print ("Contestant dictionary: {}".format(dctContestants))
    if contestants[playerNum][2:] == "random":
      mv, msg, actual = random.choice([*lm]), "", ""
    else:
      mv, msg, actual = getMove(board, contestants[playerNum], tokens[playerNum], secsPerMove)  # get a move
    if msg[:len(txtTimedOut)]==txtTimedOut:
      moves.append(-2)
      if msg==txtTimedOut: msg=""

    mvCt = len({*moves}-{-1,-2})
    if msg or mv not in lm:                                          # If error or move invalid
      # Report failure
      return [board, moves, mv, msg or "Illegal move attempt of {}".format(mv), actual]
    board = makeMove(board, tokens[playerNum], mv, lm[mv])    # Make the move
    moves.append(mv)                                          # Record it


    showBoard(board, mvCt+1, contestants, tokens, contestants[playerNum], tokens[playerNum], mv)

    playerNum = 1-playerNum                                   # Switch sides
    lm = legalMoves(board, tokens[playerNum])

    if not lm:                                                # If no possible moves
      plyr = contestants[playerNum]
      playerNum = 1-playerNum                                 #   Player must pass
      lm = legalMoves(board, tokens[playerNum])
      if lm:
        moves.append(-1)                                      #   provided opponent can move
        print ("\nPlayer {} must pass.\n".format(plyr))

  return [board, moves, mv, "", actual]                     # game over






def main():
  global theX, theO, dot, sL, txtTimedOut, dirs, dirrng, dctContestants
  theX, theO, dot, sL = "X", "O", ".", 8    # sL = side length
  txtTimedOut = "Timed out"


  startTime = time.time()
  pyver = re.sub(' [^Z]*', "", sys.version)
  print ("{} running under python version {}".format(os.path.basename(__file__), pyver))


  #### initialization
  # the set of directions in which one can go for making moves
  dirs = [{h+v for h in [-1,0,1] for v in [-sL,0,sL] for b in [c+h+v+h+v] \
                   if (b>=0)*(b<sL*sL)*((b%sL-c%sL)*h>=0)}-{0} for c in range(sL*sL)]
  # the direction together with the boundary of where one must check for bracketing (used in legalMoves)
  dirrng = [[(dir,idx+rngLim(idx,dir,sL)*dir) for dir in setOfDirs] for idx,setOfDirs in enumerate(dirs)]



  board, token, contestants, gameCt, secsPerMove = parseArgs()
  playerIdx = random.choice([0, 1])          # index of the player to go first
  aRes, tokens = [], [token, "XO"["OX".find(token)]]
# primaryTknCt, secondaryTknCt, gamesWon, gamesLost, worst2

  dctContestants = {cntstnt: "" for cntstnt  in contestants}
  i = 0
  for cntstnt in dctContestants:
    if cntstnt[2:]=="random": continue
    imprt = "import {} as con{}\ndctContestants['{}'] = con{}.Strategy()".format(cntstnt[2:][:-3], i, cntstnt, i)
    print ("About to import\n" + imprt)
    exec(imprt)
    i += 1


  # Conduct the contest here
  global gameNum
  for gameNum in range(1,gameCt+1):
  #  primaryPlayer is contestants[0]
  #  secondaryPlayer is contestants[1]
  #  player to play first is contestants[playerIdx]
  ##  primaryPlayer token is "XOX"[tokens[0]=="O"+playerIdx]
  #  primaryPlayer token is tokens[playerIdx]

    # returns board, moveTranscript, mostRecentMove, errMsg, actualOut
    print ("About to start game")
    res = playGame(board, contestants[::1-2*playerIdx], tokens, secsPerMove)
#    aRes.append(res + ["XOX"[(token=="O")+playerIdx], gameNum])
    aRes.append(res + [tokens[playerIdx], gameNum])
#    tokens = tokens[::-1]
    playerIdx = 1 - playerIdx

  # Compute the stats here
  ERRIDX, GAMENMIDX, PRIMARYTOKENIDX = 3, 6, 5
  aErr = [res for res in aRes if res[ERRIDX]]
  if aErr:
    print (aErr)
    print ("{} error{} detected:".format(len(aErr), "s were" if len(aErr) else " was"))
    for res in aErr:
      primaryTkn = res[PRIMARYTOKENIDX]
      print ("\nGame {}; {} as {} vs. {} as {}".format(
        res[GAMENMIDX], contestants[0], primaryTkn, contestants[1], "XO"["OX".find(primaryTkn)]))
      res1ct = len(res[1]) + 2*res[1].count(-1) - res[1].count(-2)
      tknToMove = "XO"[((token=="O") + res1ct) % 2]
      print ("Board/tkn to move: {} {}".format(res[0], tknToMove))
      showBoard(res[0], "", "", "", "", "", "")
      print ("History: {}\nLegal moves: {}\n".format(" ".join([str(rs) for rs in res[1]]), {*legalMoves(res[0], tknToMove)}))
      if res[2]>=0: print("Move attempt: {}".format(res[2]))
      print("Err msg:\n  " + "\n  ".join(res[ERRIDX].splitlines()))
      exit()


  scores = [(tknCt - (sL*sL - tknCt - res[0].count(dot)), idx) for idx, res in enumerate(aRes) \
                                                             for tknCt in [res[0].count(res[PRIMARYTOKENIDX])]]
  rest = [*range(len(scores))]
  if len(aRes)>20:
    scores.sort()
    worst = {scores[idx][1] for idx in range(3)}
    best  = {scores[-idx-1][1] for idx in range(3)}
    rest  = {*range(len(scores))} - worst - best
    rest  = (sorted([*rest]) + [*best] + [*worst])[-20:]

  for idx in rest:
    res = aRes[idx]
    primaryTkn = res[PRIMARYTOKENIDX]
    ptc        = res[0].count(primaryTkn)
    print ("\nGame {}; {} as {} vs. {} as {} ==> {} to {}".format(
      res[GAMENMIDX], contestants[0], primaryTkn, contestants[1],
      "XO"["OX".find(primaryTkn)], ptc, sL*sL - ptc - res[0].count(dot)))
    showBoard(res[0], "", "", "", "", "", "")
    print ("History: {}\n".format(" ".join([str(rs) for rs in res[1]])))


  won   = sum([tknCt > sL*sL - tknCt - res[0].count(dot) for res in aRes for tknCt in [res[0].count(res[PRIMARYTOKENIDX])]])
  lost  = sum([tknCt < sL*sL - tknCt - res[0].count(dot) for res in aRes for tknCt in [res[0].count(res[PRIMARYTOKENIDX])]])
  smry  = "Games won: {}; tied: {}; lost: {}\n".format(won, len(aRes)-won-lost, lost)
  tknCt = sum(res[0].count(res[PRIMARYTOKENIDX]) for res in aRes)
  dotCt = sum(res[0].count(dot) for res in aRes)
  nmyCt = sL*sL*len(aRes) - tknCt - dotCt
  tmtCt = sum(res[1].count(-2) for res in aRes)
  pct   = "{}".format(100*tknCt / (tknCt + nmyCt))[:6]
  smry += "Primary token count: {}; Enemy token count: {} ==>  {}%".format(tknCt, nmyCt, pct)
  if tmtCt: smry += "\nTimeouts: {}\n".format(tmtCt)
  print(smry)


  print ("\nScores: {}".format(scores))


if __name__ == '__main__':
  multiprocessing.freeze_support()
  main()

