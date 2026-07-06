# Error Budgets & SLO Forecasting

Continuous tracking of SLO budgets, consumption speeds, and exhaustion forecasting.

## Concepts & Formulas

The error budget represents the allowed unreliability of a service within a rolling window:

$$\text{Error Budget} = 1.0 - \text{SLO Target}$$

### Consumption & Burn Rate
As metrics breach SLO parameters, the error budget is consumed:

$$\text{Remaining Budget} = \text{Total Budget} - \text{Consumed Budget}$$

$$\text{Burn Rate} = \frac{\text{Actual Consumption Fraction}}{\text{Expected Consumption Fraction}}$$

- **Burn Rate = 1.0**: Normal consumption rate.
- **Burn Rate > 1.0**: Rapid budget depletion.

## Exhaustion Forecasting

Using current burn rates, the engine projects the time to exhaustion:

$$\text{Hours to Exhaustion} = \frac{\text{Budget Remaining}}{\text{Hourly Burn Rate}}$$

## REST APIs

### GET `/api/v1/operations-fabric/error-budgets`
Lists all active error budget balances, burn rates, and exhaustion forecasts for the tenant.
