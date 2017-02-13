import sys
import time
import math
import urllib.request
import xml.etree.ElementTree as ET
import re


from datetime import date
from datetime import datetime
from datetime import timedelta

def playtime(gameId):

  root = ET.fromstring(urllib.request.urlopen("https://www.boardgamegeek.com/xmlapi2/thing?id="+str(gameId)).read())
  time.sleep(0.3)
  
  item = root.find('item')
  playLen = item.find('playingtime')
  minutes = int(playLen.get('value'))

  return minutes

def getPlayStats(bggId,minDate):
  stats = []
  playDict = {}

  baseUrl = "https://www.boardgamegeek.com/xmlapi2/plays?username="+bggId+"&mindate="+minDate.isoformat()+"&page="
  
  pPage = 1
  playData = urllib.request.urlopen(baseUrl+str(pPage)).read()

  playTree = ET.fromstring(playData)

  totalPlays = playTree.get('total')
  totalPages = math.floor(int(totalPlays)/100)+1

  for pg in range(1, totalPages+1):
    print('Processing page ' + str(pg))
    playData = urllib.request.urlopen(baseUrl+str(pg)).read()
    playTree = ET.fromstring(playData)
    # time.sleep(1)
    for play in playTree.findall('play'):
      pDate = play.get('date')
      pQty = int(play.get('quantity'))
      for pItem in play.findall('item'):
        pName = pItem.get('name')
        pGameId = pItem.get('objectid')
        
      if pGameId not in playDict:
        playDict[pGameId] = [pName,pQty,pDate]
      else:
        playDict[pGameId][1] = playDict[pGameId][1] + pQty

  print('Getting playtimes for ' + str(len(playDict)) + ' games...')
  i=1
  for game in playDict:
    pGameLen = playtime(game)
    gameRec = playDict[game]
    print (str(i) + " - " + gameRec[0])
    i += 1
    gameRec.append(pGameLen)
    gameRec.append(pGameLen * gameRec[1])
    gameRec.append(game)
    stats.append(gameRec)

  return stats

def totalTime(gameInfo):
  rc = gameInfo[4]  # plays*time
  if gameInfo[1] > 1:
    rc = rc+1000000  # single plays to the bottom of the list

  datenum = datetime.strptime(gameInfo[2],"%Y-%m-%d")
  rc = rc + (datenum.toordinal()/1000000)

  rc = -rc  # because we want highest total first.
  return rc

def printStats(gameStats):
  # list
  # Total games played
  # Games played 2+ times
  i = 0
  plays = 0
  multi = 0

  print("")

  for game in gameStats:
    i += 1
    plays += game[1]
    if (game[1] > 1):
      multi += 1
    print (str(i) + ". " + game[0] + " (" + str(game[1]) + " plays, Total: " + str(game[4]) + ", Last Played: " + game[2] + ")")
    
  print ("")
  print ("Total plays: " + str(plays))
  print ("Games played more than once: " + str(multi))

  return

def statsToCsv(gameStats, filename, bggId):
  gameCollection = {}
  
  collUrl = "https://www.boardgamegeek.com/xmlapi2/collection?username=iklinck&played=1"
  collData = urllib.request.urlopen(collUrl).read()
  collTree = ET.fromstring(collData)

  outf = open(filename + '.csv', 'w')
  outf.write('Game,Plays,Total Time,Last Played,Long,Owned,Traded\n')
  for game in collTree.findall('item'):
    gId = game.get('objectid')
    gameDetails = ['NOT_OWNED','']
    for gStat in game.findall('status'):
      gOwned = gStat.get('own')
      if gOwned == "1":
        gameDetails[0] = ""
    gComment = game.get('comment')

    for child in game:
      if child.tag == 'comment':
        if re.search(r"[T]",child.text):
          gameDetails[1] = "TRADED_FOR"
    gameCollection[gId] = gameDetails

  for game in gameStats:
    line = '"' + game[0] + '",' + str(game[1]) + "," + str(game[4]) + "," + game[2]
    if game[3] >= 75:
      line = line + ",LONG"
    else:
      line = line + ","

    line = line + "," + gameCollection[game[5]][0] + "," + gameCollection[game[5]][1] + "\n"

    outf.write(line)
  outf.close()

  return

def main():
  if len(sys.argv) < 3:
    print ('usage: ./playstats.py BGG-ID num-days')
    sys.exit(1)
  
  # exception handling:
  # bad data types
  # invalid BGG ID

  # Add handling for Unpublished Prototype - 18291

  minDate=date.today()-timedelta(int(sys.argv[2]))
  
  playStats = []

  playStats = getPlayStats(sys.argv[1],minDate)
  playStats = sorted(playStats, key=totalTime)
  
  printStats(playStats)
  if (len(sys.argv) > 3):
    statsToCsv(playStats, sys.argv[3], sys.argv[1])


if __name__ == '__main__':
  main()
