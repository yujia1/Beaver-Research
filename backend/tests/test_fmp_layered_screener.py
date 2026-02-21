import pytest

from services.market import fmp_layered_screener as screener


class Dummy:
    pass


def make_km(currentRatio=1.2, interestBurden=3.0, netDebtToEBITDA=1.0, freeCashFlow=1000,
            capexToRevenue=0.03, stockBasedCompensationToRevenue=0.01, freeCashFlowYield=0.06,
            evToEbitda=10.0, earningsYield=0.05, epsDilutedGrowth=0.1, roic=0.15,
            grossProfitMargin=0.4, operatingProfitMargin=0.2):
    return [{
        "currentRatio": currentRatio,
        "interestBurden": interestBurden,
        "netDebtToEBITDA": netDebtToEBITDA,
        "freeCashFlow": freeCashFlow,
        "capexToRevenue": capexToRevenue,
        "stockBasedCompensationToRevenue": stockBasedCompensationToRevenue,
        "freeCashFlowYield": freeCashFlowYield,
        "evToEbitda": evToEbitda,
        "earningsYield": earningsYield,
        "epsDilutedGrowth": epsDilutedGrowth,
        "returnOnInvestedCapital": roic,
        "grossProfitMargin": grossProfitMargin,
        "operatingProfitMargin": operatingProfitMargin
    }]


def make_income(netIncome=100, weightedAverageShsOut=1):
    return [{"netIncome": netIncome, "weightedAverageShsOut": weightedAverageShsOut}]


def make_cashflow(freeCashFlow=100, operatingCashFlow=120, depreciationAndAmortization=10):
    return [{"freeCashFlow": freeCashFlow, "operatingCashFlow": operatingCashFlow, "depreciationAndAmortization": depreciationAndAmortization}]


def make_balance(longTermDebt=0, shortTermDebt=0, cashAndCashEquivalents=0):
    return [{"longTermDebt": longTermDebt, "shortTermDebt": shortTermDebt, "cashAndCashEquivalents": cashAndCashEquivalents}]


def test_layered_screener_survival_fail(monkeypatch):
    # Prepare data where currentRatio < 1 triggers survival fail
    km = make_km(currentRatio=0.8, freeCashFlow=-50)
    inc = make_income(netIncome=10)
    cf = make_cashflow(freeCashFlow=-50)
    bs = make_balance(longTermDebt=100, shortTermDebt=0, cashAndCashEquivalents=0)

    monkeypatch.setattr(screener, 'fetch_key_metrics', lambda s, limit=5, period='FY': km)
    monkeypatch.setattr(screener, 'fetch_income_statement', lambda s, years=5: inc)
    monkeypatch.setattr(screener, 'fetch_cash_flow_statement', lambda s, years=5: cf)
    monkeypatch.setattr(screener, 'fetch_balance_sheet', lambda s, years=5: bs)
    monkeypatch.setattr(screener, 'fetch_stock_quote', lambda s: {"price": 10})

    result = screener.run_layered_screener('DUMMY', limit=1, period='FY')

    assert result['ticker'] == 'DUMMY'
    assert result['survival_filter']['pass'] is False
    assert result['action']['recommendation'] == 'Avoid'


def test_layered_screener_buy_case(monkeypatch):
    # Prepare healthy company with high FCF yield to get Buy recommendation
    km = make_km(currentRatio=2.0, freeCashFlow=1000, freeCashFlowYield=0.06)
    inc = make_income(netIncome=100, weightedAverageShsOut=1)
    cf = make_cashflow(freeCashFlow=1000)
    bs = make_balance(longTermDebt=0, shortTermDebt=0, cashAndCashEquivalents=0)

    monkeypatch.setattr(screener, 'fetch_key_metrics', lambda s, limit=5, period='FY': km)
    monkeypatch.setattr(screener, 'fetch_income_statement', lambda s, years=5: inc)
    monkeypatch.setattr(screener, 'fetch_cash_flow_statement', lambda s, years=5: cf)
    monkeypatch.setattr(screener, 'fetch_balance_sheet', lambda s, years=5: bs)
    monkeypatch.setattr(screener, 'fetch_stock_quote', lambda s: {"price": 10})

    result = screener.run_layered_screener('GOOD', limit=1, period='FY')

    assert result['ticker'] == 'GOOD'
    # Survival should pass
    assert result['survival_filter']['pass'] is True
    # Recommendation should be Buy because high FCF yield
    assert result['action']['recommendation'] in ('Buy', 'Watch')
