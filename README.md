# Wealth Guide

A Claude Code skill that builds you a personalized, CFP-quality financial roadmap. You answer 10 questions about your money. Six AI agents analyze your situation in parallel. You get a 600+ line wealth plan with real numbers, specific fund tickers, tax strategies, and a prioritized action checklist.

Works for the US, Canada, and India. No signup. No API keys. Just install and say "wealth guide."

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

---

## What You Get

A 12-section financial plan that reads like you paid a CFP $2,000 for it:

| Section | What's In It |
|---------|-------------|
| Executive Summary | Net worth snapshot, projected growth, timeline to your goal |
| Financial Position | Net worth breakdown, cash flow, health score with benchmarks |
| Wealth Projections | 3 scenarios (conservative/base/optimistic) projected year-by-year |
| Strategy Blueprint | 3-5 ranked strategies with fund tickers, dollar amounts, verdicts |
| Debt Strategy | Per-debt-type breakdown: payoff math, refinancing, prepay vs invest |
| Tax Strategy | Account optimization, contribution priority, asset location map |
| Cash Flow Plan | Savings waterfall with dollar amounts, year-by-year targets |
| Risk Assessment | Stress test (40% crash + job loss), sensitivity analysis |
| Action Plan | Every action in one table: priority, owner, deadline |
| Market Context | Live market data via web search (rates, indices, opportunities) |
| Learning Path | 3-phase curriculum with books, resources, time estimates |
| Key Dates | Tax deadlines, contribution deadlines, review schedule |

Here's what the executive summary actually looks like:

```
| Metric                          | Current (Age 35)  | Projected (Age 45, 2036)  |
|---------------------------------|-------------------|---------------------------|
| Total Net Worth (est.)          | ₹1,24,75,000      | ₹1,13,34,000 - ₹1,30,30,000 |
| Liquid Investable Portfolio     | ₹70,00,000        | ₹89,48,000 (base case)    |
| Annual Savings Capacity         | ₹41,62,500        | --                        |
| Sustainable Annual Income (4%)  | --                | ₹35,79,250                |
```

Not "consider diversifying your portfolio." Real numbers. Real tickers. Real deadlines.

---

## How It Works

```
You ──> 10 interview screens ──> 6 AI agents (parallel) ──> 12-section roadmap
        (~3 minutes)              (~3-5 minutes)             (saved as markdown)
```

### The Interview

10 screens, all at the beginning. No interruptions mid-pipeline. Country-aware -- Indian users see ₹ ranges in lakhs and crores, US/Canada users see dollar ranges.

1. Country + age + financial goal
2. Income bracket + monthly expenses
3. Income drill-down (narrower range for precision)
4. Savings + investment brackets
5. Savings + investment drill-down
6. Debt check (yes/no)
7. Debt types (credit card, loans, mortgage -- multiselect)
8. Debt amounts per type
9. Home value (only if you have a mortgage)
10. Risk tolerance + investing experience

Age accepts your exact number. Everything else uses smart ranges with a two-step drill-down: pick a broad bracket, then narrow it. This keeps each question to 4 options max while covering the full spectrum.

### The Pipeline

Six specialized agents, running in two phases:

**Phase 1 (parallel -- all 3 run simultaneously):**

| Agent | Model | Job |
|-------|-------|-----|
| Financial Diagnostician | Sonnet | Health score, savings rate, DTI, emergency fund analysis |
| Knowledge Advisor | Sonnet | Reads the entire knowledge base (~2,500 lines of curated financial strategy), matches methodologies to your profile, builds a learning curriculum, and searches the web for current financial news |
| Market Context Analyzer | Sonnet | Live web search for current rates, indices, real estate trends, inflation, gold prices |

**Phase 2 (sequential):**

| Agent | Model | Job |
|-------|-------|-----|
| Wealth Strategist | Opus | Generates 3-5 diverse strategies grounded in matched methodologies |
| Risk/Reward Evaluator | Sonnet | Scores each strategy, assigns verdicts (RECOMMENDED / PROCEED WITH CAUTION / NOT SUITABLE) |
| Action Plan Generator | Opus | Produces the final 12-section CFP-quality roadmap |

The strategist runs on Opus because strategy generation requires complex reasoning across financial data, tax rules, and methodology matching. The action plan generator runs on Opus because it synthesizes everything into a coherent 600+ line document. Everything else runs on Sonnet for speed.

---

## Install

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- Python 3.8+ (for SQLite database initialization)
- A Claude API key with access to Opus and Sonnet models

### Setup

```bash
# Clone the repo
git clone https://github.com/Srivatsa-Kasagar/wealth-guide.git

# Create the skill symlink
mkdir -p ~/.claude/skills
ln -s "$(pwd)/wealth-guide" ~/.claude/skills/wealth-guide
```

That's it. No dependencies. No `npm install`. No virtual environments. The skill uses only Python's standard library (`sqlite3`, `json`, `os`).

### Verify

Open Claude Code in any directory and type:

```
wealth guide
```

If the interview starts, you're good.

---

## The Knowledge Base

This is what makes the roadmap actually useful. Nearly 2,500 lines of hand-curated financial strategy across 7 files, covering everything from beginner budgeting to advanced tax optimization -- with country-specific sections for the US, Canada, and India.

Every file contains real numbers: current contribution limits, tax brackets, specific fund tickers with expense ratios, APR ranges, methodology citations, and step-by-step decision frameworks. The knowledge advisor reads all of it before matching strategies to your profile.

| File | What's Inside |
|------|--------------|
| `tax-optimization.md` | US: 401(k)/IRA/Roth/HSA limits, LTCG brackets, QBI. Canada: RRSP/TFSA/FHSA, dividend tax credit, meltdown strategies. India: Old vs New regime decision framework, 80C/80D/80E/24(b)/80CCD layering, STCG/LTCG post-2024 rules, HRA exemption, TDS thresholds |
| `retirement-planning.md` | US: Social Security optimization, Roth conversion ladders, Rule of 55. Canada: CPP/OAS deferral, RRIF, GIS. India: EPF/PPF/NPS mechanics, FIRE at 30-35x (not 25x -- India has no safety net), SWP vs annuity, retirement income ladder |
| `index-investing.md` | US: VTI/VOO/BND, target-date funds. Canada: VEQT/XEQT, Couch Potato, withholding tax. India: Nifty 50/Next 50/500, SIP mechanics, direct vs regular plans, platform comparison, Sovereign Gold Bonds, asset allocation by age |
| `real-estate-investing.md` | US: FHA/VA loans, 1031 exchanges, PMI. Canada: FHSA, HBP, Smith Manoeuvre. India: RERA, stamp duty by state, home loan deductions, REITs (Embassy/Mindspace), rent vs buy math, NRI rules |
| `money-fundamentals.md` | Emergency fund sizing (3-6 months US/CA, 6-12 months India), debt avalanche/snowball, credit scores (FICO/Equifax/CIBIL), insurance essentials (term life, health, what to avoid like ULIPs) |
| `career-income-growth.md` | Salary negotiation, stock option taxation (ISOs, RSUs, ESOPs across all 3 countries), freelance tax treatment, CTC vs take-home (India) |
| `side-hustles.md` | Freelancing, digital products, rental income -- with country-specific tax treatment (Schedule C, T2125, Section 44ADA/GST) |

Plus 4 step-by-step workflow guides (wealth building, debt freedom, first investment, side hustle launch) with country-specific paths.

The agents don't hallucinate financial advice. They read the knowledge base, find what matches your profile, and build the roadmap on that foundation.

---

## Configuration

`config/agent-config.yaml` controls the pipeline behavior:

```yaml
timeouts:
  wealth_strategist: 120      # Seconds before timeout (Opus agents need more time)
  action_plan_generator: 120
  financial_diagnostician: 60
  knowledge_advisor: 120

interview:
  cache_hours: 24              # Reuse profile if < 24 hours old
  refresh_days: 30             # Offer partial refresh if < 30 days old

levels:
  beginner_threshold: 50       # Health score below this = beginner
  intermediate_threshold: 75   # Score above this + $50K invested = advanced
  min_investment_for_advanced: 50000
```

### Profile Persistence

Your financial data is stored locally in a SQLite database at `~/.claude/skills/wealth-guide/data/profiles.db`. The schema:

- **profiles** -- country, age, income, expenses, savings, investments, 3 debt types, risk tolerance, experience, goal
- **session_history** -- links each run to the profile, strategies matched, roadmap path

If you run the skill again within 24 hours, it offers to reuse your existing data. Between 1-30 days, it offers a partial refresh (update income/expenses only). After 30 days, fresh interview.

Your data never leaves your machine. No API calls with your financial info. The agents receive aggregated midpoint values, not raw inputs.

---

## Country Support

### United States
- Tax-advantaged accounts: 401(k), Traditional IRA, Roth IRA, HSA, 529
- Debt context: PMI removal, student loan programs (IDR, PSLF), 1031 exchanges
- Tax strategy: standard vs itemized deduction, LTCG brackets, QBI deduction
- Market data: S&P 500, Fed Funds rate, HYSA rates

### Canada
- Tax-advantaged accounts: RRSP, TFSA, RESP, FHSA
- Debt context: CMHC insurance, stress test, mortgage renewal strategy
- Tax strategy: RRSP meltdown, dividend tax credit, superficial loss rule, OAS clawback
- Market data: TSX Composite, Bank of Canada rate, GIC rates, CREA HPI

### India
- Tax-advantaged accounts: EPF, PPF, NPS, ELSS, SCSS, Sukanya Samriddhi
- Tax regime: Old vs New regime optimization, Section 80C/80D/80E/24(b) deductions
- Debt context: Home loan deductions, gold loans, CIBIL scores, RBI floating-rate prepayment rules
- Capital gains: Equity STCG 20%, LTCG 12.5% above ₹1.25L, Sovereign Gold Bonds (zero LTCG at maturity)
- Investment: Nifty 50/Sensex index funds, SIP culture, direct vs regular mutual fund plans
- Market data: Nifty 50, Sensex, RBI repo rate, FD rates, NHB RESIDEX

The entire pipeline adapts based on your country. A Canadian user gets RRSP meltdown strategies and CPP deferral analysis. A US user gets Roth conversion ladders and HSA triple-tax-advantage breakdowns. An Indian user gets old vs new tax regime analysis, Section 80C optimization, and SIP-based wealth building with specific fund tickers.

---

## Customization

### Adding a Country

1. Add country-specific context blocks in `SKILL.md` (search for `if country == "US"` to find all the spots)
2. Add country-specific sections to the knowledge base files
3. Add the country option to Screen 1 of the interview
4. Add country-specific interview ranges (currency, income brackets, debt ranges)
5. Update the roadmap template's resource links

### Modifying Strategies

The strategies aren't hardcoded. The knowledge advisor reads the knowledge base files and matches methodologies to the user's profile. To add a new strategy methodology:

1. Add it to the relevant knowledge base file (e.g., `index-investing.md`)
2. Include: methodology name, key principle, citations, risk level, typical returns
3. The knowledge advisor will automatically pick it up if it matches the user's profile

### Changing the Roadmap Format

Edit `templates/roadmap-template.md`. Every `{PLACEHOLDER}` is filled by the action plan generator. Add sections, remove sections, change the order. The generator prompt in `SKILL.md` (Step 5) has section-by-section instructions that you'll want to update to match.

---

## Privacy

Everything runs locally.

- Your financial data is stored in a local SQLite file on your machine
- Agent prompts contain aggregated midpoint values, not raw answers
- No data is sent to external services beyond the Claude API (which processes the agent prompts)
- The database file is created with `0600` permissions (owner read/write only)
- Roadmaps are saved locally as markdown files

If you want to nuke your data: `rm -rf ~/.claude/skills/wealth-guide/data/`

---

## License

MIT. Use it, fork it, build on it.

---

## Disclaimer

This tool is for educational and planning purposes only. It does not constitute investment advice, tax advice, or legal advice. All projections are based on assumptions that may not be realized. Past performance is not indicative of future results.

Before making significant financial decisions, consult qualified professionals:
- **US:** Find a CFP at [letsmakeaplan.org](https://www.letsmakeaplan.org/)
- **Canada:** Find a CFP at [fpcanada.ca](https://fpcanada.ca/)
- **India:** Find a SEBI-registered investment advisor at [sebi.gov.in](https://www.sebi.gov.in/)
