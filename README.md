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

FinAI consumes raw user data directly from the database.

### User Profile

{
  "salary": number,
  "rent": number,
  "current_savings": number
}
Expenses



  { "amount": number }

Assets



  {
    "type": "Bank | Mutual Fund | Stock | Gold | Real Estate | PF | Crypto",
    "value": number,
    "liquidity_score": 1-5
  }

Liabilities



  {
    "outstanding_amount": number,
    "monthly_payment": number
  }

Goals



  {
    "name": string,
    "target_amount": number,
    "target_date": "YYYY-MM-DD"
  }

## 🧮 What FinAI Calculates
### 💰 Net Worth


Net Worth = Total Assets − Total Debt
Used to identify long-term financial risk and bankruptcy scenarios.

### 🚨 Emergency Fund (Liquidity-Aware)
Only assets with liquidity_score ≥ 4 are counted.

To prevent manipulation:

Monthly burn is stabilized

Baseline burn is at least 50% of salary



Emergency Months = Liquid Assets / Baseline Burn
### 🔥 Monthly Burn & Surplus


Monthly Burn = Rent + Expenses + EMI
Surplus = Salary − Monthly Burn
A negative surplus:

Triggers overspending warnings

Reduces the financial health score

### 📈 Investment Recommendation (Capped Logic)


Recommended Investment =
min(
  30% of monthly surplus,
  20% of gross salary
)
This prevents:

Unrealistic advice during lean months

Over-optimization when lifestyle costs are temporarily low

### 📊 Financial Ratios
Savings Rate



(Surplus / Salary) × 100
Debt Ratio



(EMI / Salary) × 100
These ratios directly influence the health score.

### 🎯 Goal Feasibility Engine
Each financial goal is evaluated mathematically.

How it works
- Calculate months remaining until the target date

- Compute required monthly savings

- Compare against available surplus

Goal Status
- Status	Meaning
- On Track	Achievable with current finances
- At Risk	Requires lifestyle adjustments
- Impossible	Mathematically infeasible

No false optimism.

### 🏥 Financial Health Score (0–100)
The score is intentionally conservative and hard to game.

Factors
- ✅ High savings rate

- ✅ Low debt ratio

- ✅ Adequate emergency fund

- ❌ Overspending

- ❌ High EMI burden

- ❌ Negative net worth

Scores are clamped between 0 and 100.

### 📤 Output Schema


{
  "score": number,
  "net_worth": number,
  "total_assets": number,
  "liquid_assets": number,
  "monthly_burn": number,
  "surplus": number,
  "recommended_investment": number,
  "emergency_months": number,
  "savings_rate": number,
  "debt_ratio": number,
  "monthly_emi_burden": number,
  "allocation": object,
  "analyzed_goals": array
}
This output is:

- UI-ready

- AI-safe

- Deterministic

- Easy to test

## 🧪 Edge Cases Handled
- Zero income

- Overspending months

- Only locked assets

- EMI > salary

- Expired goals

- Negative net worth

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

