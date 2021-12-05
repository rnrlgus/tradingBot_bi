import pandas as pd


def get_macd(df):
    df = pd.DataFrame(df)

    ma_50 = df['close'].rolling(window=50).mean()

    df = df.assign(ma50 = ma_50)
    return df


def algo(data):
    data["state"] = ''
    data["long_ratio"] = ''
    data["short_ratio"] = ''
    data["ratio"] = ''

    for i in range(1, len(data)):
        if data.loc[i-1, 'state'] != 'long' and data.loc[i-1, 'state'] != 'short':
            if data.loc[i-1,'ma50'] < data.loc[i-1, 'close']:
                data.loc[i, 'state'] = 'long'
                buy_price = data.loc[i, 'open']
            if data.loc[i - 1, 'ma50'] > data.loc[i - 1, 'close']:
                data.loc[i, 'state'] = 'short'
                buy_price = data.loc[i, 'open']
        else:
            if data.loc[i-1, 'state'] == 'long':
                if data.loc[i-1, 'state'] != 'terminate':
                    data.loc[i, 'state'] = 'long'
                if data.loc[i, 'close'] < data.loc[i, 'ma50']:
                    sell_price = data.loc[i, 'close']
                    data.loc[i, 'ratio'] = sell_price / buy_price
                    data.loc[i, 'long_ratio'] = sell_price / buy_price
                    data.loc[i, 'state'] = 'terminate'

            if data.loc[i-1, 'state'] == 'short':
                if data.loc[i-1, 'state'] != 'terminate':
                    data.loc[i, 'state'] = 'short'
                if data.loc[i, 'close'] > data.loc[i, 'ma26']:
                    sell_price = data.loc[i, 'close']
                    data.loc[i, 'ratio'] = buy_price / sell_price
                    data.loc[i, 'short_ratio'] = buy_price / sell_price
                    data.loc[i, 'state'] = 'terminate'

    return data

def conclude(data, ticker, column):
    minimum = float('inf')
    maximum = 1.0
    ratio = 1
    baddest = 1
    goodest = 1
    profit = 0
    damage = 0
    pro_ratio = 0
    dam_ratio = 0
    for i in range(0, len(data)):
        if data.loc[i, 'ma100'] != '':
            if minimum > data.loc[i, 'ma100']:
                minimum = data.loc[i, 'ma100']
            if maximum < data.loc[i, 'ma100']:
                maximum = data.loc[i, 'ma100']
        if data.loc[i, column] != '':
            if data.loc[i, column] - 0.00278 > 1:
                profit += 1
                pro_ratio += data.loc[i, column] - 0.00278
                if goodest < data.loc[i, column] - 0.00278:
                    goodest = data.loc[i, column] - 0.00278
            if data.loc[i, column] - 0.00278 < 1:
                damage += 1
                dam_ratio += data.loc[i, column] - 0.00278
                if baddest > data.loc[i, column] - 0.00278:
                    baddest = data.loc[i, column] - 0.00278
            ratio *= data.loc[i, column] - 0.00278
    if profit != 0 and damage != 0:
        aver_pro = pro_ratio / profit
        aver_dam = dam_ratio / damage
        win_rate = profit / (profit + damage)
    else:
        aver_pro = 0
        aver_dam = 0
        win_rate = 0
    rate = maximum/minimum
    model = (ratio / (rate+ratio))*100
    return ratio, model, rate, aver_pro, aver_dam, win_rate


def print_rate(ticker, model, rate, ratio, kelly):
    print(ticker)
    print('모델적합도', int(model), '%')
    print('최고 상승률', int(rate * 100), '%')
    print('총 이율:', int(ratio * 100), '%')
    print("캘리의 법칙", kelly, '\n')

def backtest(data, ticker, print=True):

    macd_data = get_macd(data)
    result = algo(macd_data)
    ratio, model, rate, aver_pro, aver_dam, win_rate = conclude(result, ticker, 'ratio')

    if win_rate != 0:
        kelly = win_rate - (1-win_rate)/((aver_pro-1)/(1-aver_dam))
    else:
        kelly = 0
    if kelly < 0:
        kelly = 0

    if print == True:
        print_rate(ticker, model, rate, ratio, kelly)

    return macd_data, kelly

