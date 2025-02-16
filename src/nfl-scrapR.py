#! /usr/bin/env python3


def get_boxscores(year,week):
    '''
    input: year of game, week of game
    processing: gets boxscore links for specified year and week. there
    should be 16 games every week unless teams have their bye weeks.
    output: list of boxscore links
    '''
    from bs4 import BeautifulSoup
    import requests


    url = 'https://www.pro-football-reference.com'
    r = requests.get(url + '/years/' + str(year) + '/week_' + str(week) +'.htm')
    soup = BeautifulSoup(r.content, 'html.parser')
    parsed_table = soup.find_all('table', class_="teams")

    game_list = []
    for data in soup.find_all('table', class_='teams'):
        for a in data.select("a[href*=boxscores]"):
            game_list.append(url + a.get('href'))

    return game_list


def get_gameinfo(url):
    '''
    input: url string of game
    processing: scrapes game info for game. creates composite key with gamedate + hometeam
    output: dataframe of game information (includes weather, vegas line, toss information, etc.)
    '''
    import re
    from bs4 import BeautifulSoup
    import requests
    import pandas

    try:
        r = requests.get(url)
        ## work around comments
        comm = re.compile("<!--|-->")
        soup = BeautifulSoup(comm.sub("", r.text), 'lxml')
        tables = soup.findAll('table', id = 'game_info')
        data_rows = tables[0].findAll('tr')

        game_data = [[td.getText() for td in data_rows[i].findAll(['th','td'])] for i in range(len(data_rows))][1:]
        ## add composite key
        game_data.insert(0, ['game_id',url[-16:-4]])
        ## get teams
        for home_team in soup.findAll("a", itemprop="name")[0:1]:
            game_data.insert(0, ['home_team',home_team.getText()])
        for away_team in soup.findAll("a", itemprop="name")[1:2]:
            game_data.insert(0, ['away_team',away_team.getText()])
        ## get coach names
        for home_coach in soup.select("a[href*=coaches]")[0:1]:
            game_data.insert(0, ['home_coach',home_coach.getText()])
        for away_coach in soup.select("a[href*=coaches]")[1:2]:
            game_data.insert(0, ['away_coach',away_coach.getText()])


        data = pandas.DataFrame(game_data)
        data = data.transpose().T.set_index(0).T.reset_index(drop = True)

        return data
    except:
        print("This URL: %s doesn't have \'Game Info\' available.\
        \nThis is most likely due to the fact that this game has not happened yet." % (url))

def nflscrapR(start_yr,end_yr):
    '''
    input: start year and end year of scrape
    processing: retrieves game info data for years specified
    output: game info dataframe for years specified
    '''
    import time
    import csv
    import os
    import pandas as pd

    print("Starting now..")

    os.chdir("/Users/anhthyngo/ds-projects/nfl-predict/data")

    start_time = time.time()

    url_list = [get_boxscores(year,week) for week in range(1,22) for year in range(start_yr,end_yr+1)]
    flat_list = [item for sublist in url_list for item in sublist]
    print("--- %s seconds to scrape %s game links ---" % (time.time() - start_time, len(flat_list)))

    start_time = time.time()

    game_info = pd.DataFrame()

    for game in flat_list:
        try:
            row = get_gameinfo(game)
            game_info = game_info.append(row,ignore_index = True)
            # be nice
            time.sleep(1)
        except:
            print(game)

    ## some urls don't have weather data
    game_info[['temperature','humidity','wind_mph','wind_chill']] = game_info['Weather'].str.split(',',expand=True)

    print("--- %s seconds to load dataframe ---" % (time.time() - start_time))
    file_name = 'scraped-game-info-%s-%s.csv' % (start_yr,end_yr)
    game_info.to_csv(file_name, index=False)


if __name__ == "__main__":
    nflscrapR(2014,2019)
