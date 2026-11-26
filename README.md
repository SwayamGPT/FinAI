#  FinAI — Financial Intelligence Engine

FinAI is a deterministic financial intelligence engine that transforms raw personal finance data into risk-aware insights, realistic recommendations, and explainable metrics.

> ⚠️ FinAI is not an AI model and not a UI calculator.  
> It is a rules-based, precision-first financial engine designed to prevent unsafe or unrealistic financial advice.

---

## ✨ Why FinAI Exists

Most personal finance apps:
- Ignore asset liquidity
- Overestimate safety during low-spend months
- Suggest unrealistic investment amounts
- Spread financial logic across frontend and backend

FinAI fixes this by acting as a single source of truth for all financial decisions.

---

## 🧠 Design Principles

- Precision First  
  All monetary calculations use `Decimal` (no floating-point errors).

- Liquidity-Aware  
  Not all assets are equal — only liquid assets count for emergencies.

- Human-Realistic Advice  
  Investment recommendations are capped using real-world advisory rules.

- Hard to Game  
  Emergency funds, scores, and goals cannot be inflated artificially.

- Deterministic & Explainable  
  Same input → same output. Always.

---

## 📥 Inputs

FinAI reads raw user data from the database.

| Input | Fields |
|---|---|
| Profile | `salary` (monthly take-home, after tax), `rent`, `current_savings` |
| Expenses | `amount`, `date` — the current month plus the 3 months before it |
| Assets | `type` (Bank, Fixed Deposit, Mutual Fund, Stock, Gold, Real Estate, PF, Crypto), `value`, `liquidity_score` 1–5 |
| Liabilities | `outstanding_amount`, `interest_rate` (% p.a.), `monthly_payment` |
| Goals | `name`, `target_amount` (today's price), `target_date`, `priority` (High/Medium/Low), `saved_amount` |

Loan EMIs belong in Liabilities only, never in `rent`, so they are not counted twice.

## 🧮 What FinAI Calculates

All assumptions live at the top of `financial_engine.py`: inflation 6%, cash 3.5%, equity 10%,
per-asset returns (FD 7%, stocks 11%, gold 8%, property 5%, PF 8.25%, crypto 0%), high-interest threshold 12%.

### 1. Monthly expenses (no low-spend optimism)
```
monthly_expenses = max(
  this month so far, scaled to a full month   (only after day 7),
  average of the last 3 full months with logged expenses
)
Monthly Burn = Rent + monthly_expenses + EMIs
Surplus      = Salary − Monthly Burn
```

### 2. Emergency fund (liquidity-aware)
Only savings and assets with `liquidity_score ≥ 4` count. `Emergency Months = Liquid Assets / Monthly Burn`. Target: 6 months.

### 3. The surplus plan — every rupee is allocated once
The surplus is split in a fixed order and nothing is counted twice:

1. **Emergency fund** — 50% of surplus while below 3 months, 20% while between 3 and 6 months.
2. **High-interest debt** (≥ 12%) — everything that's left, until it is cleared.
3. **Goals** — High → Medium → Low priority, then nearest date first. Each goal only gets what earlier goals left.
   While high-interest debt is being prepaid, goals are judged on the money that frees up once it's gone.
4. **Investing** — whatever remains, but only once 3 months of emergency fund exist and no high-interest debt remains.
   Otherwise the recommendation is ₹0 with a reason (`investment_note`).

### 4. Debt payoff (true avalanche)
Each loan is simulated separately, month by month: every loan gets its EMI, the extra payment goes to the highest-rate
loan, and EMIs freed by paid-off loans roll over to the next one. Compared with paying only minimum EMIs, this gives
`interest_saved`. Debt not cleared within 30 years is flagged as a debt trap.

### 5. Goals
```
inflated_target   = target_amount × (1 + 6%)^years
remaining         = inflated_target − saved_amount × (1 + r)^months
required_monthly  = remaining × i / ((1 + i)^n − 1)        (SIP formula)
```
`r` is 6% for goals under 3 years, 10% otherwise. Status: **On Track** (fully funded by the plan), **At Risk** (≥ 50%),
**Unrealistic** (< 50%), **Achieved**, or **Overdue** (date passed, money still needed).

### 6. Net-worth projection (12 months)
Each asset grows at its own rate, each loan follows the debt simulation (interest added, principal repaid), and plan
contributions flow into cash, goals or investments. A deficit drains savings. Every point also has `net_worth_real`
(in today's money). Labels include the year (`Jan 27`).

### 7. Health score (0–100), with a breakdown
| Component | Max | Full marks when |
|---|---|---|
| Savings rate | 25 | saving ≥ 20% of income |
| Emergency fund | 25 | ≥ 6 months |
| Debt-to-income | 20 | EMIs ≤ 20% of income (0 at ≥ 50%, or a debt trap) |
| High-interest debt | 10 | none |
| Goals on track | 10 | all goals funded (no goals = 5) |
| Net worth | 10 | ≥ one year of income |
| Overspending | −20 | penalty scales with the deficit, full at 10% of income |

Every component is continuous (no cliff edges) and is returned in `score_breakdown` with a plain-English reason.

### 8. Asset allocation
Percentages are computed in `Decimal` and rounded with the largest-remainder method, so they always sum to exactly 100.

### 📤 Output (main fields)
```
score, score_breakdown[], net_worth, surplus, monthly_burn, monthly_expenses, month_to_date_spent,
expense_basis{}, total_emi, plan{emergency_fund, debt_prepayment, goals, investment},
recommended_investment, investment_note, emergency_months, emergency_target,
debt_strategy{freedom_date, months_to_freedom, recommended_extra_payment, interest_saved, payoff_order[]},
projections[{month, net_worth, net_worth_real, assets, debt}], analyzed_goals[], allocation{}, assumptions{}
```
The frontend only displays these numbers; it does no financial maths of its own.

## 🧪 Tests
```
cd backend && pip install -r requirements.txt -r requirements-dev.txt && pytest
```
Worked examples cover double-counting, avalanche ordering, rollover, SIP/inflation, overdue goals,
early-month estimates, investment safety, score smoothness and allocation rounding.

## 🔒 Safety by Design
FinAI ensures:

- No AI can give reckless advice

- No UI can bypass financial constraints

- All recommendations are explainable

- FinAI protects users from bad financial decisions — even if they try to game the system.

## 📁 Location


backend/services/financial_engine.py


## 📌 Disclaimer
This project is for educational and informational purposes only
and does not constitute financial advice.

