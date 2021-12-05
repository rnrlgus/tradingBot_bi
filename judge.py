

def judge_buy(data, ticker):
    minus2 = data.index[-2]

    #long 판단 추가
    if data.loc[minus2, 'close'] > data.loc[minus2, 'ma4']:
        return True

    print('결론 : ' + ticker + ' long 진입 대기!!\n')
    return False

def judge_short(data, ticker):
    minus2 = data.index[-2]

    #short 판단 추가
    if data.loc[minus2, 'close'] < data.loc[minus2, 'ma4']:
            return True

    print('결론 : ' + ticker + ' short 진입 대기!!\n')
    return False

def judge_long_terminate(data, ticker):
    minus2 = data.index[-2]

    print(ticker + ' : long 종료 판단')
    if data.loc[minus2, 'close'] < data.loc[minus2, 'ma4']:
        print(ticker + ': long 포지션 종료', '\n')
        return True
    print('결론 : ' + ticker + ': long 포지션 유지')
    print()
    return False

def judge_short_terminate(data, ticker):
    minus2 = data.index[-2]

    print(ticker + ' : short 종료 판단')
    if data.loc[minus2, 'close'] > data.loc[minus2, 'ma4']:
        print(ticker + ': short 포지션 종료', '\n')
        return True
    print('결론 : ' + ticker + ': short 포지션 유지')
    print()
    return False