#!/usr/bin/python3
#
# Othello Lab 5+ grader - Othello Moderator
#
# Original development Torbert, 18 Dec 2015: mod.py
# updated by Gabor, Jan - Feb, 2016 to deal with timeouts: modmod.py
# further updates by Gabor, Jan, 2018 to facilitate grading

# usage:
# python3 modmod.py PrimaryScript [secondaryScript] [numberOfRounds]
# 
# primaryScript is either an explicit script file or the unique prefix for a script file in the same directory
# secondaryScript, if given, works the same as primaryScript.
#   If omitted, it looks for BaselineRandom.py and failing that defaults to the primaryScript
# The number of rounds is half the number of games.
#   The default is 1, meaning both sides will play one game apiece as x (and one as o)
#
# Both primaryScript and secondaryScript will be given as input,
#   an Othello board position and a token (x or o)
#   The final number, an index, output by the script will be taken as the move
#   A1 notation is not used
##################################################

from subprocess import Popen
from time       import time, ctime, strptime
from os         import path, remove
import sys, re, os, random
import subprocess    # linux evidently needs this with TimeoutExpired

##################################################
timeLeft = 5    # number of seconds allowed per move
help     = "Usage: modmod.py primaryScript [secondaryScript] [rounds]"
sL       = 8
theX, theO, dot = "X", "O", "."


startTime = time()
pyver = re.sub(' [^Z]*', "", sys.version)
print ("{} running under python version {}".format(path.basename(__file__), pyver))


def getMove(board, playerScript, token):
  # Preparation
  timedOut = False
  if path.isfile("out.txt"): remove("out.txt")
  if path.isfile("err.txt"): remove("err.txt")

  # Construct and execute the move request   
  myargs = [ sys.executable , "-u", '"{}"'.format(playerScript) , board, token, ">out.txt", "2>err.txt" ]
  po = Popen ( " ".join(myargs), shell=True )

  # wait for the request to finish
  if os.name == "posix":
    try:
      po.wait(float(timeLeft))
    except subprocess.TimeoutExpired:
      subprocess.call("ps -ef | awk '$3 == \"" + str(po.pid) + "\" {print $2}' | xargs kill -9", shell=True)
      po.kill()        
      timedOut = True
       
  else:
    try:
      po.wait(float(timeLeft))
    except subprocess.TimeoutExpired:
      timedOut = True
      print ("Initiating TASKKILL of {}".format(po.pid))
      pok = Popen("TASKKILL /F /PID {} /T".format(po.pid))
      pok.wait(20)    # waiting for TASKKILL to finish


  # Now parse the results
  errOut = open("err.txt", "r").read().strip() if path.isfile("err.txt") else ""
  actualOut = open("out.txt", "r").read().strip() if path.isfile("out.txt") else ""

  grps = rexSyn1.search(errOut)
  if grps: return -1, "Syntax error on line {}: {}".format(grps.group(1), grps.group(2)), actualOut

  if errOut and not timedOut:
    grps = rexScript.search(errOut)
    if grps: return -1, "Script error at line {}: {}\n  {}".format(grps.group(1), grps.group(2), grps.group(3)), actualOut
    return -1, "Unknown error:\n{}".format(errOut), actualOut

  if timedOut==True: errOut = txtTimedOut
  out1 = rexDecimals.sub("", actualOut)    # gets rid of decimals
  grps = rexLastNum.search(out1)

  if not grps: return -1, errOut + ("/ " if errOut else "") + "No move given", actualOut
  return int(grps.group(1)), errOut, actualOut



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


# def showBoard(board, mvNum, player, token, mv):
def showBoard(board, mvNum, players, tokens, player, token, mv):
#  global gnum
  print("Game {}, Move {}; Player A-{} as {} vs. Player B-{} as {}".format(
         gameNum, mvNum, players[0], tokens[0], players[1], tokens[1]))
#  print("\nMove {}\nPlayer {} as {} moves to {}  ===> X:{} vs. O:{}".format(
#             mvNum, player, token, mv, board.count(theX), board.count(theO)))
  print("Token {} moves to {} => X={} vs. O={}".format(token, mv, board.count('X'), board.count('O')))
  print("\n".join([str(i+1) + "  " + " ".join(board[i*sL:i*sL+sL]) for i in range(sL)]))
  print("\n   A B C D E F G H\n")


def playGame(players, tokens):
  # returns: board, moveTranscript, primaryPlayerToken, mostRecentMove, possibleMoves, errMsg, moveScore
  board = startBoard
  playerNum = tokens.index(theX)                # index of player to move
  moves = []                                    # transcript of game
  lm = legalMoves(board, tokens[playerNum])     # possible moves

  while lm:                                                          # While a move is possible ...
    mv, msg, actual = getMove(board, players[playerNum], tokens[playerNum])  # get a move
    if msg[:len(txtTimedOut)]==txtTimedOut:
      moves.append(-2)
      if msg==txtTimedOut: msg=""

    mvCt = len({*moves}-{-1,-2})
    if msg or mv not in lm:                                          # If error or move invalid
      # Report failure
      return board, moves, tokens[0], mv, lm, msg or "Illegal move", mvCt//4, players[1], actual
    board = makeMove(board, tokens[playerNum], mv, lm[mv])    # Make the move
    moves.append(mv)                                          # Record it


    plyr = "{}-{}".format(chr(65+playerNum), players[playerNum])
    showBoard(board, mvCt+1, players, tokens, plyr, tokens[playerNum], mv)

    playerNum = 1-playerNum                                   # Switch sides
    lm = legalMoves(board, tokens[playerNum])

    if not lm:                                                # If no possible moves
      plyr = "{}-{}".format(chr(65+playerNum), players[playerNum])
      playerNum = 1-playerNum                                 #   Player must pass
      lm = legalMoves(board, tokens[playerNum])
      if lm:
        moves.append(-1)                                      #   provided opponent can move
        print ("\nPlayer {} must pass.\n".format(plyr))

  return board, moves, tokens[0], -1, lm, "", 30, players[1], actual   # game over


def findFile(*fileSpec):
  mypath = os.getcwd()
  for fs in fileSpec:
    if fs[-3:]==".py":               # If explicit filename is provided
      if path.isfile(fs): return {fs}
    else:                            # If unique prefiex is provided
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




rexSyn1     = re.compile(", line (\\d+)$\\s*^\\s*(.*?)$.*SyntaxError:", re.S | re.M)
rexScript   = re.compile("^Traceback.*line (\\d+).*^\\s*(.+)$.*^(.+)$", re.M | re.S)
rexDecimals = re.compile("\\d+[.]\\d*|[.]\\d+")
rexLastNum  = re.compile("(\\d+)\\D*$")
reNum       = re.compile("^\\d+[.]?\\d*|[.]\\d+$")
txtTimedOut = "Timed out"


if len(sys.argv)<2: exit("No arguments given\n" + help)

scripts = findFile(sys.argv[1])
if not len(scripts): exit("No primary script found\n" + help)
if len(scripts)>2:   exit("Primary script spec not unique: {}\n{}".format(scripts, help))
primary = scripts.pop()

if len(sys.argv)>3 or (len(sys.argv)==3 and not reNum.search(sys.argv[1])):
      scripts = findFile(sys.argv[2], "BaselineRandom.py", primary)
else: scripts = findFile(             "BaselineRandom.py", primary)
if len(scripts)>2: exit("Secondary script spec not unique: {}\n{}".format(scripts, help))
secondary = scripts.pop()
players = (primary, secondary)



startBoard = dot * ((sL*sL-sL)//2-1) + theO + theX + dot * (sL-2) + theX + theO + dot * ((sL*sL-sL)//2-1)
# the set of directions in which one can go for making moves
dirs = [{h+v for h in [-1,0,1] for v in [-sL,0,sL] for b in [c+h+v+h+v] \
                 if (b>=0)*(b<sL*sL)*((b%sL-c%sL)*h>=0)}-{0} for c in range(sL*sL)]
# the direction together with the boundary of where one must check for bracketing
dirrng = [[(dir,idx+rngLim(idx,dir,sL)*dir) for dir in setOfDirs] for idx,setOfDirs in enumerate(dirs)]


gameCt = int(2*float(sys.argv[-1])) if reNum.search(sys.argv[-1]) else 2
tokens = [theX, theO, theX][random.randint(0,1):][:2]
primaryTknCt, dotCt, secondaryTknCt = 0, 0, 0
aRes = []
for gameNum in range(gameCt):
  # board, moveTranscript, primaryPlayerToken, mostRecentMove, possibleMoves, errMsg, moveScore, secondaryPlayer, actualOut
#  res = playGame((primary, primary) if gameNum%2 and secondary=="BaselineRandom.py" else players, tokens)
  res = playGame(players, tokens)
  aRes.append(res)
  tokens = tokens[::-1]
  if not res[5]:
    ptc, dotCt     = res[0].count(res[2]), res[0].count(dot)
    primaryTknCt   += ptc
    dotCt          += dotCt
    secondaryTknCt += len(res[0]) - ptc - dotCt

pct = primaryTknCt + secondaryTknCt
pct = "{}".format(primaryTknCt / pct)[:6] if pct else "N/A"
moveScore = sum(rs[6] for rs in aRes)

# Overall test summary
smry = "Summary for A-{}: move score: {}, total tokens: {}, enemy tokens: {}, percent: {}".format(
          primary, moveScore, primaryTknCt, secondaryTknCt, pct)
print(smry)

# Summary per game
for gnum, rs in enumerate(aRes):
  brd = rs[0]
  sOut = "Board: {}\nMoves: {}\n".format(brd, " ".join([str(i) for i in rs[1]]))
  if not rs[5]:
    sOut = "Game {} as {} vs B-{} => move score {}, tokens: {} vs. {}\n{}\n".format(
          gnum+1,rs[2], rs[7], rs[6], rs[0].count(rs[2]), len(brd)-brd.count(rs[2])-brd.count(dot), sOut)
  else:
    sOut = "\nGame {} as {} vs B-{} => move score {}".format(gnum+1, rs[2], rs[7], rs[6]) + \
           "\nError:\n{}\n".format("  "+"\n  ".join(rs[5].splitlines())) + sOut
    if rs[3]>=0: sOut += "Attempted move: {}\n".format(rs[3])
    sOut += "Legal moves: {}\n\n".format(", ".join([str(k) for k in rs[4]]))
  print ("  " + "\n  ".join(sOut.splitlines()))

print(smry)
print ("Script ran in {} seconds".format(time() - startTime))