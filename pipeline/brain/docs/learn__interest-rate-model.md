> ## Documentation Index
> Fetch the complete documentation index at: https://docs.vanna.finance/llms.txt
> Use this file to discover all available pages before exploring further.

# Interest Rate Model

> Current Stellar testnet interest rate model.

The borrow rate rises as more of a pool's assets are borrowed. Utilization is outstanding debt divided by available cash plus outstanding debt.

The implemented curve combines linear, 32nd-power, and 64th-power utilization terms. Defaults use coefficients 0.1, 0.3, and 3.5, producing a smooth curve that steepens at high utilization. It is not a two-slope kink model.

## Configurable economics

The rate-model admin can change the coefficients, within an implied worst-case cap of 1000% APR at full utilization. Each pool can also change its rate-model address. A historical example or default coefficient does not establish today's deployed rate.

The pool's separate 95% utilization cap limits new borrowing; it is not the interest model's maximum input. Supply yield depends on utilization and borrower interest, and displayed APR is not guaranteed realized APY.

Interest accrues between updates. Reads preview it, and subsequent pool operations persist it. See [Rate Model](/developers/contracts/rate-model) and [Math Reference](/developers/math-reference).
