"""Forecasting model library shared by scripts 07-09.
Every model: fn(train_series, h) -> forecast pd.Series (month-start index)."""
import itertools
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

warnings.filterwarnings("ignore")
SP = 12


def future_index(s, h):
    return pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")


def _ser(vals, s, h):
    return pd.Series(np.asarray(vals, dtype=float), index=future_index(s, h))


def naive(s, h): return _ser([s.iloc[-1]] * h, s, h)
def snaive(s, h): return _ser(np.resize(s.iloc[-SP:].values, h), s, h)
def ses(s, h): return _ser(SimpleExpSmoothing(s, initialization_method="estimated").fit().forecast(h), s, h)


def _hw(s, h, trend, damped, seasonal):
    r = ExponentialSmoothing(s, trend=trend, damped_trend=damped, seasonal=seasonal, seasonal_periods=SP,
                             initialization_method="estimated").fit()
    return _ser(r.forecast(h), s, h)


def hw_add_damped(s, h): return _hw(s, h, "add", True, "add")      # the project's "Holt-Winters (additive)"
def hw_add(s, h): return _hw(s, h, "add", False, "add")            # undamped additive trend
def hw_mul(s, h): return _hw(s, h, None, False, "mul")             # multiplicative seasonality, no trend
def hw_mul_damped(s, h): return _hw(s, h, "add", True, "mul")      # damped trend, multiplicative seasonality
def arima111(s, h): return _ser(ARIMA(s, order=(1, 1, 1)).fit().forecast(h), s, h)


def sarima_fixed(s, h):
    r = SARIMAX(s, order=(1, 1, 1), seasonal_order=(0, 1, 1, SP)).fit(disp=False)
    return _ser(r.forecast(h), s, h)


SARIMA_GRID = [(p, 1, q, P, 1, Q) for p, q, P, Q in itertools.product([0, 1], [0, 1], [0, 1], [0, 1])]


def sarima_search(s, h, return_order=False):
    """Small AIC-guided search: d=D=1, p,q,P,Q in {0,1} (16 candidates). Lowest AIC wins."""
    best = None
    for p, d, q, P, D, Q in SARIMA_GRID:
        try:
            r = SARIMAX(s, order=(p, d, q), seasonal_order=(P, D, Q, SP)).fit(disp=False, maxiter=100)
            if np.isfinite(r.aic) and (best is None or r.aic < best[0]):
                best = (r.aic, (p, d, q, P, D, Q), r)
        except Exception:
            continue
    if best is None:
        raise RuntimeError("no SARIMA candidate converged")
    f = _ser(best[2].forecast(h), s, h)
    return (f, best[1]) if return_order else f


ETS_CONFIGS = [(None, False, "add"), (None, False, "mul"), ("add", True, "add"), ("add", True, "mul")]


def ets_auto(s, h, return_cfg=False):
    """ETS(A,.,.) family chosen by AICc among 4 configs (A,N,A) (A,N,M) (A,Ad,A) (A,Ad,M)."""
    best = None
    for tr, dp, se in ETS_CONFIGS:
        try:
            r = ETSModel(s, error="add", trend=tr, damped_trend=dp, seasonal=se, seasonal_periods=SP,
                         initialization_method="estimated").fit(disp=False, maxiter=200)
            if np.isfinite(r.aicc) and (best is None or r.aicc < best[0]):
                best = (r.aicc, (tr, dp, se), r)
        except Exception:
            continue
    if best is None:
        raise RuntimeError("no ETS candidate converged")
    f = _ser(best[2].forecast(h), s, h)
    return (f, best[1]) if return_cfg else f


MODELS = {
    "Seasonal naive": snaive,
    "Naive": naive,
    "SES": ses,
    "Holt-Winters additive (damped)": hw_add_damped,
    "Holt-Winters additive (undamped)": hw_add,
    "Holt-Winters multiplicative": hw_mul,
    "Holt-Winters mult. seasonal + damped trend": hw_mul_damped,
    "ETS (AICc-selected)": ets_auto,
    "ARIMA(1,1,1)": arima111,
    "SARIMA(1,1,1)(0,1,1,12)": sarima_fixed,
    "SARIMA (AIC search)": sarima_search,
}


def metrics(actual, pred, train):
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    e = a - p
    scale = np.mean(np.abs(train.values[SP:] - train.values[:-SP]))    # in-sample seasonal-naive MAE
    return {"MAE": np.mean(np.abs(e)), "RMSE": np.sqrt(np.mean(e ** 2)),
            "MAPE": np.mean(np.abs(e) / a) * 100,
            "sMAPE": np.mean(2 * np.abs(e) / (np.abs(a) + np.abs(p))) * 100,
            "MASE": np.mean(np.abs(e)) / scale}


def intervals(model_fn, s, h, reps=2000, seed=42):
    """Point forecast plus 80%/95% bounds. Residual-bootstrap simulation for exponential smoothing
    (ExponentialSmoothing.simulate with bootstrapped errors); model-based (Gaussian) for SARIMA;
    seasonal-naive uses empirical quantiles of in-sample 12-month differences."""
    rng = np.random.default_rng(seed)
    idx = future_index(s, h)
    if model_fn is sarima_fixed or model_fn is sarima_search:
        if model_fn is sarima_search:
            _, o = sarima_search(s, h, True)
        else:
            o = (1, 1, 1, 0, 1, 1)
        r = SARIMAX(s, order=o[:3], seasonal_order=(o[3], o[4], o[5], SP)).fit(disp=False)
        g = r.get_forecast(h)
        f = g.predicted_mean.values
        c80, c95 = g.conf_int(alpha=.2).values, g.conf_int(alpha=.05).values
        out = pd.DataFrame({"forecast": f, "lower_80": c80[:, 0], "upper_80": c80[:, 1],
                            "lower_95": c95[:, 0], "upper_95": c95[:, 1]}, index=idx)
        return out.clip(lower=0), "model-based (Gaussian) interval"
    if model_fn is snaive:
        d = (s.values[SP:] - s.values[:-SP])
        f = snaive(s, h).values
        q = lambda a: np.quantile(d, a)
        out = pd.DataFrame({"forecast": f, "lower_80": f + q(.1), "upper_80": f + q(.9),
                            "lower_95": f + q(.025), "upper_95": f + q(.975)}, index=idx)
        return out.clip(lower=0), "empirical quantiles of 12-month differences"
    cfg = {hw_add_damped: ("add", True, "add"), hw_add: ("add", False, "add"), hw_mul: (None, False, "mul"),
           hw_mul_damped: ("add", True, "mul")}
    if model_fn not in cfg:
        raise ValueError("no interval method for this model")
    tr, dp, se = cfg[model_fn]
    r = ExponentialSmoothing(s, trend=tr, damped_trend=dp, seasonal=se, seasonal_periods=SP,
                             initialization_method="estimated").fit()
    sims = np.asarray(r.simulate(h, repetitions=reps, error="add", random_errors="bootstrap",
                                 anchor="end", random_state=rng))
    f = np.asarray(r.forecast(h))
    out = pd.DataFrame({"forecast": f, "lower_80": np.quantile(sims, .1, axis=1), "upper_80": np.quantile(sims, .9, axis=1),
                        "lower_95": np.quantile(sims, .025, axis=1), "upper_95": np.quantile(sims, .975, axis=1)}, index=idx)
    return out.clip(lower=0), "residual-bootstrap simulation (2,000 paths)"
