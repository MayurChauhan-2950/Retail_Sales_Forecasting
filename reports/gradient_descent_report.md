# Optimisation: Gradient Descent vs Closed Form (Ch7)

Data: 48 monthly sales totals; model `sales = slope * month_index + intercept`.
Both variables standardised first (z-score), learning rate 0.1, 200 epochs, starting from w=0, b=0.

## Parameters and MSE
| method | slope_$_per_month | intercept_$ | MSE_original_units |
|---|---|---|---|
| Gradient descent | 902.0075 | 26,661.1742 | 465,460,447.0807 |
| Closed form (normal equation) | 902.0075 | 26,661.1742 | 465,460,447.0807 |
| np.polyfit (check) | 902.0075 | 26,661.1742 | 465,460,447.0807 |

- Scaled-space MSE: gradient descent 0.748802 vs closed form 0.748802 (difference 0.00e+00)
- Loss within 1e-6 of the optimum after about 28 epochs
- Trend line R^2 = 0.251; RMSE = 21,574.53 $ (the linear trend alone ignores seasonality)
- Interpretation: sales grow by about $902.01 per month on average.

## Learning-rate experiment (final loss after 200 epochs, scaled data)
| learning_rate | final_loss | outcome |
|---|---|---|
| 0.001 | 0.862 | converging slowly |
| 0.01 | 0.7489 | converged |
| 0.1 | 0.7488 | converged |
| 0.5 | 0.7488 | converged |
| 1.05 | 7,486,962,558,521,216 | DIVERGED |

A tiny rate converges slowly; a suitable rate converges quickly; too large a rate overshoots and diverges.

Figures: `figures/gd_loss_curve.png`, `figures/gd_trend_fit.png`
