# Wealth Guide SKILL.md Conversion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the Korean rich-guide SKILL.md into a US/Canada wealth-guide SKILL.md with country-aware branching, English interview, strategy-focused knowledge base references, and 7 expanded strategy categories.

**Architecture:** Single SKILL.md file containing the full 7-agent pipeline algorithm. Country detection at interview start propagates a `country` field through all agent prompts. Interview uses 2 free-text fields (income, expenses) and 7 multiple-choice fields. Knowledge base expanded from 4 to 7 files. Strategy categories expanded from 4 to 7.

**Tech Stack:** Markdown skill file with embedded Python pseudocode, SQLite for profile persistence, Claude subagents (Sonnet 4.5 + Opus 4.6).

**Spec:** `docs/superpowers/specs/2026-04-16-wealth-guide-design.md`
**Source (Korean):** `SKILL.md` (current file in repo root)
**Target:** `SKILL.md` (overwrite in place)

---

### Task 1: Frontmatter + Triggers + Step 1 (Environment Setup)

**Files:**
- Modify: `SKILL.md:1-101` (replace frontmatter, triggers, and Step 1 entirely)

- [ ] **Step 1: Replace frontmatter and trigger section**

Replace lines 1-21 of SKILL.md with:

```markdown
---
name: wealth-guide
description: Use when user says "wealth guide", "financial plan", "investment strategy", "how to build wealth", "money strategy", "retirement planning", "side hustle ideas", or wants personalized wealth strategy. Conducts financial interview, runs 7-agent pipeline with expert knowledge base, and generates comprehensive learning + action + workflow roadmap.
version: 1.0.0
model: claude-sonnet-4-5-20250929
---

# Wealth Guide Skill

Personalized US/Canada wealth coaching via 7-agent multi-agent pipeline with curated strategy-focused knowledge base.

## Trigger Phrases

- "wealth guide"
- "financial plan"
- "investment strategy"
- "how to build wealth"
- "retirement planning"
- "side hustle ideas"
- "/wealth-guide"
```

- [ ] **Step 2: Replace Step 1 (Environment Setup & Config Load)**

Replace lines 23-101 with the updated environment setup. Key changes:
- Directory path: `~/.claude/skills/wealth-guide/` (was `rich-guide`)
- DB_DIR, ROADMAP_DIR, KB_DIR, WF_DIR all use `wealth-guide`
- Config path uses `wealth-guide`
- Profile check query stays the same (SQLite schema changes are in the init_db.py, not here)

```markdown
## Execution Algorithm

### Step 1: Environment Setup & Config Load

\```python
import subprocess, os, json
from datetime import datetime

DB_DIR = os.path.expanduser("~/.claude/skills/wealth-guide/data")
DB_PATH = f"{DB_DIR}/profiles.db"
ROADMAP_DIR = os.path.expanduser("~/.claude/skills/wealth-guide/roadmaps")
KB_DIR = os.path.expanduser("~/.claude/skills/wealth-guide/knowledge")
WF_DIR = os.path.expanduser("~/.claude/skills/wealth-guide/workflows")
TS = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create directories
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(ROADMAP_DIR, exist_ok=True)

# Init DB
init_script = os.path.expanduser("~/.claude/skills/wealth-guide/config/init_db.py")
subprocess.run(["python3", init_script, DB_PATH], check=True)
os.chmod(DB_PATH, 0o600)

# Load agent-config.yaml
config_path = os.path.expanduser("~/.claude/skills/wealth-guide/config/agent-config.yaml")
agent_config = {}
try:
    import yaml
    with open(config_path) as f:
        agent_config = yaml.safe_load(f) or {}
except Exception:
    agent_config = {
        "timeouts": {
            "wealth_strategist": 120,
            "action_plan_generator": 120,
            "financial_diagnostician": 60,
            "market_context_analyzer": 60,
            "risk_reward_evaluator": 60,
            "knowledge_advisor": 120,
        },
        "retry": {"max_attempts": 2, "fallback_on_fail": True},
        "interview": {"cache_hours": 24, "refresh_days": 30},
        "levels": {"beginner_threshold": 50, "intermediate_threshold": 75, "min_investment_for_advanced": 50000},
    }

TIMEOUT_STRATEGIST = agent_config.get("timeouts", {}).get("wealth_strategist", 120)
TIMEOUT_EVALUATOR = agent_config.get("timeouts", {}).get("risk_reward_evaluator", 60)
TIMEOUT_ACTION = agent_config.get("timeouts", {}).get("action_plan_generator", 120)
TIMEOUT_KNOWLEDGE = agent_config.get("timeouts", {}).get("knowledge_advisor", 120)
CACHE_HOURS = agent_config.get("interview", {}).get("cache_hours", 24)
REFRESH_DAYS = agent_config.get("interview", {}).get("refresh_days", 30)
LEVEL_BEGINNER = agent_config.get("levels", {}).get("beginner_threshold", 50)
LEVEL_INTERMEDIATE = agent_config.get("levels", {}).get("intermediate_threshold", 75)
LEVEL_ADV_INVEST = agent_config.get("levels", {}).get("min_investment_for_advanced", 50000)

# Check existing profile
result = subprocess.run(
    ["python3", "-c", f"""
import sqlite3, json
conn = sqlite3.connect('{DB_PATH}')
row = conn.execute("SELECT *, (julianday('now') - julianday(updated_at)) as age_days FROM profiles ORDER BY updated_at DESC LIMIT 1").fetchone()
if row:
    cols = [d[0] for d in conn.execute("PRAGMA table_info(profiles)").fetchall()]
    d = dict(zip(cols, row[:-1]))
    age = row[-1]
    print(json.dumps({{"exists": True, "age_days": age, "data": d}}))
else:
    print(json.dumps({{"exists": False}}))
conn.close()
"""],
    capture_output=True, text=True
)
try:
    existing = json.loads(result.stdout.strip())
except json.JSONDecodeError:
    existing = {"exists": False}
profile = None
\```

Decide data strategy based on loaded config thresholds:
- `existing["exists"]` AND `existing["age_days"] < CACHE_HOURS/24` -> offer reuse
- `existing["exists"]` AND `CACHE_HOURS/24 <= existing["age_days"] <= REFRESH_DAYS` -> offer refresh
- Otherwise -> new interview
```

- [ ] **Step 3: Verify the frontmatter and Step 1 read correctly**

Read back lines 1-100 of the modified SKILL.md and confirm:
- Frontmatter says `name: wealth-guide`
- All paths reference `wealth-guide` not `rich-guide`
- `min_investment_for_advanced` is `50000` (USD/CAD) not `2000` (만원)
- No Korean text remains

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert wealth-guide frontmatter and environment setup from Korean"
```

---

### Task 2: Step 2 (Financial Interview) - Reuse/Refresh Branch

**Files:**
- Modify: `SKILL.md` (replace the reuse/refresh section of Step 2, roughly lines 112-195 in original)

- [ ] **Step 1: Write the reuse/refresh branch in English**

This replaces the Korean reuse/refresh prompts. The partial-refresh branch asks about income and expenses (the two free-text fields) since those change most often.

```markdown
### Step 2: Financial Interview (or Reuse / Refresh Existing)

\```python
if existing.get("exists") and existing["age_days"] < (CACHE_HOURS / 24):
    reuse_choice = AskUserQuestion(questions=[{
        "question": f"Use existing financial data (created {existing['data']['updated_at'][:10]})?",
        "header": "Existing Data",
        "options": [
            {"label": "Use existing data", "description": "Jump straight to strategy analysis"},
            {"label": "Start fresh", "description": "Re-enter all financial information"}
        ]
    }])
    if reuse_choice["Existing Data"] == "Use existing data":
        profile = existing["data"]

elif existing.get("exists") and (CACHE_HOURS / 24) <= existing["age_days"] <= REFRESH_DAYS:
    refresh_choice = AskUserQuestion(questions=[{
        "question": f"Your financial data is {int(existing['age_days'])} days old. What would you like to do?",
        "header": "Data Refresh",
        "options": [
            {"label": "Use existing data", "description": f"Continue with {existing['data']['updated_at'][:10]} data"},
            {"label": "Update key fields", "description": "Update income/expenses only"},
            {"label": "Start from scratch", "description": "Re-enter all financial information"}
        ]
    }])
    refresh_answer = refresh_choice.get("Data Refresh", "Start from scratch")
    if refresh_answer == "Use existing data":
        profile = existing["data"]
    elif refresh_answer == "Update key fields":
        partial_responses = AskUserQuestion(questions=[
            {
                "question": f"Annual pre-tax income (current: ${existing['data'].get('annual_income', '?'):,.0f}). Enter new amount or type 'same':",
                "header": "income_refresh"
            },
            {
                "question": f"Monthly expenses (current: ${existing['data'].get('monthly_expense', '?'):,.0f}). Enter new amount or type 'same':",
                "header": "expense_refresh"
            }
        ])
        profile = dict(existing["data"])
        new_income = partial_responses.get("income_refresh", "same").strip()
        new_expense = partial_responses.get("expense_refresh", "same").strip()

        def parse_currency(val):
            """Strip $, commas, spaces and return float or None."""
            cleaned = val.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None

        if new_income.lower() != "same":
            parsed = parse_currency(new_income)
            if parsed is not None:
                profile["annual_income"] = parsed
        if new_expense.lower() != "same":
            parsed = parse_currency(new_expense)
            if parsed is not None:
                profile["monthly_expense"] = parsed

        # Persist partial refresh to DB
        subprocess.run(["python3", "-c", f"""
import sqlite3, json
conn = sqlite3.connect('{DB_PATH}')
d = json.loads('''{json.dumps(profile)}''')
conn.execute('''INSERT INTO profiles
    (country, annual_income, monthly_expense, savings, investment_assets, debt, risk_tolerance, experience, goal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (d.get('country','US'), d.get('annual_income',75000), d.get('monthly_expense',4000),
     d.get('savings','$5,000 - $25,000'), d.get('investment_assets','None'),
     d.get('debt','None'), d.get('risk_tolerance','medium'),
     d.get('experience','none'), d.get('goal','')))
conn.commit()
conn.close()
"""], check=True)
\```
```

- [ ] **Step 2: Verify no Korean text in reuse/refresh section**

Read the reuse/refresh section and confirm all user-facing strings are English.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert reuse/refresh interview branch to English with free-text income/expenses"
```

---

### Task 3: Step 2 (Financial Interview) - New Interview

**Files:**
- Modify: `SKILL.md` (replace the new interview section, roughly lines 197-353 in original)

- [ ] **Step 1: Write the new interview with 9 fields**

This is the largest content change. Country question first, then 2 free-text (income, expenses), then 6 multiple-choice (savings, investments, debt, risk, experience, goal).

```markdown
\```python
if profile is None:
    # Question 1: Country
    country_response = AskUserQuestion(questions=[
        {
            "question": "Which country are you based in?",
            "header": "country",
            "options": [
                {"label": "United States", "description": "US tax system, 401(k), IRA, etc."},
                {"label": "Canada", "description": "Canadian tax system, RRSP, TFSA, etc."}
            ]
        }
    ])
    country = "US" if country_response.get("country") == "United States" else "CA"

    # Questions 2-3: Free-text income and expenses
    income_expense = AskUserQuestion(questions=[
        {
            "question": "What is your annual pre-tax household income? (e.g., 75000)",
            "header": "annual_income"
        },
        {
            "question": "What are your total monthly expenses? (e.g., 4500)",
            "header": "monthly_expense"
        }
    ])

    def parse_currency(val):
        """Strip $, commas, spaces and return float or None."""
        cleaned = str(val).replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    annual_income = parse_currency(income_expense.get("annual_income", "75000")) or 75000.0
    monthly_expense = parse_currency(income_expense.get("monthly_expense", "4000")) or 4000.0

    # Questions 4-6: Savings, investments, debt (multiple choice)
    assets_debt = AskUserQuestion(questions=[
        {
            "question": "How much do you have in savings/checking accounts?",
            "header": "savings",
            "options": [
                {"label": "Under $1,000", "description": ""},
                {"label": "$1,000 - $5,000", "description": ""},
                {"label": "$5,000 - $25,000", "description": ""},
                {"label": "$25,000 - $100,000", "description": ""},
                {"label": "$100,000+", "description": ""}
            ]
        },
        {
            "question": "Total investment assets (stocks, bonds, funds, crypto, etc.)?",
            "header": "investment_assets",
            "options": [
                {"label": "None", "description": "No investment experience"},
                {"label": "Under $10,000", "description": ""},
                {"label": "$10,000 - $50,000", "description": ""},
                {"label": "$50,000 - $200,000", "description": ""},
                {"label": "$200,000 - $500,000", "description": ""},
                {"label": "$500,000+", "description": ""}
            ]
        },
        {
            "question": "Total outstanding debt (mortgage, student loans, credit cards, etc.)?",
            "header": "debt",
            "options": [
                {"label": "None", "description": ""},
                {"label": "Under $5,000", "description": ""},
                {"label": "$5,000 - $25,000", "description": ""},
                {"label": "$25,000 - $100,000", "description": ""},
                {"label": "$100,000 - $300,000", "description": ""},
                {"label": "$300,000+", "description": "Mortgage territory"}
            ]
        }
    ])

    # Questions 7-9: Risk tolerance, experience, goal (multiple choice)
    preferences = AskUserQuestion(questions=[
        {
            "question": "What is your risk tolerance?",
            "header": "risk_tolerance",
            "options": [
                {"label": "Low", "description": "Capital preservation first - prefer savings accounts, bonds, GICs/CDs"},
                {"label": "Medium", "description": "Balanced growth - index funds, some individual stocks"},
                {"label": "High", "description": "Aggressive growth - individual stocks, crypto, leveraged positions"}
            ]
        },
        {
            "question": "What is your investment experience?",
            "header": "experience",
            "options": [
                {"label": "None", "description": "I'm completely new to investing"},
                {"label": "Basic", "description": "I have a savings account, maybe a workplace retirement plan"},
                {"label": "Intermediate", "description": "I actively invest in stocks/funds"},
                {"label": "Advanced", "description": "I manage a diversified portfolio across asset classes"}
            ]
        },
        {
            "question": "What is your primary financial goal?",
            "header": "goal",
            "options": [
                {"label": "Build emergency fund (within 1 year)", "description": "Need a financial safety net"},
                {"label": "Buy a home (3-5 years)", "description": "Saving for a down payment"},
                {"label": "Retirement planning (10+ years)", "description": "Long-term wealth building"},
                {"label": "Generate side income", "description": "Start a side hustle or freelance"},
                {"label": "Early retirement / FIRE", "description": "Financial independence, retire early"},
                {"label": "Pay off debt", "description": "Eliminate high-interest or total debt"}
            ]
        }
    ])

    # Midpoint mappings for numeric calculations
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

    risk_map = {"Low": "low", "Medium": "medium", "High": "high"}
    experience_map = {"None": "none", "Basic": "basic", "Intermediate": "intermediate", "Advanced": "advanced"}

    savings_label = assets_debt.get("savings", "Under $1,000")
    investments_label = assets_debt.get("investment_assets", "None")
    debt_label = assets_debt.get("debt", "None")

    profile = {
        "country": country,
        "annual_income": annual_income,
        "monthly_expense": monthly_expense,
        "savings": savings_label,
        "savings_midpoint": savings_midpoints.get(savings_label, 3000),
        "investment_assets": investments_label,
        "investment_midpoint": investment_midpoints.get(investments_label, 0),
        "debt": debt_label,
        "debt_midpoint": debt_midpoints.get(debt_label, 0),
        "risk_tolerance": risk_map.get(preferences.get("risk_tolerance", "Medium"), "medium"),
        "experience": experience_map.get(preferences.get("experience", "None"), "none"),
        "goal": preferences.get("goal", "Retirement planning (10+ years)")
    }

    # Save to DB
    import tempfile
    profile_tmp = tempfile.mktemp(suffix=".json")
    with open(profile_tmp, "w") as f:
        json.dump(profile, f, ensure_ascii=False)

    subprocess.run(["python3", "-c", f"""
import sqlite3, json
with open('{profile_tmp}') as f:
    d = json.load(f)
conn = sqlite3.connect('{DB_PATH}')
conn.execute('''INSERT INTO profiles
    (country, annual_income, monthly_expense, savings, investment_assets, debt, risk_tolerance, experience, goal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (d['country'], d['annual_income'], d['monthly_expense'], d['savings'],
     d['investment_assets'], d['debt'], d['risk_tolerance'], d['experience'], d['goal']))
conn.commit()
conn.close()
import os
os.remove('{profile_tmp}')
print("saved")
"""], check=True)

    monthly_income = profile['annual_income'] / 12
    monthly_surplus = monthly_income - profile['monthly_expense']
    currency = "USD" if country == "US" else "CAD"
    print(f"Financial profile saved")
    print(f"Monthly surplus: approx. ${monthly_surplus:,.0f} {currency}")
\```
```

- [ ] **Step 2: Verify the interview section**

Read the interview section and confirm:
- Country question appears first
- Free-text for income/expenses with `parse_currency` helper
- Multiple choice for savings/investments/debt with correct brackets from spec
- Risk/experience/goal options match spec exactly
- Midpoint mappings match spec
- DB INSERT uses 9 fields (country, annual_income, monthly_expense, savings, investment_assets, debt, risk_tolerance, experience, goal)
- No Korean text

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert financial interview to English with country detection and 9-field form"
```

---

### Task 4: Step 3 (Phase 1 - Financial Diagnostician Agent)

**Files:**
- Modify: `SKILL.md` (replace Phase 1 intro + diagnostician agent, roughly lines 357-400 in original)

- [ ] **Step 1: Write Phase 1 header and financial-diagnostician agent**

```markdown
### Step 3: Phase 1 - Parallel Diagnosis + Knowledge Matching

Launch all 3 Phase 1 agents simultaneously. All three Task() calls must appear in a single response block so Claude Code executes them in parallel. The knowledge-advisor combines knowledge base reading with web search.

\```python
print("Phase 1: Diagnosis + Knowledge Matching (3 agents in parallel)...")

experience = profile.get("experience", "none")
country = profile.get("country", "US")
currency = "USD" if country == "US" else "CAD"
monthly_income = profile['annual_income'] / 12

country_context_diagnostician = ""
if country == "US":
    country_context_diagnostician = """
    Country-specific rules (US):
    - Debt-to-income threshold: 36% DTI is healthy, >43% is concerning
    - High-interest debt: >20% APR (credit cards)
    - Emergency fund: 3-6 months expenses in HYSA
    - Savings rate benchmark: 20%+ (50/30/20 rule)
    """
else:
    country_context_diagnostician = """
    Country-specific rules (Canada):
    - Debt ratios: GDS ≤ 32%, TDS ≤ 40%
    - High-interest debt: >20% APR (credit cards)
    - Emergency fund: 3-6 months expenses in HISA or GIC
    - Savings rate benchmark: 20%+
    """

# CRITICAL: All 3 Task calls must be in a single response for parallel execution
Task(
    subagent_type="financial-diagnostician",
    model="claude-sonnet-4-5-20250929",
    description="Financial health diagnosis",
    prompt=f"""
    Analyze the user's financial profile and produce a financial health diagnosis.

    Profile:
    - Country: {country} ({currency})
    - Annual income: ${profile['annual_income']:,.0f}
    - Monthly income: ${monthly_income:,.0f}
    - Monthly expenses: ${profile['monthly_expense']:,.0f}
    - Savings: {profile['savings']} (midpoint: ${profile['savings_midpoint']:,.0f})
    - Investment assets: {profile['investment_assets']} (midpoint: ${profile['investment_midpoint']:,.0f})
    - Debt: {profile['debt']} (midpoint: ${profile['debt_midpoint']:,.0f})
    - Risk tolerance: {profile['risk_tolerance']}
    - Goal: {profile.get('goal', 'Not specified')}

    {country_context_diagnostician}

    Save the following JSON to /tmp/wealth-guide-diagnostician-{TS}.json:
    {{
      "status": "success",
      "agent": "financial-diagnostician",
      "country": "{country}",
      "health_score": 0-100,
      "monthly_surplus": monthly surplus in {currency},
      "savings_rate": savings rate (%),
      "debt_ratio": debt-to-income ratio (%),
      "emergency_fund_months": months of expenses covered by savings,
      "diagnosis": "2-3 sentence summary of financial health",
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"],
      "recommended_investment_ratio": recommended % of surplus to invest
    }}

    Use the Write tool to save the file.
    """
)
\```
```

- [ ] **Step 2: Verify diagnostician agent prompt**

Confirm: country-aware DTI thresholds, currency formatting, English output fields, correct tmp file path pattern (`wealth-guide-` not `rich-guide-`).

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert financial-diagnostician agent to US/CA with country branching"
```

---

### Task 5: Step 3 (Phase 1 - Knowledge Advisor Agent)

**Files:**
- Modify: `SKILL.md` (replace knowledge-advisor agent)

- [ ] **Step 1: Write knowledge-advisor agent with 7 knowledge base files**

```markdown
\```python
country_context_knowledge = ""
if country == "US":
    country_context_knowledge = """
    Country: United States
    Tax-advantaged accounts: 401(k), Traditional IRA, Roth IRA, HSA, 529
    Common index funds: VTI, VXUS, VOO, BND, target-date funds
    Tax-loss harvesting: wash sale rule (30 days)
    Employer match: 401(k) match
    """
else:
    country_context_knowledge = """
    Country: Canada
    Tax-advantaged accounts: RRSP, TFSA, RESP, FHSA
    Common index funds: VEQT, XEQT, VCN, ZAG, VBAL
    Tax-loss harvesting: superficial loss rule (30 days)
    Employer match: RRSP group match / DPSP
    """

Task(
    subagent_type="knowledge-advisor",
    model="claude-sonnet-4-5-20250929",
    description="Knowledge base matching + learning curriculum",
    prompt=f"""
    Match the user's profile to strategy-focused methodologies and generate a learning curriculum.

    User profile:
    - Country: {country}
    - Annual income: ${profile['annual_income']:,.0f}
    - Savings: {profile['savings']} (midpoint: ${profile['savings_midpoint']:,.0f})
    - Investment assets: {profile['investment_assets']} (midpoint: ${profile['investment_midpoint']:,.0f})
    - Debt: {profile['debt']} (midpoint: ${profile['debt_midpoint']:,.0f})
    - Risk tolerance: {profile['risk_tolerance']}
    - Experience: {experience}
    - Goal: {profile.get('goal', 'Not specified')}

    {country_context_knowledge}

    Knowledge base file paths (Read each with the Read tool):
    1. {KB_DIR}/index-investing.md - Passive index investing methodology
    2. {KB_DIR}/real-estate-investing.md - Real estate strategies
    3. {KB_DIR}/side-hustles.md - Side hustle guide
    4. {KB_DIR}/money-fundamentals.md - Budgeting, emergency fund, debt payoff
    5. {KB_DIR}/tax-optimization.md - Tax-advantaged strategies
    6. {KB_DIR}/retirement-planning.md - Retirement and FIRE strategies
    7. {KB_DIR}/career-income-growth.md - Career growth and salary optimization

    Workflow file paths (record filename only if selected):
    - first-investment.md, debt-freedom.md, side-hustle-launch.md, wealth-building.md

    Level assessment criteria:
    - Beginner: health_score < {LEVEL_BEGINNER} OR investments = "None" OR experience = "none"/"basic"
    - Intermediate: {LEVEL_BEGINNER} <= score < {LEVEL_INTERMEDIATE} AND investments > $0
    - Advanced: score >= {LEVEL_INTERMEDIATE} AND investments >= ${LEVEL_ADV_INVEST:,.0f}

    Note: health_score is not yet calculated. Use investment assets ({profile['investment_assets']}) and experience ({experience}) for initial level assessment.

    Tasks:
    1. Read all 7 knowledge base files
    2. Assess user level
    3. Match 3-5 strategy methodologies based on level + risk + goal + country
    4. Generate learning curriculum (order + topic + source + reason)
    5. Select 1-2 appropriate workflows
    6. Use WebSearch for current financial news relevant to the user's situation

    Save the following JSON to /tmp/wealth-guide-knowledge-{TS}.json:
    {{
      "status": "success",
      "agent": "knowledge-advisor",
      "country": "{country}",
      "user_level": "beginner/intermediate/advanced",
      "level_reasoning": "reasoning for level assessment",
      "matched_strategies": [
        {{"methodology": "strategy name", "category": "category", "reason": "matching reason", "source_file": "filename", "citations": ["author1", "author2"]}}
      ],
      "learning_curriculum": [
        {{"order": 1, "topic": "topic", "source": "source", "why": "reason", "estimated_time": "time"}}
      ],
      "recommended_books": [
        {{"title": "book title", "author": "author", "level": "level"}}
      ],
      "selected_workflows": ["workflow filename"],
      "workflow_reasoning": "selection reason",
      "curated_info": [
        {{"title": "article title", "source": "domain", "url": "URL", "summary": "summary", "verified": true, "relevance": "high"}}
      ],
      "key_insights": ["insight1", "insight2"],
      "tax_benefits": ["tax benefit1", "tax benefit2"]
    }}

    Use the Write tool to save the file.
    """
)
\```
```

- [ ] **Step 2: Verify knowledge-advisor changes**

Confirm: 7 knowledge file paths (not 4), strategy-focused field names (`matched_strategies` not `matched_experts`), country context block, English output, correct tmp file path.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert knowledge-advisor to 7 strategy-focused knowledge files with US/CA context"
```

---

### Task 6: Step 3 (Phase 1 - Market Context Analyzer + Phase 1 Results)

**Files:**
- Modify: `SKILL.md` (replace market-context-analyzer agent and Phase 1 result reading)

- [ ] **Step 1: Write market-context-analyzer with US/CA market references**

```markdown
\```python
country_context_market = ""
if country == "US":
    country_context_market = """
    Country: United States
    Domestic market: S&P 500, NASDAQ Composite
    Interest rate: Federal Reserve / Fed Funds rate
    Real estate: Case-Shiller Home Price Index
    Savings benchmark: HYSA rates
    """
else:
    country_context_market = """
    Country: Canada
    Domestic market: TSX Composite
    Interest rate: Bank of Canada / overnight rate
    Real estate: CREA Home Price Index (HPI)
    Savings benchmark: HISA / GIC rates
    """

Task(
    subagent_type="market-context-analyzer",
    model="claude-sonnet-4-5-20250929",
    description="Market conditions analysis",
    prompt=f"""
    Analyze current investment market conditions relevant to the user.

    User country: {country}
    User goal: {profile.get('goal', 'Not specified')}
    Risk tolerance: {profile['risk_tolerance']}

    {country_context_market}

    Analysis areas:
    1. Current interest rate environment (savings account attractiveness)
    2. Equity market valuation (index investing entry point)
    3. Real estate market trends (home buying timing)
    4. Inflation environment (real return perspective)

    Save the following JSON to /tmp/wealth-guide-market-{TS}.json:
    {{
      "status": "success",
      "agent": "market-context-analyzer",
      "country": "{country}",
      "market_summary": "2-3 sentence current market summary",
      "interest_rate_env": "high/medium/low (savings attractiveness)",
      "equity_valuation": "overvalued/fair/undervalued",
      "key_opportunities": ["opportunity1", "opportunity2"],
      "key_risks": ["risk1", "risk2"],
      "recommended_asset_allocation": {{
        "savings_accounts": savings allocation (%),
        "bonds": bonds allocation (%),
        "domestic_equity": domestic stocks (%),
        "international_equity": international stocks (%),
        "real_estate": real estate (%),
        "alternatives": alternatives (%)
      }}
    }}

    Use the Write tool to save the file.
    """
)
\```
```

- [ ] **Step 2: Write Phase 1 result reading section**

```markdown
\```python
# Read Phase 1 results - called AFTER all Task() calls above have completed
def read_agent_output(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

monthly_income = profile['annual_income'] / 12
default_surplus = monthly_income - profile['monthly_expense']

diag = read_agent_output(f"/tmp/wealth-guide-diagnostician-{TS}.json",
    {"status": "failed", "health_score": 50, "monthly_surplus": default_surplus,
     "diagnosis": "Diagnostic data unavailable", "strengths": [], "weaknesses": [], "recommended_investment_ratio": 20})

knowledge = read_agent_output(f"/tmp/wealth-guide-knowledge-{TS}.json",
    {"status": "failed", "user_level": "beginner", "matched_strategies": [],
     "learning_curriculum": [], "recommended_books": [],
     "selected_workflows": ["first-investment"],
     "curated_info": [], "key_insights": [], "tax_benefits": []})

market = read_agent_output(f"/tmp/wealth-guide-market-{TS}.json",
    {"status": "failed", "market_summary": "Market data unavailable", "key_opportunities": [], "key_risks": [],
     "recommended_asset_allocation": {"savings_accounts": 40, "bonds": 10, "domestic_equity": 20, "international_equity": 20, "real_estate": 10, "alternatives": 0}})

# Save Phase 1 combined
phase1 = {"diagnostician": diag, "knowledge": knowledge, "market": market, "profile": profile}
with open(f"/tmp/wealth-guide-phase1-{TS}.json", "w") as f:
    json.dump(phase1, f, ensure_ascii=False, indent=2)

print(f"Phase 1 complete - Health score: {diag.get('health_score', 'N/A')}, Level: {knowledge.get('user_level', 'N/A')}")
\```

---
```

- [ ] **Step 3: Verify market analyzer and results**

Confirm: S&P 500/TSX references (not KOSPI), `wealth-guide-` tmp file prefixes, English fallback messages, `matched_strategies` (not `matched_experts`) in knowledge fallback, asset allocation keys updated (`savings_accounts` not `deposits`, `international_equity` not `global_equity`).

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert market-context-analyzer to US/CA markets and update Phase 1 results"
```

---

### Task 7: Step 4 (Phase 2 - Wealth Strategist)

**Files:**
- Modify: `SKILL.md` (replace Phase 2-A wealth-strategist agent)

- [ ] **Step 1: Write wealth-strategist with expanded categories and country branching**

```markdown
### Step 4: Phase 2 - Sequential Strategy then Evaluation

wealth-strategist runs first with knowledge context (matched strategies), so strategies are grounded in real methodologies. risk-reward-evaluator then runs with those actual strategies.

\```python
print("Phase 2-A: Strategy generation (wealth-strategist)...")

country_context_strategist = ""
if country == "US":
    country_context_strategist = """
    Country: United States (USD)
    Retirement accounts: 401(k) ($23,500 limit), Traditional IRA ($7,000), Roth IRA ($7,000), HSA ($4,300 individual / $8,550 family)
    First home: FHA loan (3.5% down), down payment assistance programs
    Tax optimization: standard/itemized deduction, 0%/15%/20% long-term capital gains brackets, QBI deduction for self-employed
    Side hustle: Schedule C, 15.3% self-employment tax, quarterly estimated taxes
    College savings: 529 plans (state tax deduction)
    """
else:
    country_context_strategist = """
    Country: Canada (CAD)
    Retirement accounts: RRSP ($31,560 limit), TFSA ($7,000 limit), FHSA ($8,000/yr, $40,000 lifetime)
    First home: FHSA, RRSP Home Buyers' Plan ($60,000), First Home Buyer Incentive
    Tax optimization: basic personal amount, 50% capital gains inclusion, dividend tax credit, RRSP/TFSA decision framework
    Side hustle: T2125, CPP self-employed contributions, GST/HST registration at $30K
    Education savings: RESP (20% CESG match up to $500/yr)
    """

Task(
    subagent_type="wealth-strategist",
    model="claude-opus-4-6",
    description="Strategy generation",
    prompt=f"""
    Based on Phase 1 diagnosis and knowledge matching, generate 3-5 wealth-building strategies.

    Financial profile:
    {json.dumps(phase1['profile'], ensure_ascii=False)}

    Financial diagnosis:
    {json.dumps(phase1['diagnostician'], ensure_ascii=False)}

    Market conditions:
    {json.dumps(phase1['market'], ensure_ascii=False)}

    User level: {phase1['knowledge'].get('user_level', 'beginner')}

    Matched strategy methodologies (each strategy must be grounded in one of these):
    {json.dumps(phase1['knowledge'].get('matched_strategies', []), ensure_ascii=False)}

    Learning curriculum (include learning_prerequisites per strategy):
    {json.dumps(phase1['knowledge'].get('learning_curriculum', []), ensure_ascii=False)}

    Tax benefits:
    {json.dumps(phase1['knowledge'].get('tax_benefits', []), ensure_ascii=False)}

    {country_context_strategist}

    Strategy diversity requirements:
    - Risk range: must include low-risk + medium-risk + high-risk strategies
    - Time range: must include short-term (1yr) + mid-term (3yr) + long-term (10yr+)
    - Categories: at least 3 of these 7: investment / tax-optimization / side-hustle / career-growth / real-estate / debt-payoff / cost-saving
    - MUST include at least 1 tax optimization strategy

    Each strategy must include a strategy_source field:
    "strategy_source": {{
      "methodology": "methodology name",
      "key_principle": "core principle in one sentence",
      "citations": ["author1", "author2"]
    }}

    And a country_specific field:
    "country_specific": {{
      "accounts": ["relevant tax-advantaged accounts"],
      "tax_implications": "tax impact summary",
      "regulatory_notes": "any regulatory considerations"
    }}

    And a learning_prerequisites field:
    "learning_prerequisites": ["prerequisite1", "prerequisite2"]

    Save the following JSON to /tmp/wealth-guide-strategist-{TS}.json:
    {{
      "status": "success",
      "agent": "wealth-strategist",
      "country": "{country}",
      "strategies": [
        {{
          "id": "S1",
          "title": "Strategy name (methodology)",
          "category": "investment/tax-optimization/side-hustle/career-growth/real-estate/debt-payoff/cost-saving",
          "risk_level": "low/medium/high",
          "time_horizon": "short/mid/long",
          "expected_return": "annual X%",
          "initial_capital": initial capital needed,
          "monthly_commitment": "$ amount or hours per month",
          "description": "3-4 sentence strategy description with methodology reference",
          "strategy_source": {{"methodology": "...", "key_principle": "...", "citations": ["..."]}},
          "country_specific": {{"accounts": ["..."], "tax_implications": "...", "regulatory_notes": "..."}},
          "learning_prerequisites": ["...", "..."],
          "pros": ["pro1", "pro2"],
          "cons": ["con1", "con2"],
          "first_step": "Immediate actionable first step",
          "sources": []
        }}
      ]
    }}

    Use the Write tool to save the file.
    """
)

# Read strategist output before launching evaluator
strategist = read_agent_output(f"/tmp/wealth-guide-strategist-{TS}.json",
    {"status": "failed", "strategies": [
        {"id": "S1", "title": "Index Fund Investing (Passive Strategy)", "category": "investment", "risk_level": "medium",
         "time_horizon": "long", "expected_return": "annual 7-10%", "initial_capital": 0,
         "monthly_commitment": "$500/month",
         "description": "Dollar-cost average into a diversified index fund portfolio through tax-advantaged accounts.",
         "strategy_source": {"methodology": "Passive Index Investing", "key_principle": "Buy the whole market at low cost and hold long-term", "citations": ["John Bogle", "Burton Malkiel"]},
         "country_specific": {"accounts": ["401(k)", "Roth IRA"] if country == "US" else ["RRSP", "TFSA"], "tax_implications": "Tax-deferred or tax-free growth", "regulatory_notes": "Annual contribution limits apply"},
         "learning_prerequisites": ["Understanding compound interest", "Index fund basics"],
         "pros": ["Expert-validated methodology", "Tax advantages", "Fully automatable"], "cons": ["Requires long time horizon"],
         "first_step": "Open a brokerage account and set up automatic contributions", "sources": []}
    ]})

strategies = strategist.get("strategies", [])

# Guard against empty strategies list
if not strategies:
    default_accounts = ["HYSA", "401(k)"] if country == "US" else ["HISA", "TFSA"]
    strategies = [
        {"id": "S1", "title": "Emergency Fund + High-Yield Savings (Foundation)", "category": "cost-saving", "risk_level": "low",
         "time_horizon": "short", "expected_return": "annual 4-5%", "initial_capital": 0,
         "monthly_commitment": "$200/month",
         "description": "Build an emergency fund covering 3-6 months of expenses in a high-yield savings account before investing.",
         "strategy_source": {"methodology": "Emergency Fund First", "key_principle": "Build a financial safety net before investing", "citations": ["Dave Ramsey", "Elizabeth Warren"]},
         "country_specific": {"accounts": default_accounts, "tax_implications": "Interest is taxable income", "regulatory_notes": "FDIC/CDIC insured up to limits"},
         "learning_prerequisites": ["Budgeting basics"],
         "pros": ["Zero risk", "Immediate start"], "cons": ["Low returns"],
         "first_step": "Open a high-yield savings account", "sources": []}
    ]

print(f"Strategy generation complete - {len(strategies)} strategies")
\```
```

- [ ] **Step 2: Verify strategist changes**

Confirm: 7 strategy categories (not 4), `strategy_source` (not `expert_source`), `country_specific` field, US/CA account contribution limits are current, fallback strategies use country-aware accounts, `wealth-guide-` tmp prefix.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert wealth-strategist to 7 categories with US/CA tax account branching"
```

---

### Task 8: Step 4 (Phase 2 - Risk-Reward Evaluator + Phase 2 Results)

**Files:**
- Modify: `SKILL.md` (replace risk-reward-evaluator agent and Phase 2 result saving)

- [ ] **Step 1: Write risk-reward-evaluator agent**

```markdown
\```python
print("Phase 2-B: Risk/reward evaluation (risk-reward-evaluator)...")

Task(
    subagent_type="risk-reward-evaluator",
    model="claude-sonnet-4-5-20250929",
    description="Strategy risk/reward evaluation",
    prompt=f"""
    Evaluate the risk/reward of each strategy for this specific user.

    Financial profile:
    {json.dumps(phase1['profile'], ensure_ascii=False)}

    Health score: {phase1['diagnostician'].get('health_score', 50)}
    Monthly surplus: ${phase1['diagnostician'].get('monthly_surplus', 1000):,.0f}
    Risk tolerance: {phase1['profile']['risk_tolerance']}
    Country: {country}

    Strategies to evaluate (use each strategy's id and title exactly as given):
    {json.dumps(strategies, ensure_ascii=False)}

    Save the following JSON to /tmp/wealth-guide-evaluator-{TS}.json:
    {{
      "status": "success",
      "agent": "risk-reward-evaluator",
      "user_risk_capacity": "assessment of actual risk capacity",
      "evaluations": [
        {{
          "strategy_id": "exact id from strategist (e.g., S1)",
          "strategy_title": "exact title from strategist",
          "risk_score": 1-10,
          "reward_potential": "expected annual return range",
          "suitable_for_user": true/false,
          "suitability_reason": "reason for suitability assessment",
          "max_allocation": "maximum recommended allocation (%)"
        }}
      ],
      "overall_recommendation": "2-3 sentence overall portfolio direction"
    }}

    Use the Write tool to save the file.
    """
)

# Read evaluator output
evaluator = read_agent_output(f"/tmp/wealth-guide-evaluator-{TS}.json",
    {"status": "failed", "overall_recommendation": "A balanced, diversified approach is recommended to manage risk while building long-term wealth.", "evaluations": []})

phase2 = {"strategist": strategist, "evaluator": evaluator}
with open(f"/tmp/wealth-guide-phase2-{TS}.json", "w") as f:
    json.dump(phase2, f, ensure_ascii=False, indent=2)

print(f"Phase 2 complete - {len(strategies)} strategies evaluated")
\```

---
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert risk-reward-evaluator to English with USD/CAD formatting"
```

---

### Task 9: Step 5 (Strategy Selection)

**Files:**
- Modify: `SKILL.md` (replace strategy selection UI)

- [ ] **Step 1: Write strategy selection in English**

```markdown
### Step 5: Strategy Selection

\```python
# Display strategies with risk/reward summary and methodology source
strategy_options = []
for s in strategies:
    risk_label = {"low": "Low Risk", "medium": "Medium Risk", "high": "High Risk"}.get(s.get("risk_level"), "Medium Risk")
    horizon_label = {"short": "Short-term (1yr)", "mid": "Mid-term (3yr)", "long": "Long-term (10yr+)"}.get(s.get("time_horizon"), "Mid-term")
    methodology = s.get("strategy_source", {}).get("methodology", "")
    method_tag = f" [{methodology}]" if methodology else ""
    strategy_options.append({
        "label": s.get("title", f"Strategy {s.get('id', '?')}"),
        "description": f"{risk_label} | {horizon_label} | {s.get('expected_return', 'N/A')}{method_tag}"
    })

selected = AskUserQuestion(questions=[{
    "question": "Which strategy would you like to focus on first?",
    "header": "Strategy Selection",
    "options": strategy_options
}])

selected_title = selected.get("Strategy Selection")
chosen_strategy = next(
    (s for s in strategies if s.get("title") == selected_title),
    strategies[0] if strategies else {"title": "Default Strategy", "description": "Index fund investing"}
)
print(f"Selected strategy: {chosen_strategy.get('title')}")
\```

---
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert strategy selection UI to English"
```

---

### Task 10: Step 6 (Phase 3 - Action Plan Generation)

**Files:**
- Modify: `SKILL.md` (replace action-plan-generator agent)

- [ ] **Step 1: Write action-plan-generator with country-aware resources**

```markdown
### Step 6: Phase 3 - Action Plan Generation (Learning + Action + Workflow)

The action-plan-generator reads the roadmap template AND workflow files, producing a comprehensive 3-section roadmap.

\```python
print("Phase 3: Generating integrated learning + action + workflow roadmap...")

roadmap_path = f"{ROADMAP_DIR}/roadmap-{TS}.md"
template_path = os.path.expanduser("~/.claude/skills/wealth-guide/templates/roadmap-template.md")

# Read template
template_content = ""
try:
    with open(template_path) as f:
        template_content = f.read()
except FileNotFoundError:
    template_content = "(Template file not found - generate roadmap directly)"

# Prepare workflow file paths
selected_workflows = phase1['knowledge'].get('selected_workflows', ['first-investment'])
workflow_paths = [f"{WF_DIR}/{wf}" if wf.endswith('.md') else f"{WF_DIR}/{wf}.md" for wf in selected_workflows]

# Net worth calculation
net_worth = phase1['profile'].get('savings_midpoint', 0) + phase1['profile'].get('investment_midpoint', 0) - phase1['profile'].get('debt_midpoint', 0)

country_resources = ""
if country == "US":
    country_resources = """
    Key resources for US users:
    - Financial planner: letsmakeaplan.org
    - Tax authority: irs.gov
    - Investor education: investor.gov
    - Retirement calculator: ssa.gov/benefits/calculators
    - Free credit report: annualcreditreport.com
    """
else:
    country_resources = """
    Key resources for Canadian users:
    - Financial planner: fpcanada.ca
    - Tax authority: canada.ca/cra
    - Investor education: getsmarteraboutmoney.ca
    - Retirement calculator: canada.ca/cpp-calculator
    - Credit report: equifax.ca / transunion.ca
    """

Task(
    subagent_type="action-plan-generator",
    model="claude-opus-4-6",
    description="Integrated roadmap generation",
    prompt=f"""
    Create a 3-section integrated roadmap for the selected strategy:
    1. Learning Plan (what to learn first)
    2. Action Plan (what to do, week by week)
    3. Workflow (step-by-step execution order)

    Selected strategy:
    {json.dumps(chosen_strategy, ensure_ascii=False)}

    User level: {phase1['knowledge'].get('user_level', 'beginner')}
    Country: {country}

    Learning curriculum (from knowledge-advisor):
    {json.dumps(phase1['knowledge'].get('learning_curriculum', []), ensure_ascii=False)}

    Recommended books:
    {json.dumps(phase1['knowledge'].get('recommended_books', []), ensure_ascii=False)}

    Workflow files to read and integrate (use Read tool):
    {json.dumps(workflow_paths, ensure_ascii=False)}

    Financial context:
    - Monthly surplus: ${phase1['diagnostician'].get('monthly_surplus', 1000):,.0f}
    - Risk tolerance: {phase1['profile']['risk_tolerance']}
    - Goal: {phase1['profile'].get('goal', 'wealth building')}
    - Health score: {phase1['diagnostician'].get('health_score', 50)}
    - Strengths: {json.dumps(phase1['diagnostician'].get('strengths', []), ensure_ascii=False)}
    - Weaknesses: {json.dumps(phase1['diagnostician'].get('weaknesses', []), ensure_ascii=False)}
    - Net worth: ${net_worth:,.0f}

    Market conditions: {phase1['market'].get('market_summary', '')}

    Risk evaluation: {phase2['evaluator'].get('overall_recommendation', '')}

    Curated sources:
    {json.dumps(phase1['knowledge'].get('curated_info', [])[:3], ensure_ascii=False)}

    {country_resources}

    Roadmap template (fill all {{PLACEHOLDER}} values with actual content):
    {template_content}

    Save the completed markdown roadmap to {roadmap_path}.
    Read workflow files with the Read tool and integrate into the {{WORKFLOW_CONTENT}} section.
    Use the Write tool to save the file.
    Save to exactly this path: {roadmap_path}
    """
)

print(f"Phase 3 complete")
\```

---
```

- [ ] **Step 2: Verify action-plan-generator**

Confirm: country-aware resource links, net worth uses midpoint values (not raw bracket strings), currency formatting with `$`, `wealth-guide` paths, English template references.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert action-plan-generator to English with US/CA resource links"
```

---

### Task 11: Step 7 (Final Report + Session Recording + Cleanup)

**Files:**
- Modify: `SKILL.md` (replace final report, session recording, and cleanup)

- [ ] **Step 1: Write final report with country-aware disclaimer and resources**

```markdown
### Step 7: Display Final Report, Record Session & Cleanup

\```python
print("\n" + "="*60)
print("Wealth Roadmap Complete!")
print("="*60)

disclaimer_url = "https://www.letsmakeaplan.org/" if country == "US" else "https://fpcanada.ca/"
print(f"""
DISCLAIMER
This analysis is AI-generated reference information.
Investment decisions should be made based on your own judgment
and responsibility. Consult a qualified financial advisor before
making significant financial decisions.
Find a CFP: {disclaimer_url}
""")

user_level = phase1['knowledge'].get('user_level', 'N/A')
currency = "USD" if country == "US" else "CAD"
print(f"Country: {'United States' if country == 'US' else 'Canada'}")
print(f"User level: {user_level}")
print(f"Financial health score: {phase1['diagnostician'].get('health_score', 'N/A')}")
monthly_surplus = phase1['diagnostician'].get('monthly_surplus', 'N/A')
if isinstance(monthly_surplus, (int, float)):
    print(f"Monthly surplus: approx. ${monthly_surplus:,.0f} {currency}")
else:
    print(f"Monthly surplus: {monthly_surplus}")
print()
print(f"Selected strategy: {chosen_strategy.get('title')}")
strategy_source = chosen_strategy.get('strategy_source', {})
if strategy_source:
    print(f"Methodology: {strategy_source.get('methodology', '')} - {strategy_source.get('key_principle', '')}")
    citations = strategy_source.get('citations', [])
    if citations:
        print(f"Citations: {', '.join(citations)}")
print(f"Expected return: {chosen_strategy.get('expected_return', 'N/A')}")
print(f"Risk level: {chosen_strategy.get('risk_level', 'N/A')}")

# Show country-specific details
country_details = chosen_strategy.get('country_specific', {})
if country_details:
    accounts = country_details.get('accounts', [])
    if accounts:
        print(f"Recommended accounts: {', '.join(accounts)}")
    tax_note = country_details.get('tax_implications', '')
    if tax_note:
        print(f"Tax implications: {tax_note}")
print()

# Show learning curriculum summary
curriculum = phase1['knowledge'].get('learning_curriculum', [])
if curriculum:
    print("Learning plan summary:")
    for item in curriculum[:3]:
        print(f"  {item.get('order', '?')}. {item.get('topic', '')} ({item.get('estimated_time', '')})")
    print()

print(f"Generated roadmap: {roadmap_path}")
print()

# Show verified sources
sources = [s for s in phase1['knowledge'].get('curated_info', []) if s.get('verified')]
if sources:
    print("References:")
    for src in sources[:3]:
        print(f"  - {src.get('source', '')}: {src.get('title', '')} ({src.get('url', '')})")

print()
print("Next steps:")
print("1. Open the roadmap file above and review the learning plan")
print("2. Start the Week 1 checklist")
if country == "US":
    print("3. Find a CFP: https://www.letsmakeaplan.org/")
else:
    print("3. Find a CFP: https://fpcanada.ca/")

# Record session history to DB
try:
    matched_strats = json.dumps(phase1["knowledge"].get("matched_strategies", []), ensure_ascii=False)
    sel_workflows = json.dumps(phase1["knowledge"].get("selected_workflows", []), ensure_ascii=False)
    user_lvl = phase1["knowledge"].get("user_level", "beginner")
    strat_title = chosen_strategy.get("title", "")

    subprocess.run(["python3", "-c", f"""
import sqlite3, json
conn = sqlite3.connect('{DB_PATH}')
row = conn.execute("SELECT id FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
pid = row[0] if row else None
if pid:
    conn.execute('''INSERT INTO session_history
        (profile_id, user_level, selected_strategy, matched_strategies, selected_workflows, roadmap_path)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (pid, '{user_lvl}', '{strat_title}',
         '''{matched_strats}''',
         '''{sel_workflows}''',
         '{roadmap_path}'))
    conn.commit()
conn.close()
"""], check=True)
except (subprocess.CalledProcessError, OSError):
    pass  # Session tracking failure is non-critical

# Cleanup /tmp files for this session
import glob
for tmp_file in glob.glob(f"/tmp/wealth-guide-*-{TS}.json"):
    try:
        os.remove(tmp_file)
    except OSError:
        pass
\```
```

- [ ] **Step 2: Verify final report**

Confirm: English disclaimer, country-aware CFP links, `strategy_source` (not `expert_source`), `matched_strategies` (not `matched_experts`), `wealth-guide-` tmp prefix in cleanup glob, no Korean text anywhere.

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: convert final report and session recording to English with US/CA disclaimer"
```

---

### Task 12: Error Handling + Model Selection Tables

**Files:**
- Modify: `SKILL.md` (replace error handling and model selection tables at bottom)

- [ ] **Step 1: Write error handling and model selection in English**

```markdown
## Error Handling

| Error | Response |
|-------|----------|
| DB init failure | "Database initialization failed. Check python3 installation and retry." |
| agent-config.yaml missing | Continue with hardcoded defaults (no warning) |
| Knowledge base file missing | knowledge-advisor falls back to WebSearch only, default learning curriculum |
| Agent result file missing | Apply fallback defaults, show warning, continue |
| Empty strategies list | Auto-generate 1 default strategy (emergency fund + HYSA/HISA) |
| json.loads parse failure | Catch JSONDecodeError, use {"exists": False} default |
| Session recording failure | Ignore and continue (non-critical) |
| Free-text parse failure | Re-prompt user or use default ($75,000 income / $4,000 expenses) |

## Model Selection

| Agent | Model | Reason |
|-------|-------|--------|
| financial-diagnostician | claude-sonnet-4-5-20250929 | Numerical analysis |
| knowledge-advisor | claude-sonnet-4-5-20250929 | Knowledge matching + web search |
| market-context-analyzer | claude-sonnet-4-5-20250929 | Market analysis |
| wealth-strategist | claude-opus-4-6 | Strategy generation (complex reasoning) |
| risk-reward-evaluator | claude-sonnet-4-5-20250929 | Quantitative risk assessment |
| action-plan-generator | claude-opus-4-6 | Integrated roadmap generation |
```

- [ ] **Step 2: Final full-file review**

Read the entire SKILL.md from top to bottom and verify:
- Zero Korean text remains
- All paths use `wealth-guide` (not `rich-guide`)
- All tmp files use `wealth-guide-` prefix
- All currency references use `$` with country-aware `USD`/`CAD` labels
- `expert_source` -> `strategy_source` everywhere
- `matched_experts` -> `matched_strategies` everywhere
- 7 knowledge base files referenced (not 4)
- 7 strategy categories listed (not 4)
- DB schema uses `country`, `annual_income`, `experience` fields
- Country branching via conditional blocks in each agent prompt

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat: complete wealth-guide SKILL.md conversion from Korean to US/Canada English"
```

---

### Task 13: Final Integration Verification

**Files:**
- Read: `SKILL.md` (full file)
- Read: `docs/superpowers/specs/2026-04-16-wealth-guide-design.md`

- [ ] **Step 1: Spec coverage check**

Cross-reference every section of the spec against the SKILL.md:
- [ ] Metadata & triggers match spec
- [ ] 9-field interview matches spec (country, income, expenses, savings, investments, debt, risk, experience, goal)
- [ ] Country branching tables implemented in agent prompts (diagnostician, knowledge-advisor, market-analyzer, strategist)
- [ ] 7 knowledge base files referenced
- [ ] 7 strategy categories + diversity requirements
- [ ] `strategy_source` and `country_specific` fields in strategist output
- [ ] Data layer: profiles table has country, annual_income, experience columns
- [ ] Midpoint mappings match spec values
- [ ] Resource links match spec (letsmakeaplan.org, fpcanada.ca, etc.)
- [ ] Disclaimer matches spec
- [ ] Model selection matches spec

- [ ] **Step 2: Consistency check**

Verify type/name consistency across all tasks:
- `parse_currency()` function defined in Task 3, reused in Task 2 (refresh branch) - confirm same signature
- `read_agent_output()` function defined in Task 6, used in Tasks 7, 8 - confirm same signature
- `phase1` dict keys consistent: `diagnostician`, `knowledge`, `market`, `profile`
- `phase2` dict keys consistent: `strategist`, `evaluator`
- All agent tmp file paths use same `{TS}` timestamp variable

- [ ] **Step 3: Final commit with tag**

```bash
git add SKILL.md docs/
git commit -m "docs: add wealth-guide design spec and implementation plan"
```
