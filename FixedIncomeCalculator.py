from numpy import array, where, vectorize, float64 as float, ceil
import pandas as pd
import numpy as np
from scipy import optimize
from  CouponCalculator import CouponCalculator
import warnings
warnings.filterwarnings('ignore')
from scipy.optimize import  newton

def price_bond (issue, settle, mat, freq, coupon_rate, par, price,  ytm, redeem=None, daycount=None):
    ''''
    ALL calculations are based on this function:
    Inputs :
    Cr = Coupon Rate = 17
    C = Coupon = Cr* Par/m
    N = # Year = 3
    m = frequency
    I_m = YTM/m 20%/2 = 10%
    YTM = Yearly Interest rate
    n = N * m - n_before_coupon
    t = the number of days after the last payment coupon
    T = the number of days between tow coupon
    Par = Face Value
    Redeem = if it is not availebe, it is par

    P = C/ (1+ I_M)**(1-T/t)+ .... (C + par)/(1 + I_M)**(n-T/t)

    Returns:
    first: Cash Flow
    second: some important parameter
    '''
    redeem = int(where(redeem is None, par, redeem))
    settle = pd.to_datetime(settle)
    cpn_dates = CouponCalculator(issue=issue, mat=mat, freq=freq)
    I_M = ytm / freq
    cpn_dates['T'] = (cpn_dates[['Ad_cpn_date']].apply(lambda x: x.shift(-1) - x, axis=0)).shift(1) / np.timedelta64(1,'D')
    cpn_dates['Copun'] = (cpn_dates['T'] / 365) * (coupon_rate/100) * par
    remain_copun = cpn_dates[cpn_dates.Ad_cpn_date > settle]
    Next_Copun = remain_copun.iloc[0, :]['Ad_cpn_date']
    Previous_Copun = cpn_dates[cpn_dates.Ad_cpn_date < Next_Copun].iloc[-1]['Ad_cpn_date']

    if daycount is None:
        daycounter = default_daycounter
    else:
        assert daycount in daycounters, (
            "Unknown daycount {:}. {:}".format(
                daycount,
                "isda_daycounters not available"
                if no_isda else ""))
        daycounter = daycounters[daycount]
    discounting_fraction = daycounter.year_fraction(
        settle, Next_Copun) * freq
    accrual_fraction = daycounter.year_fraction(Previous_Copun, settle) * freq

    AccruedInterest = accrual_fraction * remain_copun['Copun']
    AccruedInterest = AccruedInterest.iloc[-1]

    remain_copun['Copun'].iloc[-1,] = (remain_copun.iloc[-1,]['Copun'] + redeem)

    remain_copun = remain_copun.assign(periods=range(1, remain_copun.shape[0] + 1))
    T_mean = remain_copun.iloc[:-1]['T'].mean()

    if np.abs(T_mean - remain_copun.iloc[-1, :]['T']) > 7:
        remain_copun['periods'].iloc[-1] = (remain_copun['periods'].iloc[-1] -1)  + (
                    remain_copun.iloc[-1, :]['T'] / T_mean)

    remain_copun = remain_copun.assign(Persent_values=remain_copun['Copun'] / (1 + I_M) ** remain_copun['periods'])

    dirty = (remain_copun['Persent_values'].sum()) * (1 + I_M) ** (accrual_fraction)
    Clean = dirty - AccruedInterest
    remain_copun['PV_Duration'] = (remain_copun['Copun']/((1+I_M)**(remain_copun['periods']) - accrual_fraction))
    remain_copun['Duration'] = remain_copun['PV_Duration'] * (remain_copun['periods'] - accrual_fraction)

    result = {'NextCoupon': Next_Copun, 'Previous_Copun': Previous_Copun,
              'clean_price': Clean , 'dirty_price': dirty , 'yld': ytm,
              'accrual_fraction': accrual_fraction, 'AccruedInterest': AccruedInterest }

    return remain_copun, pd.DataFrame(result, index=['result'])


def clean(issue, settle, mat, freq, coupon_rate, par, price, ytm, daycount=None):
    _, res = price_bond(issue=issue, mat=mat, settle=settle, par=par,
                        price=price, coupon_rate=coupon_rate, daycount=daycount,
                        freq=freq, ytm=ytm)

    return float(res['clean_price'].values)


def ytm(mat, settle, issue, par, price, coupon_rate, freq, daycount=None):
    function = lambda yld: clean(issue=issue, mat=mat, settle=settle, par=par, daycount=daycount,
                                 price=price, coupon_rate=coupon_rate, freq=freq, ytm=yld) - price

    return newton_wrapper(function, 0.20)
    #return optimize.newton(function, 0.20)


def bond(mat, settle, issue, par, price, coupon_rate, freq):
    yld = ytm(issue=issue, mat=mat, settle=settle, par=par,
              price=price, coupon_rate=coupon_rate,freq=freq)

    cash_flow, result = price_bond(issue=issue, mat=mat, settle=settle, par=par,
                                   price=price, coupon_rate=coupon_rate,
                                   freq=freq, ytm=yld)
    return cash_flow.T, result

def newton_wrapper(f, guess, warn=True):
    r"""Wrapper for `scipy.optimize.newton` to return root or `nan`

    Parameters
    ----------
    f : callable
        The function whose zero is to be found
    guess : float
        An initial estimate of the zero somewhere near the actual zero.
    warn : bool, Optional
        If true, a warning is issued when returning nan.
        This happens when `scipy.optimize.newton` does not converge.
"""

    root, status = newton(f, guess, full_output=True, disp=False)
    if status.converged:
        return root
    else:
        if warn:
            from warnings import warn
            warn("Newton root finder did not converge. Returning nan")
        return np.nan

def convexity_effective(mat, settle, issue, par, price, coupon_rate, freq, dy=0.001, yld=0.001):
    # def bond_convexity(price, par, T, coup, freq, dy=0.001):

    yld = ytm(issue=issue, mat=mat, settle=settle, par=par,
              price=price, coupon_rate=coupon_rate, freq=freq)

    ytm_minus = yld - dy
    price_minus = clean(issue=issue, mat=mat, settle=settle, par=par,
                        price=price, coupon_rate=coupon_rate,
                        freq=freq, ytm=ytm_minus)

    ytm_plus = yld + dy
    price_plus = clean(issue=issue, mat=mat, settle=settle, par=par,
                       price=price, coupon_rate=coupon_rate,
                       freq=freq, ytm=ytm_plus)

    convexity = (price_minus + price_plus - 2 * price) / (2 * price * dy ** 2)
    return convexity


def macauly_duration(mat, settle, issue, par, price, coupon_rate, freq):
    
    cash_flow, _ = bond(issue=issue, mat=mat, settle=settle, par=par, price=price, coupon_rate=coupon_rate, freq=freq)
    
    return (cash_flow.loc['Duration'].sum() / cash_flow.loc['PV_Duration'].sum())/freq
    


def effective_duration(mat, settle, issue, par, price, coupon_rate, freq, dy=0.001):
    yld = ytm(issue=issue, mat=mat, settle=settle, par=par,
              price=price, coupon_rate=coupon_rate, freq=freq)

    ytm_minus = yld - dy

    price_minus = clean(issue=issue, mat=mat, settle=settle, par=par,
                        price=price, coupon_rate=coupon_rate,
                        freq=freq, ytm=ytm_minus)

    ytm_plus = yld + dy

    price_plus = clean(issue=issue, mat=mat, settle=settle, par=par,
                       price=price, coupon_rate=coupon_rate,
                       freq=freq, ytm=ytm_plus)

    mduration = (price_minus - price_plus) / (2 * price * dy)
    return mduration


def all_bond(mat, settle, issue, par, price, coupon_rate, freq, dy=0.001):
    yld = ytm(issue=issue, mat=mat, settle=settle, par=par,
              price=price, coupon_rate=coupon_rate, freq=freq)

    modified_duration_ = effective_duration(issue=issue, mat=mat, settle=settle, par=par,
                                            price=price, coupon_rate=coupon_rate, freq=freq)

    macauly_duration_ = macauly_duration(issue=issue, mat=mat, settle=settle, par=par,
                                         price=price, coupon_rate=coupon_rate, freq=freq)

    convexity_effective_ = convexity_effective(issue=issue, mat=mat, settle=settle, par=par,
                                               price=price, coupon_rate=coupon_rate,
                                               freq=freq, yld=yld, dy=dy)

    return modified_duration_, macauly_duration_, convexity_effective_, yld

def zero_coupon_bond_price(par, ytm, settle, maturity):
    settle = pd.to_datetime(settle)
    maturity = pd.to_datetime(maturity)

    T = (maturity - settle) / np.timedelta64(1, 'Y')

    return par / ((1 + ytm) ** T)
    


def zero_coupon_bond_yield(par, price, settle, maturity):
    settle = pd.to_datetime(settle)
    maturity = pd.to_datetime(maturity)
    T = (maturity - settle) / np.timedelta64(1, 'Y')

    return ((par / price) ** (1 / T)) - 1


def zero_effective_duration(mat, settle, par, price, dy=0.001):
    yld = zero_coupon_bond_yield(par=par, price=price, settle=settle, maturity=mat)

    ytm_minus = yld - dy

    price_minus = zero_coupon_bond_price(par= par, ytm=ytm_minus, settle=settle, maturity=mat)

    ytm_plus = yld + dy

    price_plus = zero_coupon_bond_price(par= par, ytm=ytm_plus, settle=settle, maturity=mat)

    mduration = (price_minus - price_plus) / (2 * price * dy)
    return mduration


def zero_convexity_effective(mat, settle, par, price, dy=0.001):
    yld = zero_coupon_bond_yield(par=par, price=price, settle=settle, maturity=mat)
    ytm_minus = yld - dy

    price_minus = zero_coupon_bond_price(par= par, ytm=ytm_minus, settle=settle, maturity=mat)
    ytm_plus = yld + dy
    price_plus = zero_coupon_bond_price(par= par, ytm=ytm_plus, settle=settle, maturity=mat)

    convexity = (price_minus + price_plus - 2 * price) / (2 * price * dy ** 2)
    return convexity


# def _import_isda_daycounters():
#     r"""Import isda_daycounters. Could raise ImportError
#     Returns
#     -------
#     daycounters : dict
#          keys are the names of the daycounters, values are the classes
#     default_daycounter : daycounter
#          thirty360
#     no_isda : bool
#          Whether isda_daycounters unavailable (False)
#     """
#     from isda_daycounters import (actual360, actual365,
#                                   actualactual, thirty360,
#                                   thirtyE360, thirtyE360ISDA)
#     daycounters = {x.name: x for x in (actual360, actual365,
#                                        actualactual, thirty360,
#                                        thirtyE360, thirtyE360ISDA)}
#     default_daycounter = thirty360
#     no_isda = False
#     return daycounters, default_daycounter, no_isda


# def _make_simple_day_counter():
#     r"""Create a simple daycounter (basically ACT/365)
#     Returns
#     -------
#     daycounters : dict
#          only key is 'simple', value is SimpleDayCount
#     default_daycounter : daycounter
#          SimpleDayCount
#     no_isda : bool
#          Whether isda_daycounters available (True)
#     """

#     class SimpleDayCount:
#         def day_count(start_date, end_date):
#             return (end_date - start_date).days

#         def year_fraction(start_date, end_date):
#             return (end_date - start_date).days / 365.0

#     daycounters = {'simple': SimpleDayCount}
#     default_daycounter = SimpleDayCount
#     no_isda = True
#     from warnings import warn
#     warn("Module isda_daycounters is not installed.\n"
#          "Only 'simple' daycount (basically ACT/365) is available.\n"
#          "To use other daycounts, install isda_daycounters from\n"
#          "https://github.com/miradulo/isda_daycounters")
#     return daycounters, default_daycounter, no_isda


# try:
#     daycounters, default_daycounter, no_isda = _import_isda_daycounters()
# except ImportError:
#     daycounters, default_daycounter, no_isda = _make_simple_day_counter()