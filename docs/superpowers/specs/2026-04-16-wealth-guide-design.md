# Wealth Guide - US/Canada Personalized Wealth Coaching Skill

**Date:** 2026-04-16
**Status:** Approved
**Converted from:** rich-guide (Korean wealth coaching skill v3.0.0)

## Overview

A 7-agent multi-agent pipeline that conducts a financial interview, diagnoses financial health, matches strategy-focused methodologies from a curated knowledge base, generates personalized wealth strategies, evaluates risk/reward, and produces a comprehensive learning + action + workflow roadmap.

Supports both US and Canada via country detection at interview start. All content in English.

## Skill Metadata

```yaml
name: wealth-guide
description: Use when user says "wealth guide", "financial plan", "investment strategy",
  "how to build wealth", "money strategy", "retirement planning", or wants personalized
  wealth strategy. Conducts financial interview, runs 7-agent pipeline with expert
  knowledge base, and generates comprehensive learning + action + workflow roadmap.
version: 1.0.0
model: claude-sonnet-4-5-20250929
```

**Trigger phrases:**
- "wealth guide"
- "financial plan"
- "investment strategy"
- "how to build wealth"
- "retirement planning"
- "side hustle ideas"
- "/wealth-guide"

## Directory Structure

```
~/.claude/skills/wealth-guide/
├── data/               # SQLite profiles
├── roadmaps/           # Generated roadmap files
├── knowledge/          # Strategy-focused knowledge base (7 files)
│   ├── index-investing.md
│   ├── real-estate-investing.md
│   ├── side-hustles.md
│   ├── money-fundamentals.md
│   ├── tax-optimization.md
│   ├── retirement-planning.md
│   └── career-income-growth.md
├── workflows/
│   ├── first-investment.md
│   ├── debt-freedom.md
│   ├── side-hustle-launch.md
│   └── wealth-building.md
├── templates/
│   └── roadmap-template.md
└── config/
    ├── agent-config.yaml
    └── init_db.py
```

## Architecture

Same pipeline as Korean version - no structural changes.

- **Phase 1:** 3 parallel agents (financial-diagnostician, knowledge-advisor, market-context-analyzer)
- **Phase 2:** 2 sequential agents (wealth-strategist, risk-reward-evaluator)
- **Phase 3:** 1 agent (action-plan-generator)

## Financial Interview (9 fields)

| # | Field | Type | Details |
|---|-------|------|---------|
| 1 | Country | Choice | "United States" / "Canada" |
| 2 | Annual pre-tax income | Free text | e.g., "75000" - stored as number |
| 3 | Monthly expenses | Free text | e.g., "4500" - stored as number |
| 4 | Total savings | Choice | Under $1K / $1K-$5K / $5K-$25K / $25K-$100K / $100K+ |
| 5 | Investment assets | Choice | None / Under $10K / $10K-$50K / $50K-$200K / $200K-$500K / $500K+ |
| 6 | Total debt | Choice | None / Under $5K / $5K-$25K / $25K-$100K / $100K-$300K / $300K+ |
| 7 | Risk tolerance | Choice | Low / Medium / High |
| 8 | Investment experience | Choice | None / Basic / Intermediate / Advanced |
| 9 | Financial goal | Choice | Emergency fund / Buy home / Retirement / Side income / FIRE / Pay off debt |

Free-text fields: strip `$`, commas, reject non-numeric with gentle re-prompt.

## Country-Aware Agent Branching

Country branching lives in agent prompts via conditional blocks, not separate code paths.

### Financial Diagnostician

| Concept | US | Canada |
|---------|-----|--------|
| Debt-to-income threshold | 36% DTI | 40% TDS (GDS/TDS rules) |
| High-interest debt cutoff | >20% APR | >20% APR |
| Emergency fund benchmark | 3-6 months | 3-6 months |
| Healthy savings rate | 20%+ | 20%+ |

### Knowledge Advisor

| Concept | US | Canada |
|---------|-----|--------|
| Tax-advantaged accounts | 401(k), IRA, Roth IRA, HSA, 529 | RRSP, TFSA, RESP, FHSA |
| Index fund references | VTI, VXUS, VOO, BND | VEQT, XEQT, VCN, ZAG |
| Tax-loss harvesting | Wash sale rule (30 days) | Superficial loss rule (30 days) |
| Employer match | 401(k) match | RRSP group match / DPSP |

### Market Context Analyzer

| Concept | US | Canada |
|---------|-----|--------|
| Domestic market | S&P 500, NASDAQ | TSX Composite |
| Interest rate source | Federal Reserve / Fed Funds rate | Bank of Canada / overnight rate |
| Real estate context | Case-Shiller, local market | CREA HPI, local market |
| Savings rate benchmark | HYSA rates | HISA / GIC rates |

### Wealth Strategist

| Concept | US | Canada |
|---------|-----|--------|
| Retirement investing | Max 401(k) -> Roth IRA -> taxable | Max RRSP -> TFSA -> taxable |
| First home | FHA loan, down payment assistance | FHSA, First Home Buyer Incentive |
| Tax optimization | Standard/itemized deduction, capital gains brackets | Basic personal amount, 50% capital gains inclusion |
| Side hustle tax | Schedule C, self-employment tax 15.3% | T2125, CPP self-employed contributions |

## Knowledge Base (7 files, strategy-focused)

1. **index-investing.md** - Passive investing, DCA, asset allocation, US/CA-specific ETFs and accounts. Citations: Bogle, Malkiel, JL Collins, Canadian Couch Potato.

2. **real-estate-investing.md** - Primary residence, rental property, REITs. US: FHA, 1031 exchange. CA: FHSA, Smith Manoeuvre, principal residence exemption.

3. **side-hustles.md** - Freelancing, e-commerce, content creation, service businesses. US: LLC, Schedule C, quarterly estimated tax. CA: sole prop, GST/HST threshold.

4. **money-fundamentals.md** - Budgeting (50/30/20, zero-based), emergency fund, debt payoff (avalanche vs snowball), credit scores (FICO vs CA), insurance essentials.

5. **tax-optimization.md** - US: 401(k)/Roth ladder, backdoor Roth, HSA triple advantage, QBI deduction. CA: RRSP/TFSA decision framework, dividend tax credit, RRSP meltdown, incorporation for high earners. Estate/gift basics.

6. **retirement-planning.md** - US: Social Security optimization, RMDs, FIRE withdrawals (4% rule, Roth conversion ladder). CA: CPP optimization, OAS/GIS clawback, RRIF conversion, pension splitting.

7. **career-income-growth.md** - Salary negotiation, career capital, job hopping vs staying, equity compensation (RSUs, options, ESPP), high-ROI certifications.

## Strategy Categories

Expanded from 4 to 7:

`investment / tax-optimization / side-hustle / career-growth / real-estate / debt-payoff / cost-saving`

**Diversity requirements for wealth-strategist:**
- Risk range: low + medium + high
- Time range: short (1yr) + mid (3yr) + long (10yr+)
- Category: at least 3 of 7
- Must include at least 1 tax optimization strategy

## Output JSON Changes

- All field labels and content in English
- `expert_source` becomes `strategy_source: { methodology, key_principle, citations: ["author1", "author2"] }`
- New field per strategy: `country_specific: { accounts: [...], tax_implications: "...", regulatory_notes: "..." }`

## Data Layer

### profiles table

```sql
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT NOT NULL,
    annual_income REAL,
    monthly_expense REAL,
    savings TEXT,
    investment_assets TEXT,
    debt TEXT,
    risk_tolerance TEXT,
    experience TEXT,
    goal TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Midpoint mappings for calculations

```python
savings_midpoints = {
    "Under $1,000": 500, "$1,000 - $5,000": 3000,
    "$5,000 - $25,000": 15000, "$25,000 - $100,000": 62500, "$100,000+": 150000
}
investment_midpoints = {
    "None": 0, "Under $10,000": 5000, "$10,000 - $50,000": 30000,
    "$50,000 - $200,000": 125000, "$200,000 - $500,000": 350000, "$500,000+": 750000
}
debt_midpoints = {
    "None": 0, "Under $5,000": 2500, "$5,000 - $25,000": 15000,
    "$25,000 - $100,000": 62500, "$100,000 - $300,000": 200000, "$300,000+": 400000
}
```

### session_history table

```sql
CREATE TABLE session_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    user_level TEXT,
    selected_strategy TEXT,
    matched_strategies TEXT,
    selected_workflows TEXT,
    roadmap_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Level thresholds

- Beginner: health_score < 50, or investments = "None", or experience = "none"/"basic"
- Intermediate: 50 <= score < 75, investments > $0
- Advanced: score >= 75, investments >= $50,000

## Workflows (4 files)

| File | Purpose | US adaptations | CA adaptations |
|------|---------|---------------|----------------|
| first-investment.md | First-time investor guide | Open brokerage + Roth IRA, buy VTI/VXUS | Open TFSA, buy VEQT/XEQT |
| debt-freedom.md | Debt payoff sequencing | PSLF, IBR programs | Consumer proposal thresholds |
| side-hustle-launch.md | Starting a side business | LLC, EIN, Schedule C, quarterly tax | Sole prop, BN, GST/HST threshold |
| wealth-building.md | Long-term accumulation | 401k->Roth->taxable ladder | RRSP->TFSA->taxable optimization |

## Resource Links

| Resource | US | Canada |
|----------|-----|--------|
| Financial planner | letsmakeaplan.org | fpcanada.ca |
| Tax authority | irs.gov | canada.ca/cra |
| Investor education | investor.gov | getsmarteraboutmoney.ca |
| Retirement calculator | ssa.gov/benefits/calculators | canada.ca/cpp-calculator |
| Credit report | annualcreditreport.com | equifax.ca / transunion.ca |

## Disclaimer

Country-specific:
- US: "Consult a Certified Financial Planner (CFP) - letsmakeaplan.org"
- CA: "Consult a Certified Financial Planner (CFP) - fpcanada.ca"
- Both: "This is AI-generated reference information. Investment decisions should be made based on your own judgment and responsibility. Consult a qualified financial advisor before making significant financial decisions."

## Model Selection

| Agent | Model | Reason |
|-------|-------|--------|
| financial-diagnostician | claude-sonnet-4-5-20250929 | Numerical analysis |
| knowledge-advisor | claude-sonnet-4-5-20250929 | Knowledge matching + web search |
| market-context-analyzer | claude-sonnet-4-5-20250929 | Market analysis |
| wealth-strategist | claude-opus-4-6 | Strategy generation (complex reasoning) |
| risk-reward-evaluator | claude-sonnet-4-5-20250929 | Quantitative risk assessment |
| action-plan-generator | claude-opus-4-6 | Integrated roadmap generation |

## Deliverable

Phase 1: Convert SKILL.md only. Supporting files (knowledge base, workflows, templates, config) iterated in subsequent sessions.
