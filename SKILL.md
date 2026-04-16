---
name: wealth-guide
description: Use when user says "wealth guide", "financial plan", "investment strategy", "how to build wealth", "money strategy", "retirement planning", "side hustle ideas", or wants personalized wealth strategy. Conducts financial interview, runs 7-agent pipeline with expert knowledge base, and generates comprehensive learning + action + workflow roadmap.
version: 1.0.0
model: claude-sonnet-4-5-20250929
---

# Wealth Guide Skill

Personalized US/Canada/India wealth coaching via 7-agent multi-agent pipeline with curated strategy-focused knowledge base.

## Trigger Phrases

- "wealth guide"
- "financial plan"
- "investment strategy"
- "how to build wealth"
- "retirement planning"
- "side hustle ideas"
- "/wealth-guide"

## Execution Algorithm

### Step 1: Environment Setup & Config Load

```python
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
```

Decide data strategy based on loaded config thresholds:
- `existing["exists"]` AND `existing["age_days"] < CACHE_HOURS/24` -> offer reuse
- `existing["exists"]` AND `CACHE_HOURS/24 <= existing["age_days"] <= REFRESH_DAYS` -> offer refresh
- Otherwise -> new interview

---

### Step 2: Financial Interview (or Reuse / Refresh Existing)

```python
def parse_currency(val):
    """Strip $, commas, spaces and return float or None."""
    cleaned = str(val).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

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
                "question": f"Annual pre-tax income (current: ${existing['data'].get('annual_income', 0):,.0f}). Enter new amount or type 'same':",
                "header": "income_refresh"
            },
            {
                "question": f"Monthly expenses (current: ${existing['data'].get('monthly_expense', 0):,.0f}). Enter new amount or type 'same':",
                "header": "expense_refresh"
            }
        ])
        profile = dict(existing["data"])
        new_income = partial_responses.get("income_refresh", "same").strip()
        new_expense = partial_responses.get("expense_refresh", "same").strip()

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
    (country, age, annual_income, monthly_expense, savings, investment_assets,
     debt_credit_card, debt_personal_student, debt_mortgage,
     risk_tolerance, experience, goal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (d.get('country','US'), d.get('age',35), d.get('annual_income',75000), d.get('monthly_expense',4000),
     d.get('savings','$5,000 - $25,000'), d.get('investment_assets','None'),
     d.get('debt_credit_card','None'), d.get('debt_personal_student','None'),
     d.get('debt_mortgage','None'), d.get('risk_tolerance','medium'),
     d.get('experience','none'), d.get('goal','')))
conn.commit()
conn.close()
"""], check=True)

if profile is None:
    # ── Screen 1: About You (country + goal) ──
    about_you = AskUserQuestion(questions=[
        {
            "question": "Which country are you based in?",
            "header": "country",
            "multiSelect": False,
            "options": [
                {"label": "United States", "description": "US tax system, 401(k), IRA, etc."},
                {"label": "Canada", "description": "Canadian tax system, RRSP, TFSA, etc."},
                {"label": "India", "description": "Indian tax system, PPF, EPF, NPS, etc."}
            ]
        },
        {
            "question": "What is your age? (select a bracket or type your exact age)",
            "header": "age",
            "multiSelect": False,
            "options": [
                {"label": "Under 30", "description": "Will use 27 — or type exact age"},
                {"label": "30-39", "description": "Will use 35 — or type exact age"},
                {"label": "40-49", "description": "Will use 45 — or type exact age"},
                {"label": "50+", "description": "Will use 55 — or type exact age"}
            ]
        },
        {
            "question": "What is your primary financial goal?",
            "header": "goal",
            "multiSelect": False,
            "options": [
                {"label": "Build wealth long-term", "description": "Grow net worth steadily over 10+ years"},
                {"label": "Early retirement / FIRE", "description": "Financial independence, retire early"},
                {"label": "Buy a home", "description": "Save for a down payment (3-5 years)"},
                {"label": "Pay off debt", "description": "Eliminate high-interest or total debt"}
            ]
        }
    ])

    country_map = {"United States": "US", "Canada": "CA", "India": "IN"}
    country = country_map.get(about_you.get("country"), "US")
    age_raw = about_you.get("age", "35")
    # Parse age — handle bracket labels, exact numbers, or free-text
    age_bracket_map = {"Under 30": 27, "30-39": 35, "40-49": 45, "50+": 55}
    if age_raw in age_bracket_map:
        user_age = age_bracket_map[age_raw]
    else:
        try:
            user_age = int(str(age_raw).strip())
        except ValueError:
            import re
            nums = re.findall(r'\d+', str(age_raw))
            user_age = int(nums[0]) if nums else 35
    user_age = max(18, min(user_age, 80))  # Clamp to reasonable range

    # ── Screen 2: Income & Expenses (country-specific ranges) ──
    if country == "IN":
        income_options = [
            {"label": "Under ₹10L", "description": "Entry-level to mid career"},
            {"label": "₹10L - ₹25L", "description": "Mid to senior career"},
            {"label": "₹25L - ₹75L", "description": "Senior, specialist, or executive"},
            {"label": "Over ₹75L", "description": "C-suite, partner, or business owner"}
        ]
        expense_options = [
            {"label": "Under ₹25,000", "description": "Frugal or small city"},
            {"label": "₹25,000 - ₹50,000", "description": "Moderate spending"},
            {"label": "₹50,000 - ₹1,00,000", "description": "Comfortable metro lifestyle"},
            {"label": "Over ₹1,00,000", "description": "Premium lifestyle or large family"}
        ]
        default_income_coarse = "₹10L - ₹25L"
        default_expense = "₹25,000 - ₹50,000"
    else:
        income_options = [
            {"label": "Under $80,000", "description": "Entry-level to mid career"},
            {"label": "$80,000 - $150,000", "description": "Mid to senior career"},
            {"label": "$150,000 - $400,000", "description": "Senior, specialist, or executive"},
            {"label": "Over $400,000", "description": "C-suite, partner, or business owner"}
        ]
        expense_options = [
            {"label": "Under $3,000", "description": "Frugal or low cost of living"},
            {"label": "$3,000 - $5,000", "description": "Moderate spending"},
            {"label": "$5,000 - $8,000", "description": "Comfortable lifestyle"},
            {"label": "Over $8,000", "description": "High cost of living or family"}
        ]
        default_income_coarse = "$80,000 - $150,000"
        default_expense = "$3,000 - $5,000"

    income_expenses = AskUserQuestion(questions=[
        {
            "question": "What is your annual pre-tax household income?",
            "header": "income_range",
            "multiSelect": False,
            "options": income_options
        },
        {
            "question": "What are your total monthly living expenses?",
            "header": "monthly_expense",
            "multiSelect": False,
            "options": expense_options
        }
    ])

    income_coarse_label = income_expenses.get("income_range", default_income_coarse)
    expense_label = income_expenses.get("monthly_expense", default_expense)
    expense_midpoints = {
        "Under $3,000": 2000, "$3,000 - $5,000": 4000,
        "$5,000 - $8,000": 6500, "Over $8,000": 10000,
        # India (INR)
        "Under ₹25,000": 20000, "₹25,000 - ₹50,000": 37500,
        "₹50,000 - ₹1,00,000": 75000, "Over ₹1,00,000": 150000
    }
    monthly_expense = expense_midpoints.get(expense_label, 4000 if country != "IN" else 37500)

    # ── Screen 3: Narrow income range (country-specific) ──
    if country == "IN":
        income_sub_options = {
            "Under ₹10L": [
                {"label": "Under ₹4L", "description": "Entry-level or part-time"},
                {"label": "₹4L - ₹7L", "description": "Early career"},
                {"label": "₹7L - ₹10L", "description": "Mid career"}
            ],
            "₹10L - ₹25L": [
                {"label": "₹10L - ₹15L", "description": "Mid career"},
                {"label": "₹15L - ₹20L", "description": "Senior individual contributor"},
                {"label": "₹20L - ₹25L", "description": "Senior or lead"}
            ],
            "₹25L - ₹75L": [
                {"label": "₹25L - ₹40L", "description": "Senior or specialist"},
                {"label": "₹40L - ₹60L", "description": "Staff or principal level"},
                {"label": "₹60L - ₹75L", "description": "Director or executive"}
            ],
            "Over ₹75L": [
                {"label": "₹75L - ₹1Cr", "description": "VP or senior executive"},
                {"label": "₹1Cr - ₹2Cr", "description": "C-suite or partner"},
                {"label": "Over ₹2Cr", "description": "Top earner"}
            ]
        }
        default_sub = income_sub_options["₹10L - ₹25L"]
    else:
        income_sub_options = {
            "Under $80,000": [
                {"label": "Under $40,000", "description": "Entry-level or part-time"},
                {"label": "$40,000 - $60,000", "description": "Early career"},
                {"label": "$60,000 - $80,000", "description": "Mid career"}
            ],
            "$80,000 - $150,000": [
                {"label": "$80,000 - $100,000", "description": "Mid career"},
                {"label": "$100,000 - $125,000", "description": "Senior individual contributor"},
                {"label": "$125,000 - $150,000", "description": "Senior or lead"}
            ],
            "$150,000 - $400,000": [
                {"label": "$150,000 - $200,000", "description": "Senior or specialist"},
                {"label": "$200,000 - $250,000", "description": "Staff or principal level"},
                {"label": "$250,000 - $400,000", "description": "Director or executive"}
            ],
            "Over $400,000": [
                {"label": "$400,000 - $600,000", "description": "VP or senior executive"},
                {"label": "$600,000 - $1,000,000", "description": "C-suite or partner"},
                {"label": "Over $1,000,000", "description": "Top earner"}
            ]
        }
        default_sub = income_sub_options["$80,000 - $150,000"]

    income_narrow = AskUserQuestion(questions=[
        {
            "question": f"Can you narrow it down? (you selected {income_coarse_label})",
            "header": "annual_income",
            "multiSelect": False,
            "options": income_sub_options.get(income_coarse_label, default_sub)
        }
    ])

    income_midpoints = {
        # US/Canada (USD/CAD)
        "Under $40,000": 30000, "$40,000 - $60,000": 50000, "$60,000 - $80,000": 70000,
        "$80,000 - $100,000": 90000, "$100,000 - $125,000": 112500, "$125,000 - $150,000": 137500,
        "$150,000 - $200,000": 175000, "$200,000 - $250,000": 225000, "$250,000 - $400,000": 325000,
        "$400,000 - $600,000": 500000, "$600,000 - $1,000,000": 800000, "Over $1,000,000": 1500000,
        # India (INR — L = lakh = 100,000)
        "Under ₹4L": 300000, "₹4L - ₹7L": 550000, "₹7L - ₹10L": 850000,
        "₹10L - ₹15L": 1250000, "₹15L - ₹20L": 1750000, "₹20L - ₹25L": 2250000,
        "₹25L - ₹40L": 3250000, "₹40L - ₹60L": 5000000, "₹60L - ₹75L": 6750000,
        "₹75L - ₹1Cr": 8750000, "₹1Cr - ₹2Cr": 15000000, "Over ₹2Cr": 30000000
    }
    income_label = income_narrow.get("annual_income", "$80,000 - $100,000" if country != "IN" else "₹10L - ₹15L")
    annual_income = income_midpoints.get(income_label, 90000 if country != "IN" else 1250000)

    # ── Screen 4: Savings & Investments (coarse, country-specific) ──
    if country == "IN":
        savings_options = [
            {"label": "Under ₹1L", "description": "Building an emergency fund"},
            {"label": "₹1L - ₹10L", "description": "Solid cash reserves"},
            {"label": "₹10L - ₹50L", "description": "Large cash position"},
            {"label": "Over ₹50L", "description": "Substantial liquid wealth"}
        ]
        invest_options = [
            {"label": "Under ₹5L", "description": "Getting started or building"},
            {"label": "₹5L - ₹25L", "description": "Growing portfolio"},
            {"label": "₹25L - ₹1Cr", "description": "Substantial portfolio"},
            {"label": "Over ₹1Cr", "description": "Crore-plus portfolio"}
        ]
        default_savings_coarse = "Under ₹1L"
        default_invest_coarse = "Under ₹5L"
    else:
        savings_options = [
            {"label": "Under $15,000", "description": "Building an emergency fund"},
            {"label": "$15,000 - $100,000", "description": "Solid cash reserves"},
            {"label": "$100,000 - $500,000", "description": "Large cash position"},
            {"label": "Over $500,000", "description": "Substantial liquid wealth"}
        ]
        invest_options = [
            {"label": "Under $50,000", "description": "Getting started or building"},
            {"label": "$50,000 - $250,000", "description": "Growing portfolio"},
            {"label": "$250,000 - $1,000,000", "description": "Substantial portfolio"},
            {"label": "Over $1,000,000", "description": "Seven-figure portfolio"}
        ]
        default_savings_coarse = "Under $15,000"
        default_invest_coarse = "Under $50,000"

    assets_coarse = AskUserQuestion(questions=[
        {
            "question": "How much do you have in savings (cash, savings accounts, FDs/GICs/CDs)?",
            "header": "savings_range",
            "multiSelect": False,
            "options": savings_options
        },
        {
            "question": "Total investment assets (retirement accounts, stocks, bonds, funds)?",
            "header": "invest_range",
            "multiSelect": False,
            "options": invest_options
        }
    ])

    # ── Screen 5: Narrow savings & investments (country-specific) ──
    savings_coarse = assets_coarse.get("savings_range", default_savings_coarse)
    if country == "IN":
        savings_sub_options = {
            "Under ₹1L": [
                {"label": "Under ₹10,000", "description": "Just getting started"},
                {"label": "₹10,000 - ₹50,000", "description": "Building a buffer"},
                {"label": "₹50,000 - ₹1L", "description": "Starter emergency fund"}
            ],
            "₹1L - ₹10L": [
                {"label": "₹1L - ₹3L", "description": "3-6 month emergency fund"},
                {"label": "₹3L - ₹5L", "description": "Full emergency fund + buffer"},
                {"label": "₹5L - ₹10L", "description": "Strong cash position"}
            ],
            "₹10L - ₹50L": [
                {"label": "₹10L - ₹25L", "description": "Large cash reserves"},
                {"label": "₹25L - ₹50L", "description": "Very large cash position"}
            ],
            "Over ₹50L": [
                {"label": "₹50L - ₹1Cr", "description": "Major cash holdings"},
                {"label": "Over ₹1Cr", "description": "Ultra-high cash position"}
            ]
        }
        default_savings_sub = savings_sub_options["Under ₹1L"]
    else:
        savings_sub_options = {
            "Under $15,000": [
                {"label": "Under $1,000", "description": "Just getting started"},
                {"label": "$1,000 - $5,000", "description": "Building a buffer"},
                {"label": "$5,000 - $15,000", "description": "Starter emergency fund"}
            ],
            "$15,000 - $100,000": [
                {"label": "$15,000 - $30,000", "description": "3-6 month emergency fund"},
                {"label": "$30,000 - $50,000", "description": "Full emergency fund + buffer"},
                {"label": "$50,000 - $100,000", "description": "Strong cash position"}
            ],
            "$100,000 - $500,000": [
                {"label": "$100,000 - $250,000", "description": "Large cash reserves"},
                {"label": "$250,000 - $500,000", "description": "Very large cash position"}
            ],
            "Over $500,000": [
                {"label": "$500,000 - $1,000,000", "description": "Major cash holdings"},
                {"label": "Over $1,000,000", "description": "Ultra-high cash position"}
            ]
        }
        default_savings_sub = savings_sub_options["Under $15,000"]

    invest_coarse = assets_coarse.get("invest_range", default_invest_coarse)
    if country == "IN":
        invest_sub_options = {
            "Under ₹5L": [
                {"label": "None", "description": "Haven't started investing"},
                {"label": "Under ₹1L", "description": "Just getting started"},
                {"label": "₹1L - ₹5L", "description": "Building portfolio"}
            ],
            "₹5L - ₹25L": [
                {"label": "₹5L - ₹10L", "description": "Growing portfolio"},
                {"label": "₹10L - ₹15L", "description": "Solid investment base"},
                {"label": "₹15L - ₹25L", "description": "Strong portfolio"}
            ],
            "₹25L - ₹1Cr": [
                {"label": "₹25L - ₹50L", "description": "Substantial portfolio"},
                {"label": "₹50L - ₹75L", "description": "Large portfolio"},
                {"label": "₹75L - ₹1Cr", "description": "Approaching crore club"}
            ],
            "Over ₹1Cr": [
                {"label": "₹1Cr - ₹2Cr", "description": "Crorepati investor"},
                {"label": "Over ₹2Cr", "description": "High-net-worth investor"}
            ]
        }
        default_invest_sub = invest_sub_options["Under ₹5L"]
    else:
        invest_sub_options = {
            "Under $50,000": [
                {"label": "None", "description": "Haven't started investing"},
                {"label": "Under $10,000", "description": "Just getting started"},
                {"label": "$10,000 - $50,000", "description": "Building portfolio"}
            ],
            "$50,000 - $250,000": [
                {"label": "$50,000 - $100,000", "description": "Growing portfolio"},
                {"label": "$100,000 - $175,000", "description": "Solid investment base"},
                {"label": "$175,000 - $250,000", "description": "Strong portfolio"}
            ],
            "$250,000 - $1,000,000": [
                {"label": "$250,000 - $500,000", "description": "Substantial portfolio"},
                {"label": "$500,000 - $750,000", "description": "Large portfolio"},
                {"label": "$750,000 - $1,000,000", "description": "Approaching 7 figures"}
            ],
            "Over $1,000,000": [
                {"label": "$1,000,000 - $2,000,000", "description": "Millionaire investor"},
                {"label": "Over $2,000,000", "description": "High-net-worth investor"}
            ]
        }
        default_invest_sub = invest_sub_options["Under $50,000"]

    narrow_si = AskUserQuestion(questions=[
        {
            "question": f"Narrow your savings ({savings_coarse}):",
            "header": "savings",
            "multiSelect": False,
            "options": savings_sub_options.get(savings_coarse, default_savings_sub)
        },
        {
            "question": f"Narrow your investments ({invest_coarse}):",
            "header": "investment_assets",
            "multiSelect": False,
            "options": invest_sub_options.get(invest_coarse, default_invest_sub)
        }
    ])

    # ── Screen 6: Debt (conditional — skip if no debt) ──
    debt_check = AskUserQuestion(questions=[{
        "question": "Do you have any outstanding debt?",
        "header": "has_debt",
        "multiSelect": False,
        "options": [
            {"label": "No debt", "description": "Completely debt-free"},
            {"label": "Yes", "description": "One or more types of debt"}
        ]
    }])

    has_debt = debt_check.get("has_debt", "No debt")
    debt_cc_label = "None"
    debt_ps_label = "None"
    debt_mortgage_label = "None"
    home_value_label = "None"

    if has_debt == "Yes":
        # ── Screen 7: Debt types (multiSelect, country-specific APR descriptions) ──
        if country == "IN":
            cc_desc = "Revolving balances (typically 36-42% APR)"
            loan_desc = "Personal, car, education, or gold loans"
            mortgage_desc = "Home loan"
        else:
            cc_desc = "Revolving balances (typically 19-29% APR)"
            loan_desc = "Personal, car, student loans, or lines of credit"
            mortgage_desc = "Home mortgage or HELOC"

        debt_types = AskUserQuestion(questions=[{
            "question": "Which types of debt do you have? (select all that apply)",
            "header": "debt_types",
            "multiSelect": True,
            "options": [
                {"label": "Credit card", "description": cc_desc},
                {"label": "Loans", "description": loan_desc},
                {"label": "Mortgage", "description": mortgage_desc}
            ]
        }])

        debt_types_selected = debt_types.get("debt_types", "")

        # ── Screen 8: Debt amounts (country-specific ranges) ──
        debt_questions = []

        if "Credit card" in debt_types_selected:
            if country == "IN":
                cc_options = [
                    {"label": "Under ₹50,000", "description": "Minor — payable in 1-2 months"},
                    {"label": "₹50,000 - ₹2L", "description": "Moderate — reduce aggressively"},
                    {"label": "₹2L - ₹5L", "description": "Significant — high interest adding up"},
                    {"label": "Over ₹5L", "description": "Urgent — priority to eliminate"}
                ]
            else:
                cc_options = [
                    {"label": "Under $2,000", "description": "Minor — payable in 1-2 months"},
                    {"label": "$2,000 - $5,000", "description": "Moderate — consider balance transfer"},
                    {"label": "$5,000 - $15,000", "description": "Significant — high interest adding up"},
                    {"label": "Over $15,000", "description": "Urgent — priority to eliminate"}
                ]
            debt_questions.append({
                "question": "Total credit card balance?",
                "header": "debt_cc",
                "multiSelect": False,
                "options": cc_options
            })

        if "Loans" in debt_types_selected:
            if country == "IN":
                loan_options = [
                    {"label": "Under ₹2L", "description": "Small balance"},
                    {"label": "₹2L - ₹10L", "description": "Typical personal or car loan"},
                    {"label": "₹10L - ₹30L", "description": "Significant — education or large personal loan"},
                    {"label": "Over ₹30L", "description": "Large combined loan debt"}
                ]
            else:
                loan_options = [
                    {"label": "Under $10,000", "description": "Small balance"},
                    {"label": "$10,000 - $30,000", "description": "Typical car loan or partial student debt"},
                    {"label": "$30,000 - $75,000", "description": "Significant loan balance"},
                    {"label": "Over $75,000", "description": "Large combined loan debt"}
                ]
            debt_questions.append({
                "question": "Total personal / car / education loans?",
                "header": "debt_ps",
                "multiSelect": False,
                "options": loan_options
            })

        if "Mortgage" in debt_types_selected:
            if country == "IN":
                mortgage_options = [
                    {"label": "Under ₹25L", "description": "Small or nearly paid off"},
                    {"label": "₹25L - ₹50L", "description": "Standard home loan"},
                    {"label": "₹50L - ₹1Cr", "description": "Mid to large home loan"},
                    {"label": "Over ₹1Cr", "description": "Large home loan"}
                ]
            else:
                mortgage_options = [
                    {"label": "Under $200,000", "description": "Small or nearly paid off"},
                    {"label": "$200,000 - $400,000", "description": "Standard mortgage"},
                    {"label": "$400,000 - $700,000", "description": "Mid to large mortgage"},
                    {"label": "Over $700,000", "description": "Large mortgage"}
                ]
            debt_questions.append({
                "question": "Outstanding mortgage / home loan balance?",
                "header": "debt_mortgage",
                "multiSelect": False,
                "options": mortgage_options
            })

        if debt_questions:
            debt_amounts = AskUserQuestion(questions=debt_questions)
            debt_cc_label = debt_amounts.get("debt_cc", "None")
            debt_ps_label = debt_amounts.get("debt_ps", "None")
            debt_mortgage_label = debt_amounts.get("debt_mortgage", "None")

        # ── Screen 9: Home value (only if mortgage, country-specific) ──
        if "Mortgage" in debt_types_selected:
            if country == "IN":
                home_options = [
                    {"label": "Under ₹50L", "description": "Affordable housing or tier-2 city"},
                    {"label": "₹50L - ₹1Cr", "description": "Standard home in metro"},
                    {"label": "₹1Cr - ₹2Cr", "description": "Premium or prime location"},
                    {"label": "Over ₹2Cr", "description": "Luxury or prime metro property"}
                ]
                default_home = "Under ₹50L"
            else:
                home_options = [
                    {"label": "Under $400,000", "description": "Starter home or smaller market"},
                    {"label": "$400,000 - $700,000", "description": "Average home in most markets"},
                    {"label": "$700,000 - $1,200,000", "description": "Above-average or metro area"},
                    {"label": "Over $1,200,000", "description": "High-value or premium market"}
                ]
                default_home = "Under $400,000"

            home_value_response = AskUserQuestion(questions=[{
                "question": "Estimated current value of your home?",
                "header": "home_value",
                "multiSelect": False,
                "options": home_options
            }])
            home_value_label = home_value_response.get("home_value", default_home)

    home_value_label = home_value_label if debt_mortgage_label != "None" else "None"

    assets_debt = {
        "savings": narrow_si.get("savings", "Under $1,000"),
        "investment_assets": narrow_si.get("investment_assets", "None"),
        "debt_credit_card": debt_cc_label,
        "debt_personal_student": debt_ps_label,
        "debt_mortgage": debt_mortgage_label
    }

    # ── Screen 10: Risk & Experience ──
    preferences = AskUserQuestion(questions=[
        {
            "question": "How would you describe your risk tolerance?",
            "header": "risk_tolerance",
            "multiSelect": False,
            "options": [
                {"label": "Conservative", "description": "Protect what I have — savings accounts, bonds, fixed deposits"},
                {"label": "Balanced", "description": "Steady growth — index funds, some stocks"},
                {"label": "Aggressive", "description": "Maximize growth — stocks, crypto, higher volatility OK"}
            ]
        },
        {
            "question": "How would you rate your investing experience?",
            "header": "experience",
            "multiSelect": False,
            "options": [
                {"label": "Beginner", "description": "New to investing or just have a savings account"},
                {"label": "Intermediate", "description": "I invest regularly in stocks or funds"},
                {"label": "Advanced", "description": "I manage a diversified portfolio across asset classes"}
            ]
        }
    ])

    risk_map = {"Conservative": "low", "Balanced": "medium", "Aggressive": "high"}
    experience_map = {"Beginner": "beginner", "Intermediate": "intermediate", "Advanced": "advanced"}

    profile = {
        "country": country,
        "age": user_age,
        "annual_income": annual_income,
        "monthly_expense": monthly_expense,
        "savings": assets_debt.get("savings", "Under $1,000"),
        "investment_assets": assets_debt.get("investment_assets", "None"),
        "debt_credit_card": assets_debt.get("debt_credit_card", "None"),
        "debt_personal_student": assets_debt.get("debt_personal_student", "None"),
        "debt_mortgage": assets_debt.get("debt_mortgage", "None"),
        "home_value": home_value_label,
        "risk_tolerance": risk_map.get(preferences.get("risk_tolerance", "Balanced"), "medium"),
        "experience": experience_map.get(preferences.get("experience", "Beginner"), "beginner"),
        "goal": about_you.get("goal", "Build wealth long-term")
    }
    # Midpoints, tax estimates, and derived fields are computed in the shared block below

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
    (country, age, annual_income, monthly_expense, savings, investment_assets,
     debt_credit_card, debt_personal_student, debt_mortgage,
     risk_tolerance, experience, goal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
    (d['country'], d.get('age', 35), d['annual_income'], d['monthly_expense'], d['savings'],
     d['investment_assets'], d.get('debt_credit_card', 'None'),
     d.get('debt_personal_student', 'None'), d.get('debt_mortgage', 'None'),
     d['risk_tolerance'], d['experience'], d['goal']))
conn.commit()
conn.close()
import os
os.remove('{profile_tmp}')
print("saved")
"""], check=True)

    print(f"Financial profile saved")
```

#### Derive All Calculated Fields (runs for ALL paths: fresh, reuse, and refresh)

This block MUST run after profile is set — whether from a fresh interview, DB reuse, or partial refresh. It computes midpoints, tax estimates, surplus, and net worth fields that every downstream agent requires.

```python
# ── Derived field calculation (runs for all paths) ──
# If profile came from DB reuse/refresh, it only has raw fields.
# Recompute all midpoints and derived fields here.

country = profile.get('country', 'US')
currency_map = {"US": "USD", "CA": "CAD", "IN": "INR"}
currency = currency_map.get(country, "USD")

savings_midpoints = {
    # US/Canada (USD/CAD)
    "Under $1,000": 500, "$1,000 - $5,000": 3000, "$5,000 - $15,000": 10000,
    "$15,000 - $30,000": 22500, "$30,000 - $50,000": 40000, "$50,000 - $100,000": 75000,
    "$100,000 - $250,000": 175000, "$250,000 - $500,000": 375000,
    "$500,000 - $1,000,000": 750000, "Over $1,000,000": 1500000,
    # India (INR)
    "Under ₹10,000": 5000, "₹10,000 - ₹50,000": 30000, "₹50,000 - ₹1L": 75000,
    "₹1L - ₹3L": 200000, "₹3L - ₹5L": 400000, "₹5L - ₹10L": 750000,
    "₹10L - ₹25L": 1750000, "₹25L - ₹50L": 3750000,
    "₹50L - ₹1Cr": 7500000, "Over ₹1Cr": 15000000
}
investment_midpoints = {
    # US/Canada
    "None": 0, "Under $10,000": 5000, "$10,000 - $50,000": 30000,
    "$50,000 - $100,000": 75000, "$100,000 - $175,000": 137500, "$175,000 - $250,000": 212500,
    "$250,000 - $500,000": 375000, "$500,000 - $750,000": 625000,
    "$750,000 - $1,000,000": 875000, "$1,000,000 - $2,000,000": 1500000, "Over $2,000,000": 3000000,
    # India (INR)
    "Under ₹1L": 50000, "₹1L - ₹5L": 300000,
    "₹5L - ₹10L": 750000, "₹10L - ₹15L": 1250000, "₹15L - ₹25L": 2000000,
    "₹25L - ₹50L": 3750000, "₹50L - ₹75L": 6250000,
    "₹75L - ₹1Cr": 8750000, "₹1Cr - ₹2Cr": 15000000, "Over ₹2Cr": 30000000
}
debt_cc_midpoints = {
    # US/Canada
    "None": 0, "Under $2,000": 1000, "$2,000 - $5,000": 3500,
    "$5,000 - $15,000": 10000, "Over $15,000": 25000,
    # India (INR)
    "Under ₹50,000": 25000, "₹50,000 - ₹2L": 125000,
    "₹2L - ₹5L": 350000, "Over ₹5L": 750000
}
debt_ps_midpoints = {
    # US/Canada
    "None": 0, "Under $10,000": 5000, "$10,000 - $30,000": 20000,
    "$30,000 - $75,000": 52500, "Over $75,000": 125000,
    # India (INR)
    "Under ₹2L": 100000, "₹2L - ₹10L": 600000,
    "₹10L - ₹30L": 2000000, "Over ₹30L": 5000000
}
debt_mortgage_midpoints = {
    # US/Canada
    "None": 0, "Under $200,000": 100000, "$200,000 - $400,000": 300000,
    "$400,000 - $700,000": 550000, "Over $700,000": 900000,
    # India (INR)
    "Under ₹25L": 1250000, "₹25L - ₹50L": 3750000,
    "₹50L - ₹1Cr": 7500000, "Over ₹1Cr": 15000000
}
home_value_midpoints = {
    # US/Canada
    "None": 0, "Under $400,000": 300000, "$400,000 - $700,000": 550000,
    "$700,000 - $1,200,000": 950000, "Over $1,200,000": 1500000,
    # India (INR)
    "Under ₹50L": 3000000, "₹50L - ₹1Cr": 7500000,
    "₹1Cr - ₹2Cr": 15000000, "Over ₹2Cr": 30000000
}

# Compute midpoints (safe to re-run — idempotent)
profile['savings_midpoint'] = savings_midpoints.get(profile.get('savings', 'Under $1,000'), 3000)
profile['investment_midpoint'] = investment_midpoints.get(profile.get('investment_assets', 'None'), 0)
profile['debt_cc_midpoint'] = debt_cc_midpoints.get(profile.get('debt_credit_card', 'None'), 0)
profile['debt_ps_midpoint'] = debt_ps_midpoints.get(profile.get('debt_personal_student', 'None'), 0)
profile['debt_mortgage_midpoint'] = debt_mortgage_midpoints.get(profile.get('debt_mortgage', 'None'), 0)
profile['total_debt_midpoint'] = profile['debt_cc_midpoint'] + profile['debt_ps_midpoint'] + profile['debt_mortgage_midpoint']

# Home value and real estate equity
home_value_label = profile.get('home_value', 'None')
if profile.get('debt_mortgage', 'None') == 'None':
    home_value_label = 'None'
profile['home_value'] = home_value_label
profile['home_value_midpoint'] = home_value_midpoints.get(home_value_label, 0)
# Allow negative equity (underwater mortgage)
profile['real_estate_equity'] = profile['home_value_midpoint'] - profile['debt_mortgage_midpoint']

# Tax estimation
annual_income = profile.get('annual_income', 75000)
monthly_income = annual_income / 12

if country == "US":
    if annual_income < 50000: est_tax_rate = 0.18
    elif annual_income < 100000: est_tax_rate = 0.22
    elif annual_income < 200000: est_tax_rate = 0.28
    elif annual_income < 400000: est_tax_rate = 0.30
    else: est_tax_rate = 0.33
elif country == "CA":  # Canada
    if annual_income < 55000: est_tax_rate = 0.20
    elif annual_income < 110000: est_tax_rate = 0.28
    elif annual_income < 155000: est_tax_rate = 0.32
    elif annual_income < 220000: est_tax_rate = 0.36
    else: est_tax_rate = 0.39
else:  # India (new regime effective rates including 4% cess)
    # Thresholds in INR — user income is already in INR from interview
    if annual_income < 700000: est_tax_rate = 0.0       # Under ₹7L — rebate u/s 87A makes tax nil
    elif annual_income < 1000000: est_tax_rate = 0.08    # ₹7-10L effective ~8%
    elif annual_income < 1500000: est_tax_rate = 0.12    # ₹10-15L effective ~12%
    elif annual_income < 2000000: est_tax_rate = 0.16    # ₹15-20L effective ~16%
    elif annual_income < 3000000: est_tax_rate = 0.20    # ₹20-30L effective ~20%
    elif annual_income < 5000000: est_tax_rate = 0.25    # ₹30-50L effective ~25%
    else: est_tax_rate = 0.30                            # ₹50L+ effective ~30% (with surcharge + cess)

monthly_tax = monthly_income * est_tax_rate
monthly_net_income = monthly_income - monthly_tax
monthly_expense = profile.get('monthly_expense', 4000)
monthly_surplus = monthly_net_income - monthly_expense

profile['est_tax_rate'] = est_tax_rate
profile['monthly_tax'] = monthly_tax
profile['monthly_net_income'] = monthly_net_income
profile['monthly_surplus'] = monthly_surplus
profile['annual_tax'] = annual_income * est_tax_rate
profile['annual_surplus'] = monthly_surplus * 12

# Ensure age_label exists
if 'age_label' not in profile:
    profile['age_label'] = str(profile.get('age', 35))

print(f"Gross monthly: ${monthly_income:,.0f} | Tax (~{est_tax_rate:.0%}): ${monthly_tax:,.0f} | Net: ${monthly_net_income:,.0f}")
print(f"Monthly surplus after expenses: approx. ${monthly_surplus:,.0f} {currency}")
```

---

### Step 3: Phase 1 - Parallel Diagnosis + Knowledge Matching

Launch all 3 Phase 1 agents simultaneously. All three Task() calls must appear in a single response block so Claude Code executes them in parallel. The knowledge-advisor combines knowledge base reading with web search.

```python
print("Phase 1: Diagnosis + Knowledge Matching (3 agents in parallel)...")

experience = profile.get("experience", "none")
country = profile.get("country", "US")
currency = {"US": "USD", "CA": "CAD", "IN": "INR"}.get(country, "USD")
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
elif country == "CA":
    country_context_diagnostician = """
    Country-specific rules (Canada):
    - Debt ratios: GDS <= 32%, TDS <= 40%
    - High-interest debt: >20% APR (credit cards)
    - Emergency fund: 3-6 months expenses in HISA or GIC
    - Savings rate benchmark: 20%+
    """
else:  # India
    country_context_diagnostician = """
    Country-specific rules (India):
    - Debt-to-income threshold: EMI-to-income ratio <= 40% is healthy, >50% is concerning
    - High-interest debt: >20% APR (credit cards at 36-42% APR are highest priority)
    - Emergency fund: 6-12 months expenses (higher due to no unemployment insurance) in savings account + liquid mutual funds
    - Savings rate benchmark: 30%+ (no social safety net, must self-fund retirement)
    - Gold loans (7-10%) are cheaper than personal loans (12-24%) — factor into debt strategy
    - All amounts in INR (Indian Rupees)
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
    - Age: {profile.get('age', '--')} (exact age)
    - Annual income: ${profile['annual_income']:,.0f}
    - Monthly gross income: ${monthly_income:,.0f}
    - Estimated tax rate: {profile['est_tax_rate']:.0%} (effective, federal + state/provincial)
    - Monthly estimated tax: ${profile['monthly_tax']:,.0f}
    - Monthly net income (after tax): ${profile['monthly_net_income']:,.0f}
    - Monthly living expenses: ${profile['monthly_expense']:,.0f}
    - Monthly surplus (net income - expenses): ${profile['monthly_surplus']:,.0f}
    - Savings: {profile['savings']} (midpoint: ${profile['savings_midpoint']:,.0f})
    - Investment assets: {profile['investment_assets']} (midpoint: ${profile['investment_midpoint']:,.0f})
    - Debt — Credit card: {profile['debt_credit_card']} (midpoint: ${profile['debt_cc_midpoint']:,.0f})
    - Debt — Personal/student loans: {profile['debt_personal_student']} (midpoint: ${profile['debt_ps_midpoint']:,.0f})
    - Debt — Mortgage: {profile['debt_mortgage']} (midpoint: ${profile['debt_mortgage_midpoint']:,.0f})
    - Total debt midpoint: ${profile['total_debt_midpoint']:,.0f}
    - Risk tolerance: {profile['risk_tolerance']}
    - Goal: {profile.get('goal', 'Not specified')}

    Debt analysis guidelines:
    - Credit card debt: highest priority (19-29% APR). Calculate monthly interest cost. Recommend avalanche or snowball.
    - Personal/student loans: medium priority (4-10% APR). Consider refinancing, income-driven repayment (US), or consolidation.
    - Mortgage: lowest priority (productive leverage). Focus on rate, renewal timing, prepayment vs investing tradeoff.
    - Calculate debt-to-income (DTI) as: estimated total monthly debt PAYMENTS / monthly gross income. Estimate mortgage/home loan payment using standard amortization (25yr CA, 30yr US, 20yr IN) at current rates. CC minimum ~3% of balance (India: ~5% due to higher APR). Loan payments estimated from balance and typical terms. The benchmark is <36% (monthly payments, NOT total balance) for US/CA, <40% EMI-to-income for India. Flag high-interest debt separately.

    {country_context_diagnostician}

    Save the following JSON to /tmp/wealth-guide-diagnostician-{TS}.json:
    {{
      "status": "success",
      "agent": "financial-diagnostician",
      "country": "{country}",
      "health_score": 0-100,
      "monthly_surplus": monthly surplus in {currency},
      "savings_rate": savings rate (%),
      "debt_ratio": debt-to-income ratio (%) — calculated as monthly debt PAYMENTS / monthly gross income (NOT total balance / income),
      "emergency_fund_months": months of expenses covered by savings,
      "diagnosis": "2-3 sentence summary of financial health",
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"],
      "recommended_investment_ratio": recommended % of surplus to invest
    }}

    Use the Write tool to save the file.
    """
)

country_context_knowledge = ""
if country == "US":
    country_context_knowledge = """
    Country: United States
    Tax-advantaged accounts: 401(k), Traditional IRA, Roth IRA, HSA, 529
    Common index funds: VTI, VXUS, VOO, BND, target-date funds
    Tax-loss harvesting: wash sale rule (30 days)
    Employer match: 401(k) match
    """
elif country == "CA":
    country_context_knowledge = """
    Country: Canada
    Tax-advantaged accounts: RRSP, TFSA, RESP, FHSA
    Common index funds: VEQT, XEQT, VCN, ZAG, VBAL
    Tax-loss harvesting: superficial loss rule (30 days)
    Employer match: RRSP group match / DPSP
    """
else:  # India
    country_context_knowledge = """
    Country: India
    Tax-advantaged accounts: EPF, PPF, NPS (80CCD), ELSS (80C), SCSS, Sukanya Samriddhi
    Common index funds: UTI Nifty 50 (Direct), HDFC Nifty 50 (Direct), Motilal Oswal Nifty Next 50, Motilal Oswal S&P 500
    Tax deductions: Section 80C (₹1.5L), 80D (₹25-50K health), 80CCD(1B) (₹50K NPS), 80E (education loan interest), 24(b) (₹2L home loan interest)
    Tax-loss harvesting: No superficial loss rule in India — can rebuy immediately
    Employer match: EPF employer contribution (12% of basic)
    Tax regime choice: Old regime (full deductions) vs New regime (lower rates, limited deductions)
    Gold: Sovereign Gold Bonds (SGB) — 2.5% interest + zero LTCG if held to maturity
    """

Task(
    subagent_type="knowledge-advisor",
    model="claude-sonnet-4-5-20250929",
    description="Knowledge base matching + learning curriculum",
    prompt=f"""
    Match the user's profile to strategy-focused methodologies and generate a learning curriculum.

    User profile:
    - Country: {country}
    - Age: {profile.get('age', '--')} (exact age)
    - Annual income: ${profile['annual_income']:,.0f}
    - Savings: {profile['savings']} (midpoint: ${profile['savings_midpoint']:,.0f})
    - Investment assets: {profile['investment_assets']} (midpoint: ${profile['investment_midpoint']:,.0f})
    - Debt — Credit card: {profile['debt_credit_card']} (midpoint: ${profile['debt_cc_midpoint']:,.0f})
    - Debt — Personal/student loans: {profile['debt_personal_student']} (midpoint: ${profile['debt_ps_midpoint']:,.0f})
    - Debt — Mortgage: {profile['debt_mortgage']} (midpoint: ${profile['debt_mortgage_midpoint']:,.0f})
    - Total debt: ${profile['total_debt_midpoint']:,.0f}
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
    - Beginner: health_score < {LEVEL_BEGINNER} OR investments = "None" OR experience = "beginner"
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

country_context_market = ""
if country == "US":
    country_context_market = """
    Country: United States
    Domestic market: S&P 500, NASDAQ Composite
    Interest rate: Federal Reserve / Fed Funds rate
    Real estate: Case-Shiller Home Price Index
    Savings benchmark: HYSA rates
    """
elif country == "CA":
    country_context_market = """
    Country: Canada
    Domestic market: TSX Composite
    Interest rate: Bank of Canada / overnight rate
    Real estate: CREA Home Price Index (HPI)
    Savings benchmark: HISA / GIC rates
    """
else:  # India
    country_context_market = """
    Country: India
    Domestic market: Nifty 50 (NSE), Sensex (BSE)
    Interest rate: Reserve Bank of India (RBI) repo rate
    Real estate: NHB RESIDEX (National Housing Bank index)
    Savings benchmark: Savings account rates (4-6%), FD rates (6.5-7.5%), liquid fund returns
    Gold: MCX gold price, Sovereign Gold Bond (SGB) yield
    Currency: INR (Indian Rupee) — note USD/INR exchange rate context
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

# Read Phase 1 results - called AFTER all Task() calls above have completed
def read_agent_output(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

default_surplus = profile.get('monthly_surplus', monthly_income - profile['monthly_expense'])

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
```

---

### Step 4: Phase 2 - Sequential Strategy then Evaluation

wealth-strategist runs first with knowledge context (matched strategies), so strategies are grounded in real methodologies. risk-reward-evaluator then runs with those actual strategies.

```python
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
elif country == "CA":
    country_context_strategist = """
    Country: Canada (CAD)
    Retirement accounts: RRSP ($31,560 limit), TFSA ($7,000 limit), FHSA ($8,000/yr, $40,000 lifetime)
    First home: FHSA, RRSP Home Buyers' Plan ($60,000), First Home Buyer Incentive
    Tax optimization: basic personal amount, 50% capital gains inclusion, dividend tax credit, RRSP/TFSA decision framework
    Side hustle: T2125, CPP self-employed contributions, GST/HST registration at $30K
    Education savings: RESP (20% CESG match up to $500/yr)
    """
else:  # India
    country_context_strategist = """
    Country: India (INR)
    Retirement accounts: EPF (12% + 12% employer, ~8.25% rate), PPF (₹1.5L/yr limit, 7.1% rate, 15yr lock-in), NPS (extra ₹50K deduction under 80CCD(1B))
    Tax-saving investments (Section 80C, ₹1.5L limit): EPF, PPF, ELSS (3yr lock-in), NSC, 5yr FD, life insurance premium, SCSS, Sukanya Samriddhi
    Health insurance deduction (80D): ₹25K self + ₹25-50K parents
    Home loan: Interest deduction ₹2L (Section 24b), principal in 80C
    Capital gains: Equity STCG 20% (<1yr), LTCG 12.5% above ₹1.25L (>1yr). Debt MF taxed at slab rate.
    Gold: Sovereign Gold Bonds (SGB) — best vehicle: 2.5% interest + ZERO LTCG at maturity (8yr)
    First home: Home loan with 80C (principal) + 24b (interest) deductions, stamp duty varies by state
    Tax regime: Old (full deductions) vs New (lower rates, limited deductions) — optimize based on total deductions
    Side hustle: Presumptive taxation 44ADA (50% of receipts if <₹75L digital), GST registration at ₹20L turnover
    Education: Education loan interest fully deductible (Section 80E, no cap, 8 years)
    No universal pension — retirement is entirely self-funded for private sector
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

    Strategy caution rules:
    - Leveraged strategies (Smith Manoeuvre, margin investing, HELOCs for investing) must ALWAYS be flagged as HIGH RISK with clear warnings. These are advanced, controversial tactics — never present as default debt strategies.
    - Debt strategies should prioritize: avalanche/snowball payoff, refinancing, consolidation BEFORE suggesting leverage-based approaches.
    - For real-estate debt (mortgages): focus on renewal optimization, prepayment vs investing tradeoff, rate lock decisions — not leveraged re-borrowing.
    - Never recommend leveraged strategies for users with experience below "advanced" or risk tolerance below "high".

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
         "country_specific": {"accounts": {"US": ["401(k)", "Roth IRA"], "CA": ["RRSP", "TFSA"], "IN": ["PPF", "ELSS", "NPS"]}.get(country, ["401(k)", "Roth IRA"]), "tax_implications": "Tax-deferred or tax-free growth", "regulatory_notes": "Annual contribution limits apply"},
         "learning_prerequisites": ["Understanding compound interest", "Index fund basics"],
         "pros": ["Expert-validated methodology", "Tax advantages", "Fully automatable"], "cons": ["Requires long time horizon"],
         "first_step": "Open a brokerage account and set up automatic contributions", "sources": []}
    ]})

strategies = strategist.get("strategies", [])

# Guard against empty strategies list
if not strategies:
    default_accounts = {"US": ["HYSA", "401(k)"], "CA": ["HISA", "TFSA"], "IN": ["Savings Account", "Liquid Fund"]}.get(country, ["HYSA", "401(k)"])
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
          "verdict": "RECOMMENDED / PROCEED WITH CAUTION / NOT SUITABLE",
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
```

---

### Step 5: Phase 3 - Roadmap Generation (All Strategies)

The action-plan-generator reads the roadmap template AND workflow files, producing a comprehensive 3-section roadmap.

```python
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
net_worth = (phase1['profile'].get('savings_midpoint', 0)
             + phase1['profile'].get('investment_midpoint', 0)
             + phase1['profile'].get('real_estate_equity', 0)
             - phase1['profile'].get('debt_cc_midpoint', 0)
             - phase1['profile'].get('debt_ps_midpoint', 0))

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
elif country == "CA":
    country_resources = """
    Key resources for Canadian users:
    - Financial planner: fpcanada.ca
    - Tax authority: canada.ca/cra
    - Investor education: getsmarteraboutmoney.ca
    - Retirement calculator: canada.ca/cpp-calculator
    - Credit report: equifax.ca / transunion.ca
    """
else:  # India
    country_resources = """
    Key resources for Indian users:
    - SEBI-registered investment advisor: sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13
    - Tax authority: incometax.gov.in
    - Investor education: investor.sebi.gov.in
    - Mutual fund info: amfiindia.com
    - Credit report: cibil.com (free annual report)
    - Financial education: zerodha.com/varsity
    - Retirement/FIRE tools: freefincal.com
    - EPF portal: epfindia.gov.in
    """

Task(
    subagent_type="action-plan-generator",
    model="claude-opus-4-6",
    description="Integrated roadmap generation",
    prompt=f"""
    Generate a comprehensive, CFP-quality wealth roadmap document (4-5 pages of dense, actionable content).
    This is the final deliverable the user receives — it must read like a professional financial plan prepared
    by a certified financial planner: data-dense, table-heavy, specific dollar amounts throughout, multi-scenario
    projections, and a consolidated action plan with priorities and deadlines.

    ## Document Quality Standard

    Reference quality: a professional comprehensive financial plan with sections like Executive Summary with
    snapshot table, Current Financial Position with holdings detail, multi-scenario wealth projections, tax strategy
    with account optimization tables, risk assessment with severity ratings, and a consolidated prioritized action plan.

    Fill ALL {{PLACEHOLDER}} values in the template with real, calculated content. Every section must have
    substantive content — no empty sections, no "TBD", no "N/A" unless genuinely not applicable. Be specific
    with dollar amounts, fund tickers, dates, percentages, and account types throughout.

    ## Section-by-Section Instructions

    **Section 1: Executive Summary**
    - 3-4 sentences: health assessment, key strength, primary strategy + expected impact, timeline to goal
    - Snapshot table: Current vs Projected values for age, net worth, investable portfolio, annual savings, sustainable income (4% SWR)
    - Use the user's age ({profile.get('age', '--')}) and project forward to the target year
    - CRITICAL: Projected net worth MUST be higher than current net worth (wealth grows over time with positive savings and investment returns). Derive projected values from Section 3 projections — do NOT compute them independently. The projected net worth = projected portfolio value + real estate equity (if any) - remaining debt. Double-check that projected > current before writing the table.

    **Section 2: Current Financial Position**
    - 2.1 Net Worth table: category-level breakdown (savings, investments, real estate equity if mortgage exists, each debt type as negative). We do NOT have individual holdings — show only the aggregate categories from the interview
    - 2.2 Cash Flow Summary: monthly and annual for gross income, estimated taxes, living expenses, and available surplus. Surplus = Gross Income - Estimated Taxes - Living Expenses. Use the provided tax estimate; do NOT show surplus as gross minus expenses.
    - 2.3 Health Score with ASCII bar [████████░░] and full metrics table
    - Status indicators: EXCELLENT / GOOD / NEEDS WORK / CRITICAL
    - Debt rows: only show credit card / personal-student / mortgage rows that apply (skip "None" categories)

    **Section 3: Wealth Projection — Three Scenarios**
    - Project portfolio growth year-by-year for at least 5-10 years under 3 return assumptions
    - Conservative (base - 2%), Base Case (realistic for risk tolerance), Optimistic (base + 2%)
    - Include annual contributions from surplus
    - Scenario comparison table: return, portfolio at target, annual 4% income, vs base case delta
    - If user goal is FIRE/retirement, mark the year they hit their FIRE number

    **Section 4: Strategy Blueprint**
    - Numbered priority matrix table with ALL strategies ranked
    - For each strategy, create a detailed subsection with:
      - Specific fund tickers (e.g., XEQT, VTI, AVUV), account types, dollar allocations
      - Monthly commitment from surplus
      - Methodology source and citations
      - Country-specific accounts and tax implications
      - Verdict line from risk evaluator: RECOMMENDED / PROCEED WITH CAUTION / NOT SUITABLE FOR THIS PROFILE

    **Section 5: Debt Strategy (separate per debt type)**
    - ONLY include subsections for debt types the user actually has (skip "None" categories)
    - If no debt at all, replace entire section with: "No outstanding debt. Focus surplus entirely on wealth building."
    - **Credit Card Debt subsection** (if applicable):
      - Monthly interest cost calculation at assumed APR (19-29%)
      - Payoff strategy: avalanche vs snowball with specific timeline and monthly payment from surplus
      - Balance transfer options if balance > $2K
    - **Personal / Student Loan subsection** (if applicable):
      - Estimated rate and monthly payment
      - Refinancing analysis; US: income-driven repayment, PSLF; CA: interest tax credit, repayment assistance; IN: Section 80E interest deduction (education loans), prepayment rules
    - **Mortgage subsection** (if applicable):
      - Rate environment and renewal/refinance timing
      - Prepayment vs investing tradeoff (compare mortgage rate to expected equity return)
      - US: refinance breakeven, PMI removal; CA: renewal shopping (120 days), fixed vs variable; IN: no prepayment penalty on floating (RBI mandate), Section 24(b) + 80C deductions, balance transfer between banks
    - Each subsection: balance estimate, strategy, monthly allocation, payoff timeline

    **Section 6: Tax Strategy**
    - 6.1 Account Optimization: table of specific actions with rationale and priority (HIGH/MEDIUM/LOW)
    - 6.2 Contribution Priority: numbered table — account, annual limit, tax benefit, specific action
    - 6.3 Asset Location Map: which funds in which accounts and why (withholding tax, growth vs income, etc.)
    - Additional notes: tax-loss harvesting schedule, capital gains management, country-specific rules

    **Section 7: Cash Flow & Savings Strategy**
    - ASCII waterfall showing contribution priority order with dollar amounts
    - Year-by-year savings plan table showing what to do each year and target balance accumulation

    **Section 8: Risk Assessment & Stress Testing**
    - Risk table: each risk with description, severity (HIGH/MEDIUM/LOW), and specific mitigation
    - Stress test: 40% market decline + job loss scenario with survivability analysis
    - Sensitivity table: how portfolio and income change under different assumptions

    **Section 9: Consolidated Action Plan (CRITICAL section)**
    - ALL recommended actions from the entire roadmap in ONE numbered table
    - Columns: #, Action, Priority (CRITICAL/HIGH/MEDIUM), Responsible (Self/Advisor/Accountant/Broker), Deadline
    - CRITICAL items = within 90 days; HIGH = within 6 months; MEDIUM = within 1 year
    - This is the single most actionable section — must be comprehensive and specific

    **Section 10: Market Context**
    - Current market summary with specific data points
    - Opportunities and risks relevant to the user's strategy

    **Section 11: Learning Path**
    - 3 phases with specific resources, estimated time, and why each topic matters
    - Recommended reading list

    **Section 12: Key Dates & Deadlines**
    - Tax deadlines, contribution deadlines, mortgage renewal (if applicable), review schedule

    ## Input Data

    ALL strategies from strategist (cover ALL of them in the roadmap — do not focus on just one):
    {json.dumps(strategies, ensure_ascii=False)}

    User age: {profile.get('age', '--')} (exact age)
    User level: {phase1['knowledge'].get('user_level', 'beginner')}
    Country: {country}
    Currency: {currency}

    Learning curriculum:
    {json.dumps(phase1['knowledge'].get('learning_curriculum', []), ensure_ascii=False)}

    Recommended books:
    {json.dumps(phase1['knowledge'].get('recommended_books', []), ensure_ascii=False)}

    Workflow files to read and integrate (use Read tool):
    {json.dumps(workflow_paths, ensure_ascii=False)}

    Financial context:
    - Annual gross income: ${profile['annual_income']:,.0f}
    - Estimated effective tax rate: {profile.get('est_tax_rate', 0.30):.0%}
    - Estimated annual tax: ${profile.get('annual_tax', 0):,.0f}
    - Monthly gross income: ${profile['annual_income']/12:,.0f}
    - Monthly estimated tax: ${profile.get('monthly_tax', 0):,.0f}
    - Monthly net income (after tax): ${profile.get('monthly_net_income', 0):,.0f}
    - Monthly living expenses: ${profile['monthly_expense']:,.0f}
    - Monthly surplus (net income - expenses): ${profile.get('monthly_surplus', 0):,.0f}
    - Annual surplus: ${profile.get('annual_surplus', 0):,.0f}
    - Risk tolerance: {phase1['profile']['risk_tolerance']}
    - Experience: {phase1['profile'].get('experience', 'none')}
    - Goal: {phase1['profile'].get('goal', 'wealth building')}
    - Health score: {phase1['diagnostician'].get('health_score', 50)}
    - Strengths: {json.dumps(phase1['diagnostician'].get('strengths', []), ensure_ascii=False)}
    - Weaknesses: {json.dumps(phase1['diagnostician'].get('weaknesses', []), ensure_ascii=False)}
    - Net worth: ${net_worth:,.0f}
    - Savings: ${profile.get('savings_midpoint', 0):,.0f}
    - Investments: ${profile.get('investment_midpoint', 0):,.0f}
    - Credit card debt: {profile.get('debt_credit_card', 'None')} (midpoint: ${profile.get('debt_cc_midpoint', 0):,.0f})
    - Personal/student loan debt: {profile.get('debt_personal_student', 'None')} (midpoint: ${profile.get('debt_ps_midpoint', 0):,.0f})
    - Mortgage debt: {profile.get('debt_mortgage', 'None')} (midpoint: ${profile.get('debt_mortgage_midpoint', 0):,.0f})
    - Total debt: ${profile.get('total_debt_midpoint', 0):,.0f}
    - Home value: {profile.get('home_value', 'None')} (midpoint: ${profile.get('home_value_midpoint', 0):,.0f})
    - Real estate equity: ${profile.get('real_estate_equity', 0):,.0f}

    Market conditions: {phase1['market'].get('market_summary', '')}

    Risk evaluation: {phase2['evaluator'].get('overall_recommendation', '')}
    Risk evaluations per strategy: {json.dumps(phase2['evaluator'].get('evaluations', []), ensure_ascii=False)}

    Curated sources:
    {json.dumps(phase1['knowledge'].get('curated_info', [])[:3], ensure_ascii=False)}

    {country_resources}

    Roadmap template (fill all {{PLACEHOLDER}} values with actual content):
    {template_content}

    ## Output Instructions
    - Read workflow files with the Read tool and integrate into the workflow section
    - Use the Write tool to save the completed markdown roadmap
    - Save to exactly this path: {roadmap_path}
    - Every placeholder must be replaced with real, specific content
    - Use tables, ASCII charts, and checkboxes for visual structure
    - Dollar amounts should always include the currency context ({currency})
    """
)

print(f"Phase 3 complete")
```

---

### Step 6: Display Final Report, Record Session & Cleanup

```python
print("\n" + "="*60)
print("Wealth Roadmap Complete!")
print("="*60)

disclaimer_urls = {"US": "https://www.letsmakeaplan.org/", "CA": "https://fpcanada.ca/", "IN": "https://www.sebi.gov.in/"}
disclaimer_url = disclaimer_urls.get(country, "https://www.letsmakeaplan.org/")
print(f"""
DISCLAIMER
This analysis is AI-generated reference information.
Investment decisions should be made based on your own judgment
and responsibility. Consult a qualified financial advisor before
making significant financial decisions.
Find a CFP: {disclaimer_url}
""")

user_level = phase1['knowledge'].get('user_level', 'N/A')
currency = currency_map.get(country, "USD")
country_names = {"US": "United States", "CA": "Canada", "IN": "India"}
print(f"Country: {country_names.get(country, country)}")
print(f"User level: {user_level}")
print(f"Financial health score: {phase1['diagnostician'].get('health_score', 'N/A')}")
monthly_surplus = phase1['diagnostician'].get('monthly_surplus', 'N/A')
if isinstance(monthly_surplus, (int, float)):
    print(f"Monthly surplus: approx. ${monthly_surplus:,.0f} {currency}")
else:
    print(f"Monthly surplus: {monthly_surplus}")
print()
print(f"Strategies generated: {len(strategies)}")
for s in strategies:
    print(f"  - {s.get('id')}: {s.get('title')} ({s.get('risk_level')} risk, {s.get('time_horizon')})")
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
elif country == "CA":
    print("3. Find a CFP: https://fpcanada.ca/")
else:
    print("3. Find a SEBI-registered advisor: https://www.sebi.gov.in/")

# Record session history to DB (use temp file to avoid SQL injection from single quotes in strategy titles)
try:
    session_data = {
        "user_level": phase1["knowledge"].get("user_level", "beginner"),
        "selected_strategy": ", ".join(s.get("title", "") for s in strategies[:3]),
        "matched_strategies": json.dumps(phase1["knowledge"].get("matched_strategies", []), ensure_ascii=False),
        "selected_workflows": json.dumps(phase1["knowledge"].get("selected_workflows", []), ensure_ascii=False),
        "roadmap_path": roadmap_path
    }
    import tempfile
    session_tmp = tempfile.mktemp(suffix=".json")
    with open(session_tmp, "w") as f:
        json.dump(session_data, f, ensure_ascii=False)

    subprocess.run(["python3", "-c", f"""
import sqlite3, json, os
with open('{session_tmp}') as f:
    d = json.load(f)
conn = sqlite3.connect('{DB_PATH}')
row = conn.execute("SELECT id FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
pid = row[0] if row else None
if pid:
    conn.execute('''INSERT INTO session_history
        (profile_id, user_level, selected_strategy, matched_strategies, selected_workflows, roadmap_path)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (pid, d['user_level'], d['selected_strategy'],
         d['matched_strategies'], d['selected_workflows'], d['roadmap_path']))
    conn.commit()
conn.close()
os.remove('{session_tmp}')
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
```

---

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
