import pandas as pd
import numpy as np
from persiantools.jdatetime import JalaliDate
import pyodbc as pyodbc

def _edate_0(dt, m):
    return pd.to_datetime(dt) + pd.tseries.offsets.DateOffset(months=m)
_edate = np.vectorize(_edate_0)

def edate(dt, m):
    return _edate(dt, np.array(m))[()]

def Cpn_Create_date(IssueDate,MaturityDate, Frequency ):
    '''
    IssueDdate in Jalali format, e.g., '1401/11/02'
    MaturityDate in Jalali format, e.g., '1401/11/02'
    Frequency must be in valid amount, e.g., 1,2,3,4,6,12
    '''
    YearIssue, MonthIssue, DayIssue = int(IssueDate[0:4]), int(IssueDate[5:7]), int(IssueDate[8:10])
    YearMat, MonthMat, DayMat = int(MaturityDate[0:4]), int(MaturityDate[5:7]), int(MaturityDate[8:10])
    month = int(MonthIssue)
    day = int(DayIssue)
    year = int(YearIssue)
    MonthFreq = int(12/ Frequency)
    CpnDate = {}
    extra_days = 0
    i= 0
    while (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(year, month, day)).days> 6:
        month +=MonthFreq
        if month > 12:
            month = month - 12
            year += 1
        if  ( (month > 6) and (month !=12)) and (DayIssue == 31) :
            day = 30
        elif ((month<7) and (month!=12) and (DayIssue==30)):
            day= 31
        elif (month ==12) and (DayIssue in (31, 30)) :
            day = 29
        else : day = DayIssue

        if (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(year, month, day)).days < 6 :
            extra_days = (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(year, month, day)).days
            break

        MiladiCpnDate = JalaliDate(year, month, day).to_gregorian()
        JalaliCpnDate = JalaliDate(year, month, day)
        CpnDate[i] = (MiladiCpnDate, JalaliCpnDate)
        i += 1

    CpnDate[i+1] = (JalaliDate(YearMat, MonthMat, DayMat).to_gregorian(), JalaliDate(YearMat, MonthMat, DayMat))
    CpnDate[i+2] = (JalaliDate(YearIssue, MonthIssue, DayIssue).to_gregorian(), JalaliDate(YearIssue, MonthIssue, DayIssue))

    Coupons = pd.DataFrame(list(CpnDate.values()), columns=['MiladiCpnDate', 'JalaliCpnDate'])
    Coupons [ 'extra_days'] = extra_days
    Coupons.sort_values('MiladiCpnDate', inplace = True)
    Coupons.reset_index(drop = True, inplace= True)
    return Coupons[['MiladiCpnDate', 'JalaliCpnDate']]

print(Cpn_Create_date('1401/10/25', '1411/06/20', 6))

