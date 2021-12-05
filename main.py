import ccxt
import pprint
import time
import math
import datetime
import pandas as pd
import re
import backtest
import judge


def login():
    with open("./api.txt") as f:
        lines = f.readlines()
        api_key = lines[0].strip()
        secret = lines[1].strip()

    binance = ccxt.binance(config={
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        'options':{
            'defaultType': 'future'
        }
    })
    print('로그인')
    return binance

def get_df(binance, ticker):

    data = binance.fetch_ohlcv(
    symbol=ticker,
    timeframe='4h',
    since=None,#타임스탬프 형식인지 확인
    limit=1500
    )
    name = re.sub("\/", "", ticker)
    df = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms') + datetime.timedelta(hours=9)
    df.set_index('datetime', inplace=False)

    return df

def get_amount(binance, kelly, ticker='BTC/USDT'):

    usdt = get_usdt(binance)
    data = binance.fetch_ticker(ticker)

    usdt = usdt['total']
    price = data['last']

    usdt = usdt*kelly
    price = usdt / price

    price = price*1000
    price = math.trunc(price)
    amount = price / 1000

    return amount

def refine_kelly(kelly):
    kelly = kelly * 10
    kelly = math.trunc(kelly)
    kelly = kelly / 10
    return kelly

def get_kellys(dictionary, tickers):
    k = 0
    kellys = 0.0
    for i in range(len(dictionary)):
        if dictionary[tickers[i]][1] != 0.0:
            kellys += dictionary[tickers[i]][1]
            k += 1
    aver = round(kellys / k,1)

    print('캘리평균', aver)
    return aver

def get_tickers(binance):
    tickers = []
    markets = binance.load_markets()
    for i in markets:
        tickers.append(i)
    tickers = [s for s in tickers if "/USDT" in s]

    return tickers

def get_usdt(binance):
    balance = binance.fetch_balance(params={"type":'future'})

    return balance['USDT']

def bool_own(own, ticker):
    if ticker in own:
        return True
    else:
        return False

def get_dictionary(binance):
    tickers = get_tickers(binance)
    dictionary = {string: [False, 0.0] for string in tickers}
    return dictionary

def get_amounts(binance):
    amount = get_dictionary(binance)
    balance = binance.fetch_balance(params={"type": 'future'})
    positions = balance['info']['positions']
    positions = [s for s in positions if "USDT" in s["symbol"]]
    for position in positions:
        ticker = position["symbol"]
        positionAmt = float(position['positionAmt'])
        ticker = ticker[:-4] + '/' + ticker[-4:]
        try:
            amount[ticker][1] = positionAmt
        except KeyError as e:
            continue

    return amount

def have(binance, amounts):
    tickers = get_tickers(binance)

    for i in range(len(tickers)):
        if amounts[tickers[i]][1] == 0.0:
            del amounts[tickers[i]]

    return amounts

def kelly_sig(dictionary):
    tickers = list(dictionary.keys())
    kellys = get_kellys(dictionary, tickers)

    for i in range(len(tickers)):
        if dictionary[tickers[i]][1] <= kellys:
            del dictionary[tickers[i]]

    return dictionary


def get_coins(binance, print=True):
    tickers = get_tickers(binance)
    dictionary = {string: ['None', 0.0] for string in tickers}

    for i in range(len(tickers)):
        data = get_df(binance, tickers[i])
        df, kelly = backtest.backtest(data, tickers[i], print)

        dictionary[tickers[i]][1] = refine_kelly(kelly)
        if (judge.judge_buy(df, tickers[i]) == True):
            dictionary[tickers[i]][0] = "BUY"
        if judge.judge_sell(df, tickers[i]) == True:
            dictionary[tickers[i]][0] = "SELL"

    return dictionary

def start_long(binance, ticker, kelly):
    amount = get_amount(binance, kelly, ticker)
    print('amount:',amount)
    order = binance.create_market_buy_order(
        symbol = ticker,
        amount = amount
    )
    pprint.pprint(order)

def terminate_long(binance, ticker, amount):
    print('sell_amount:', amount)
    order = binance.create_market_sell_order(
        symbol = ticker,
        amount = amount
    )
    pprint.pprint(order)

def set_leverage(binance, ticker):
    print('레버리지 설정 진입')
    markets = binance.load_markets()
    market = binance.market(ticker)
    leverage = 3
    resp = binance.fapiPrivate_post_leverage({
        'symbol': market['id'],
        'leverage': leverage
    })

def sub():
    binance = login()

    coins = get_coins(binance, False)   #캘리 들어간 딕셔너리
    ticks = list(coins.keys())
    amounts = get_amounts(binance)      #amount 들어간 딕셔너리
    own = have(binance, amounts)

    for i in range(len(ticks)):
        if bool_own(own, ticks[i]) == False:
            if coins[ticks[i]][0]=='BUY':
                if coins[ticks[i]][1] > 0.1:
                    set_leverage(binance, ticks[i])
                    start_long(binance, ticks[i], coins[ticks[i]][1])
                    print(ticks[i], 'BUY')
        else:
            if coins[ticks[i]][0]=='SELL':
                if bool_own(own, ticks[i])==True:
                    terminate_long(binance, ticks[i], own[ticks[i]][1])
                    print(ticks[i], 'SELL')

    amounts = get_amounts(binance)
    own = have(binance, amounts)
    own_list = list(own.keys())
    print('보유중인 코인:', own_list)

def main():
    now = datetime.datetime.now()
    ago = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute) + datetime.timedelta(minutes=10)

    while True:
        try:
            now = datetime.datetime.now()
            if ago < now < ago + datetime.timedelta(minutes=5):
                now = datetime.datetime.now()
                ago = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute) + datetime.timedelta(minutes=10)
                sub()
            print(now, "vs", ago)
        except Exception as e:
            print('에러발생', e)
        time.sleep(1)
