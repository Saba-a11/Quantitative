import pandas as pd
import numpy as np
from persiantools.jdatetime import JalaliDate

def Cpn_Create_date(IssueDate,MaturityDate, Frequency ):
    '''
    IssueDdate in Jalali format, e.g., '1401/11/02'
    MaturityDate in Jalali format, e.g., '1401/11/02'
    Frequency must be in valid amount, e.g., 1,2,3,4,6,12
    '''
    YearIssue, MonthIssue, DayIssue = int(IssueDate[0:4]), int(IssueDate[5:7]), int(IssueDate[8:10])
    YearMat, MonthMat, DayMat = int(MaturityDate[0:4]), int(MaturityDate[5:7]), int(MaturityDate[8:10])
        
    YearStart = int(YearIssue)
    MonthStart = int(MonthIssue)
    DayStart = int(DayIssue)
    MonthFreq = int(12/ Frequency)
      
    CpnDate = {}
    extra_days = 0
    i= 0

    while (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(YearStart, MonthStart, DayStart)).days> 6:
        MonthStart +=MonthFreq
        if MonthStart > 12:
            MonthStart = MonthStart - 12
            YearStart += 1
        if  ( (MonthStart > 6) and (MonthStart !=12)) and (DayIssue == 31) :
            DayStart = 30
        elif ((MonthStart<7) and (MonthStart!=12) and (DayIssue==30)):
            DayStart= 31
        elif (MonthStart ==12) and (DayIssue in (31, 30)) :
            DayStart = 29
        else : DayStart = DayIssue
        if (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(YearStart, MonthStart, DayStart)).days < 6 :
            extra_days = (JalaliDate(YearMat, MonthMat, DayMat) - JalaliDate(YearStart, MonthStart, DayStart)).days
            break
        MiladiCpnDate = JalaliDate(YearStart, MonthStart, DayStart).to_gregorian()
        JalaliCpnDate = JalaliDate(YearStart, MonthStart, DayStart)
        CpnDate[i] = (MiladiCpnDate, JalaliCpnDate)
        i += 1

    CpnDate[i+1] = (JalaliDate(YearMat, MonthMat, DayMat).to_gregorian(), JalaliDate(YearMat, MonthMat, DayMat))
    CpnDate[i+2] = (JalaliDate(YearIssue, MonthIssue, DayIssue).to_gregorian(), JalaliDate(YearIssue, MonthIssue, DayIssue))
    Coupons = pd.DataFrame(list(CpnDate.values()), columns=['MiladiCpnDate', 'JalaliCpnDate'])
    Coupons [ 'extra_days'] = extra_days
    Coupons.sort_values('MiladiCpnDate', inplace = True)
    Coupons.reset_index(drop = True, inplace= True)
    return Coupons[['MiladiCpnDate', 'JalaliCpnDate']]

# print(Cpn_Create_date('1401/10/30', '1411/06/20', 6))

