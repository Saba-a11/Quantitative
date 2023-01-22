import pandas as pd
import numpy as np
from persiantools.jdatetime import JalaliDate
import pyodbc as pyodbc

def _edate_0(dt, m):
    return pd.to_datetime(dt) + pd.tseries.offsets.DateOffset(months=m)
_edate = np.vectorize(_edate_0)

def edate(dt, m):
    return _edate(dt, np.array(m))[()]

def Cpn_Create_date(issue,mat, freq ):
    '''
    issue date in Jalali format, e.g., '1401/11/02'
    maturity date in Jalali format, e.g., '1401/11/02'
    freq is frequency, e.g., 1,2,3,4,6,12 
    '''
    year_i, month_i, day_i = int(issue[0:4]), int(issue[5:7]), int(issue[8:10])
    year_m, month_m, day_m = int(mat[0:4]), int(mat[5:7]), int(mat[8:10])
    month = int(month_i)
    day = int(day_i)
    year = int(year_i)
    month_freq = int(12/ freq)
    cpn_date = {}
    extra_days = 0
    i= 0
    while (JalaliDate(year_m, month_m, day_m) - JalaliDate(year, month, day)).days> 6:
        month +=month_freq
        if month > 12:
            month = month - 12
            year += 1
        if  ( (month > 6) and (month !=12)) and (day_i == 31) :
            day = 30
        elif ((month<7) and (month!=12) and (day_i==30)):
            day= 31
        elif (month ==12) and (day_i in (31, 30)) :
            day = 29
        else : day = day_i

        if (JalaliDate(year_m, month_m, day_m) - JalaliDate(year, month, day)).days < 6 :
            extra_days = (JalaliDate(year_m, month_m, day_m) - JalaliDate(year, month, day)).days
            break

        Ad_cpn_date = JalaliDate(year, month, day).to_gregorian()
        Jli_cpn_date = JalaliDate(year, month, day)
        cpn_date[i] = (Ad_cpn_date, Jli_cpn_date)
        i += 1

    cpn_date[i+1] = (JalaliDate(year_m, month_m, day_m).to_gregorian(), JalaliDate(year_m, month_m, day_m))
    cpn_date[i+2] = (JalaliDate(year_i, month_i, day_i).to_gregorian(), JalaliDate(year_i, month_i, day_i))

    data = pd.DataFrame(list(cpn_date.values()), columns=['Ad_cpn_date', 'Jli_cpn_date'])
    data [ 'extra_days'] = extra_days
    data.sort_values('Ad_cpn_date', inplace = True)
    data.reset_index(drop = True, inplace= True)
    return data[['Ad_cpn_date', 'Jli_cpn_date']]

print(Cpn_Create_date('1401/10/25', '1411/06/20', 6))

