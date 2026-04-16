# Wealth Guide

A Claude Code skill that builds you a personalized, CFP-quality financial roadmap. You answer 10 questions about your money. Six AI agents analyze your situation in parallel. You get a 600+ line wealth plan with real numbers, specific fund tickers, tax strategies, and a prioritized action checklist.

Works for the US and Canada. No signup. No API keys. Just install and say "wealth guide."

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
| Metric                          | Current (Age 50)  | Projected (Age 55, 2031) |
|---------------------------------|-------------------|--------------------------|
| Total Net Worth (est.)          | $1,346,500 CAD    | $2,461,000 CAD           |
| Liquid Investable Portfolio     | $950,000 CAD      | $2,014,000 CAD           |
| Annual Savings Capacity         | $147,000 CAD      | --                       |
| Sustainable Annual Income (4%)  | $38,000 CAD       | $80,560 CAD              |
```

Not "consider diversifying your portfolio." Real numbers. Real tickers. Real deadlines.

---

## How It Works

```
You ──> 10 interview screens ──> 6 AI agents (parallel) ──> 12-section roadmap
        (~3 minutes)              (~3-5 minutes)             (saved as markdown)
```

### The Interview

10 screens, all at the beginning. No interruptions mid-pipeline.

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
| Knowledge Advisor | Sonnet | Reads 7 knowledge base files, matches strategies, builds curriculum, searches news |
| Market Context Analyzer | Sonnet | Live web search for rates, indices, real estate, inflation data |

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
git clone https://github.com/YOUR_USERNAME/wealth-guide.git

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

## Project Structure

```
wealth-guide/
├── SKILL.md                          # The skill definition (interview + pipeline logic)
├── config/
│   ├── agent-config.yaml             # Timeouts, retry settings, level thresholds
│   └── init_db.py                    # SQLite schema (profiles + session history)
├── knowledge/                        # 7 curated knowledge base files
│   ├── index-investing.md            # Passive investing, ETFs, asset allocation
│   ├── real-estate-investing.md      # Primary residence, rentals, REITs
│   ├── retirement-planning.md        # FIRE, 4% rule, CPP/OAS, bucket strategies
│   ├── tax-optimization.md           # RRSP, TFSA, 401(k), tax-loss harvesting
│   ├── money-fundamentals.md         # Budgeting, emergency funds, debt payoff
│   ├── career-income-growth.md       # Salary negotiation, career strategy
│   └── side-hustles.md               # Freelancing, digital products, rental income
├── templates/
│   └── roadmap-template.md           # 12-section template with placeholders
├── workflows/                        # Step-by-step action workflows
│   ├── wealth-building.md
│   ├── debt-freedom.md
│   ├── first-investment.md
│   └── side-hustle-launch.md
├── roadmaps/                         # Generated roadmaps (gitignored)
└── data/                             # SQLite database (gitignored)
```

### Knowledge Base

The knowledge base is the backbone. Seven markdown files covering personal finance from fundamentals to advanced strategies, with country-specific sections for both the US and Canada. The knowledge advisor agent reads all seven before matching strategies to your profile.

These aren't scraped articles. Each file is hand-curated with specific numbers: contribution limits, tax brackets, fund tickers, APR ranges, and methodology citations. They're updated for the current tax year.

| File | Covers | Key Topics |
|------|--------|------------|
| `index-investing.md` | Passive investing | Couch Potato, asset allocation, MER comparison, rebalancing |
| `retirement-planning.md` | FIRE + traditional retirement | 4% rule, bucket strategy, CPP/OAS, sequence-of-returns risk |
| `tax-optimization.md` | Tax-advantaged accounts | RRSP/TFSA/401(k)/IRA, meltdown strategies, asset location |
| `money-fundamentals.md` | Foundations | Emergency fund sizing, debt avalanche/snowball, 50/30/20 |
| `real-estate-investing.md` | Property + REITs | Rent vs buy, mortgage types, cap rate, 1031/PRE |
| `career-income-growth.md` | Income optimization | Negotiation scripts, career laddering, credential ROI |
| `side-hustles.md` | Additional income | Freelancing, digital products, rental income, tax implications |

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

The knowledge base, agent prompts, and roadmap content all adapt based on your country selection. A Canadian user gets RRSP meltdown strategies and CPP deferral analysis. A US user gets Roth conversion ladders and HSA triple-tax-advantage breakdowns.

---

## Customization

### Adding a Country

1. Add country-specific context blocks in `SKILL.md` (search for `if country == "US"` to find all the spots)
2. Add a knowledge base file or country-specific sections to existing files
3. Add the country option to Screen 1 of the interview
4. Update the roadmap template's resource links

### Modifying Strategies

The strategies aren't hardcoded. The knowledge advisor reads the knowledge base files and matches methodologies to the user's profile. To add a new strategy methodology:

1. Add it to the relevant knowledge base file (e.g., `index-investing.md`)
2. Include: methodology name, key principle, citations, risk level, typical returns
3. The knowledge advisor will automatically pick it up if it matches the user's profile

### Changing the Roadmap Format

Edit `templates/roadmap-template.md`. Every `{PLACEHOLDER}` is filled by the action plan generator. Add sections, remove sections, change the order. The generator prompt in `SKILL.md` (Step 5) has section-by-section instructions that you'll want to update to match.

---

## Limitations

Let's be direct about what this isn't.

- **Not financial advice.** This is an educational tool. The roadmap says so at the top and bottom. It generates plans based on general financial principles and your self-reported data. It doesn't know your full tax situation, estate complexity, insurance needs, or whether your marriage is about to implode and take half your assets with it.
- **Midpoint math.** When you pick "$200,000 - $250,000" income, the system uses $225,000. Your actual income matters. The projections are directionally right, not CPA-precise.
- **No real-time portfolio data.** The system doesn't connect to your brokerage. It works with what you tell it.
- **Market data has a shelf life.** The market context agent searches the web at run time, but interest rates and index levels change daily. The roadmap reflects conditions at generation time.
- **Two countries.** US and Canada only. The knowledge base and tax logic don't cover other jurisdictions.

---

## Privacy

Everything runs locally.

- Your financial data is stored in a local SQLite file on your machine
- Agent prompts contain aggregated midpoints, not raw answers
- No data is sent to external services beyond the Claude API (which processes the agent prompts)
- The database file is created with `0600` permissions (owner read/write only)
- Roadmaps are saved locally as markdown files

If you want to nuke your data: `rm -rf ~/.claude/skills/wealth-guide/data/`

---

## Contributing

This is an open-source project. Contributions welcome.

**Good first contributions:**
- Add knowledge base content for a new financial topic
- Improve country-specific tax sections with current-year numbers
- Add a new workflow (e.g., `home-buying.md`, `tax-season.md`)
- Fix midpoint calculations or add more granular ranges
- Add support for a new country

**Before you PR:**
- Run the full pipeline end-to-end and verify the roadmap output
- Keep knowledge base files factual with citations
- Don't add speculative investment advice or guaranteed return claims

---

## License

MIT. Use it, fork it, build on it.

---

## Disclaimer

This tool is for educational and planning purposes only. It does not constitute investment advice, tax advice, or legal advice. All projections are based on assumptions that may not be realized. Past performance is not indicative of future results.

Before making significant financial decisions, consult qualified professionals:
- **US:** Find a CFP at [letsmakeaplan.org](https://www.letsmakeaplan.org/)
- **Canada:** Find a CFP at [fpcanada.ca](https://fpcanada.ca/)
