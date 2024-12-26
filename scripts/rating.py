import sys
import os
import yfinance as yf
from datetime import datetime, timedelta


def fetch_alpha_beta(ticker):
    alpha = None
    beta = None

    try:
        stock = yf.Ticker(ticker)
        sp500 = yf.Ticker("^GSPC")

        end_date = datetime.today()
        start_date = end_date - timedelta(days=30)

        stock_history = stock.history(start=start_date, end=end_date)
        sp500_history = sp500.history(start=start_date, end=end_date)

        stock_returns = stock_history["Close"].pct_change().dropna()
        sp500_returns = sp500_history["Close"].pct_change().dropna()

        if len(stock_returns) > 1 and len(sp500_returns) > 1:
            covariance = stock_returns.cov(sp500_returns)
            variance = sp500_returns.var()
            beta = covariance / variance if variance != 0 else 0

            stock_cumulative_return = stock_returns.add(1).prod() - 1
            sp500_cumulative_return = sp500_returns.add(1).prod() - 1
            alpha = (stock_cumulative_return - sp500_cumulative_return) * 100

    except Exception:
        pass

    return alpha, beta

def fetch_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d").tail(1)['Close'].iloc[0]
        info = stock.info

        alpha, beta = fetch_alpha_beta(ticker)

        # Placeholder logic for unavailable metrics
        free_cash_flow_growth = info.get("freeCashflow", 0)  # Replace with actual key if available
        revenue_growth = info.get("revenueGrowth", 0)
        earnings_growth = info.get("earningsGrowth", 0)

        # Example fallback calculations (if required)
        if free_cash_flow_growth and revenue_growth:
            free_cash_flow_growth = (free_cash_flow_growth / revenue_growth) * 100

        return {
            "name": info.get("shortName", "Unknown Name"),
            "price": price,
            "pe_ratio": info.get("trailingPE"),
            "alpha": alpha,
            "beta": beta,
            "moving_avg_50": info.get("fiftyDayAverage"),
            "moving_avg_200": info.get("twoHundredDayAverage"),
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "dividend_yield": info.get("dividendYield"),
            "debt_to_equity": info.get("debtToEquity"),
            "free_cash_flow_growth": free_cash_flow_growth
        }
    except Exception as e:
        raise ValueError(f"Error fetching data for ticker '{ticker}': {e}")

def score_short_term(stock_data):
    # Calculates short-term score
    score = 50
    beta = stock_data.get("beta", 0)
    if beta:
        score += 15 * beta if beta > 0 else -15 * abs(beta)  # Reward or punish based on Beta

    price = stock_data.get("price", 0)
    moving_avg_50 = stock_data.get("moving_avg_50", 0)
    if moving_avg_50 and price:
        score += 10 * (price / moving_avg_50 - 1)  # Momentum boost

    # Penalize high short-term volatility (optional, if available)
    volatility = stock_data.get("volatility", 0)
    if volatility > 0.05:  # Threshold for significant volatility
        score -= 10 * volatility  # Penalty

    return round(max(1, min(100, score)), 2)


def score_long_term(stock_data):
    score = 50

    alpha = stock_data.get("alpha", 0)
    if alpha:
        score += alpha / 6

    pe_ratio = stock_data.get("pe_ratio", 0)
    if pe_ratio and isinstance(pe_ratio, int): #fix bug as one of the pe_ratios came out as a string
        if pe_ratio < 15:
            score += 20
        elif pe_ratio > 30:
            score -= 15

    price = stock_data.get("price", 0)
    moving_avg_200 = stock_data.get("moving_avg_200", 0)
    moving_avg_50 = stock_data.get("moving_avg_50", 0)

    if moving_avg_200 and price:
        score += 15 * (price / moving_avg_200 - 1)

    if moving_avg_50 and price:
        score += 5 * (price / moving_avg_50 - 1)

    revenue_growth = stock_data.get("revenue_growth", 0)
    if revenue_growth:
        score += 15 * revenue_growth

    earnings_growth = stock_data.get("earnings_growth", 0)
    if earnings_growth:
        score += min(8 * earnings_growth, 30)

    dividend_yield = stock_data.get("dividend_yield", 0)
    if dividend_yield is not None:
        score += dividend_yield * 10

    debt_to_equity = stock_data.get("debt_to_equity", None)
    if debt_to_equity is not None:
        if debt_to_equity < 1:
            score += 5
        elif debt_to_equity > 2:
            score -= 10
            
    return round(max(1, min(100, score)), 2)



def evaluate_tickers(tickers):
    results = []

    for ticker in tickers:
        try:
            stock_data = fetch_data(ticker)
            short_term_score = score_short_term(stock_data)
            long_term_score = score_long_term(stock_data)

            results.append((stock_data.get("name", "Unknown Name"), ticker, short_term_score, long_term_score))

        except ValueError:
            pass

    results.sort(key=lambda x: x[3], reverse=True)

    print("\nFinal Rankings:")
    for i, (name, ticker, short_term_score, long_term_score) in enumerate(results, start=1):
        print(f"#{i}: {name:<35} Ticker: {ticker:<6} Short-Term Score: {short_term_score:<6} Long-Term Score: {long_term_score:<6}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("Input a number and press enter:")
        print("1: Penny Stocks")
        print("2: Small Cap Stocks")
        print("3: Big Tech Stocks")
        print("4: Info on Metrics and Weighing")
        choice = input("Your choice: ")

    if choice == "1":
        tickers_to_evaluate = [
            "ABEV", "ABVE", "ACHR", "ADTX", "AEMD", "AFRM", "AGIO", "ALUR", "AMLI",
            "AMPG", "AMRN", "ANTE", "APDN", "APLT", "APTO", "AQST", "ASII",
            "ATHA", "ATUS", "BBAI", "BB", "BFLY", "BITF", "BNGO",
            "BPTH", "BTE", "BTBT", "BTG", "BURU", "CALA", "CAN", "CARA", "CBAT",
            "CHPT", "CLOV", "CMRX", "CNTX", "CRCW",
            "CRIS", "CRLBF", "CRSP", "CTM", "CUTR", "CUE", "CYBN", "DIDIY", "DNN",
            "DNA", "DOCU", "DVAX", "EDBL", "EOSE", "ENSC", "ESPR", "EXAS", "FCEL",
            "FGEN", "FLGT", "FRSX", "GILD", "GLGI", "GOEV", "GOSS", "GSAT",
            "HAO", "HIRU", "HMBL", "ICCT", "ICCM", "IQ", "IPHA",
            "INVZ", "IONS", "JDZG", "JKS", "JOB", "KPTI", "KUKE", "KULR", "LAC",
            "LAES", "LDTC", "LICN", "LITM", "LOGC", "LOOP", "LPSN", "LTRY", "LUCD",
            "LYFT", "MBRX", "MLGO", "MNKD", "MRMD", "MNTK", "MVIS", "MYNA",
            "NEGG", "NIO", "NKLA", "NMHI", "NNAX", "OCGN", "OGI", "ONMD", "OPEN",
            "OPK", "OPTT", "PACB", "PALT", "PED", "PHIL", "PLUG", "PRLD", "PRTA",
            "PSTX", "QNRX", "QSI", "RCEL", "RIG", "RIME", "RONN", "RVMD", "RYCEY",
            "SENS", "SES", "SGMO", "SIDU", "SPI", "SRMX", "SVMH", "TANH", "TNEYF",
            "TLRY", "TOVX", "TPET", "TRX", "UAMY", "URG", "VCIG", "VEEE",
            "VSTE", "VXRT", "WFSTF", "WKHS", "XELB", "XHG", "XIACF", "XTIA", "XXII",
            "ZNOG"
        ] 
    elif choice == "2":
        tickers_to_evaluate = [
            "ACLS", "AFRM", "AGEN", "AGIO", "AKRO", "ALKS", "ALVR", "AMKR", "ANIK", "APLS",
            "APP", "ARQT", "ASRT", "ATEN", "ATRA", "AXGN", "BCYC", "BEAM", "BMRN", "BLUE",
            "BLZE", "CALM", "CARA", "CDNA", "CELH", "CLDX", "CLNE", "CLOV", "CMBM", "CMTL",
            "CNDT", "CODX", "COUR", "CRSP", "CRVS", "CTMX", "CUE", "CUTR", "CYRX",
            "DAKT", "DAWN", "DENN", "DERM", "DGII", "DNA", "DNN", "DVAX", "EDIT", "ENTA",
            "EOLS", "EXAS", "FATE", "FGEN", "FIP", "FLGT", "FOLD", "FRSH", "GAN",
            "GILD", "GLTO", "GMAB", "GOSS", "HRTX", "IBRX", "INO", "IONS", "ITRI",
            "JBLU", "JKS", "KPTI", "LESL", "LGVN", "LIVN", "LOGC", "MCRB", "MNKD", "MNTK",
            "MRVI", "NTLA", "OCGN", "OPK", "OSUR", "PACB", "PRTA", "PTCT", "QURE", "RGEN",
            "RIGL", "RLMD", "RMNI", "RVMD", "SEER", "SERV", "SGMO", "SHPH", "PM"
        ]
    elif choice == "3":
        tickers_to_evaluate = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "NVDA", "META", "ADBE", "ORCL", "INTC",
            "CRM", "CSCO", "QCOM", "AMD", "IBM",
            "SAP", "SHOP", "UBER", "SQ", "PYPL",
            "PLTR", "SNOW", "ASML", "SPOT", "ZM",
            "LYFT", "DOCU", "CRWD", "NET", "FSLY"
    ]
    elif choice == "4":
        print()
        print("Scoring Factors for Short-Term Score:")
        print("- Beta: (Weighing: High) Beta is a measure of an asset's volatility relative to the overall market.\n It is calculated as the ratio of the covariance of the asset's returns with the market's returns to the variance of the market's returns.")
        print("- Price / 50-Day Moving Average: (Weighing: Medium) Captures short-term momentum.")
        print("Volatility: (Weighing: Medium) Penalizes high short-term volatility to reduce risk.")
        print()
        print("Scoring Factors for Long-Term Score:")
        print("- Alpha: (Weighing: Medium) Measures performance relative to market benchmark.")
        print("- Price/Earnings Ratio: (Weighing: Medium) Rewards low P/E (<15), penalizes high P/E (>30).")
        print("- Price / 200-Day Moving Average: (Weighing: High) Indicates long-term trends.")
        print("- Price / 50-Day Moving Average: (Weighing: Medium) Indicates shorter-term trends for context.")
        print("- Revenue Growth: (Weighing: Medium) Rewards consistent revenue growth.")
        print("- Earnings Growth: (Weighing: High) Rewards consistent earnings growth.")
        print("- Dividend Yield: (Weighing: Medium) Rewards companies paying dividends.")
        print("- Debt-to-Equity Ratio: (Weighing: Medium) Rewards low debt (<1) and penalizes high debt (>2).\n")
    elif choice == "5":
        tickers_input = input("Enter custom ticker symbols separated by commas: ").strip()
        tickers_to_evaluate = [ticker.strip().upper() for ticker in tickers_input.split(",")]
        evaluate_tickers(tickers_to_evaluate)
    else:
        print("Invalid choice. Exiting.")
        exit()

    if choice in ["1", "2", "3"]:
        evaluate_tickers(tickers_to_evaluate)
