import os, sys, re, json, requests, matplotlib
import pandas as pd
from datetime import datetime

#Matplotlib imports
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GMAIL_CREDENTIALS_PATH, SHEETS_TOKEN_PATH, EXPENSE_SHEET_ID, FAIRY_GROQ_API_KEY, GROQ_MODEL, OLLAMA_URL, MODEL_NAME, BASE_DIR

# ── Google Auth ──
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread

#Importing speaker function
from voice.speaker import speak
from brain.responses import get_confirmation_ack
 
# ── Groq (brain: persona, interpretation, spoken recommendations) ──
from groq import Groq
groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)
 
# ── OAuth scope — read-only is all we need for Sheets ──
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# ── Where generated plot PNGs get saved ──
PLOTS_DIR = os.path.join(BASE_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)
 
# ── Calendar month names — used to tell monthly tabs from trip tabs ──
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# === Header detection ===# 
def find_header_row(all_values: list[list[str]]) -> int:
    for i, row in enumerate(all_values[:15]):
        normalized = [str(cell).strip().upper() for cell in row]
        if "DATE" in normalized and "AMOUNT" in normalized:
            return i
    return -1

def _trim_trailing_blanks(row: list[str]) -> int:
    normalized = [str(cell).strip().upper() for cell in row]
    if "AMOUNT" in normalized:
        return normalized.index("AMOUNT")
    last_index = -1
    for i, cell in enumerate(row):
        if str(cell).strip() != "":
            last_index = i
    return last_index

# === Peso to Yen Conversion heper functions for Japan Trip Tabs ===#
def detect_exchange_rate(all_values: list[list[str]]) -> float | None:
    peso_value = None
    foreign_value = None

    for i, row in enumerate(all_values[:15]):
        for j, cell in enumerate(row):
            label = str(cell).strip().upper()
 
            if "PESO" in label and "BUDGET" in label:
                # The actual number usually sits one row below the label
                if i + 1 < len(all_values) and j < len(all_values[i + 1]):
                    raw = all_values[i + 1][j]
                    peso_value = parse_currency_number(raw)
 
            elif "BUDGET" in label and "PESO" not in label and "CASH" not in label:
                # Catches "YEN-CONVERTED BUDGET" or similar future labels
                if i + 1 < len(all_values) and j < len(all_values[i + 1]):
                    raw = all_values[i + 1][j]
                    foreign_value = parse_currency_number(raw)
 
    if peso_value and foreign_value and foreign_value != 0:
        return peso_value / foreign_value
 
    return None

def parse_currency_number(raw: str) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None
 
# ====== Authentication ======= #
def get_sheets_client() -> gspread.Client:
    creds = None #Set the credenmtials to an empty value
 
    if os.path.exists(SHEETS_TOKEN_PATH): #Check if the path to the sheets exists
        creds = Credentials.from_authorized_user_file(SHEETS_TOKEN_PATH, SHEETS_SCOPES) #Acquire the sheets from the user with credentials
 
    if not creds or not creds.valid: #Check for credential validity
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"credentials.json not found at '{GMAIL_CREDENTIALS_PATH}'. "
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, SHEETS_SCOPES
            )
            creds = flow.run_local_server(port=8080) # Port 8080 (Dedicated port for the Finance)
 
        with open(SHEETS_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
 
    return gspread.authorize(creds)

def load_all_sheets() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]: #returns as a tuple
    client = get_sheets_client()
    spreadsheet = client.open_by_key(EXPENSE_SHEET_ID)
 
    monthly_tabs: dict[str, pd.DataFrame] = {}
    trip_tabs: dict[str, pd.DataFrame] = {}
 
    for worksheet in spreadsheet.worksheets():
        tab_name = worksheet.title.strip()
        print(f"[Finance]: Reading tab '{tab_name}'...")
 
        try:
            all_values = worksheet.get_all_values()
 
            if not all_values:
                print(f"[Finance]: Tab '{tab_name}' is empty — skipping.")
                continue
 
            header_row_index = find_header_row(all_values)
            if header_row_index == -1:
                print(f"[Finance]: Tab '{tab_name}' has no recognizable header row — skipping.")
                continue
            raw_header_row = all_values[header_row_index]
            last_col = _trim_trailing_blanks(raw_header_row)
            expected_headers = [str(c).strip() for c in raw_header_row[:last_col + 1]]

            records = worksheet.get_all_records(
                head=header_row_index + 1,
                expected_headers=expected_headers,
            )
 
            if not records:
                print(f"[Finance]: Tab '{tab_name}' has headers but no data rows — skipping.")
                continue
 
            df = pd.DataFrame(records)
            df.columns = [c.strip().upper() for c in df.columns]
 
            # Minimum viable columns check
            if "DATE" not in df.columns or "AMOUNT" not in df.columns:
                print(f"[Finance]: Tab '{tab_name}' missing required columns — skipping.")
                continue
 
            # ── Clean AMOUNT ──
            df["AMOUNT"] = (
                df["AMOUNT"]
                .astype(str)
                .str.replace(r"[^\d.]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )

            #Currency conversion for the Japan trip code only
            is_monthly = tab_name in MONTH_NAMES
            if not is_monthly:
                rate = detect_exchange_rate(all_values)
                if rate:
                    print(f"[Finance]: Tab '{tab_name}' — converting at rate {rate:.4f} PHP per unit.")
                    df["AMOUNT"] = df["AMOUNT"] * rate
 
            # Drop template rows (rows where Amount is 0 or blank)
            df = df[df["AMOUNT"] > 0].copy()
            if df.empty:
                continue
 
            # ── Parse DATE ──
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
            df = df.dropna(subset=["DATE"])
 
            # Classify tab
            if is_monthly:
                monthly_tabs[tab_name] = df
            else:
                trip_tabs[tab_name] = df
 
        except Exception as e:
            print(f"[Finance Error]: Could not read tab '{tab_name}': {e}")
            continue
 
    return monthly_tabs, trip_tabs

def _get_current_month_df(
    monthly_tabs: dict[str, pd.DataFrame]
) -> tuple[str, pd.DataFrame | None]:
    """Returns the DataFrame for the current calendar month, or the most recent one."""
    current_month = datetime.now().strftime("%B")   # e.g. "June"
    if current_month in monthly_tabs:
        return current_month, monthly_tabs[current_month]
    if monthly_tabs:
        last = list(monthly_tabs.keys())[-1]
        return last, monthly_tabs[last]
    return "", None
 

# ===== SUB INTENT CLASSIFICATION ====== #

def classify_finance_sub_intent(voice_query: str) -> dict:
    prompt = (
        "You are an intent parser for a voice assistant's finance module. "
        "Given the user's voice query below, return ONLY a valid JSON object "
        "(no markdown, no backticks, no explanation) with these keys:\n"
        "  sub_intent: one of [monthly_summary, all_time_summary, category_summary, "
        "recommendations, plot_monthly, plot_category, plot_timeline, trip_summary, heavy_analysis]\n"
        "  month: the month name mentioned (or null)\n"
        "  category: the spending category mentioned (or null)\n"
        "  trip: the trip name mentioned (or null)\n\n"
        "Use heavy_analysis when the user asks for trends, projections, anomalies, "
        "statistical comparisons, or anything requiring deep mathematical reasoning.\n\n"
        "If the user asks to 'plot', 'chart', 'graph', 'show a pie chart', or 'visualize' "
        "category data, use plot_category — NOT category_summary. Only use category_summary "
        "when they want the answer spoken/read aloud, not a visual chart.\n\n"
        f"User query: \"{voice_query}\""
    )
 
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.1,    # Low temperature = deterministic JSON output
        )
        raw = completion.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Finance Sub-Intent Error]: {e}")
        # Fallback to a safe default
        return {"sub_intent": "monthly_summary", "month": None, "category": None, "trip": None}
    
def groq_recommendations (monthly_tabs: dict[str, pd.DataFrame]) -> str:
    if not monthly_tabs:
        return "No data to work with, Master. Load your expense sheet first."
 
    month_totals = {
        name: round(df["AMOUNT"].sum(), 2)
        for name, df in monthly_tabs.items()
    }
    avg = round(sum(month_totals.values()) / len(month_totals), 2)
 
    all_df = pd.concat(monthly_tabs.values(), ignore_index=True)
    cat_totals = {}
    if "CATEGORY" in all_df.columns:
        cat_totals = all_df.groupby("CATEGORY")["AMOUNT"].sum().round(2).to_dict()
 
    data_block = (
        f"Monthly totals (PHP): {month_totals}\n"
        f"Average monthly spend: {avg} PHP\n"
        f"All-time category totals: {cat_totals}"
    )
 
    prompt = (
        "You are FAIRY — a sharp, sarcastic, witty AI assistant. "
        "Give 2-3 short spoken sentences of financial advice based on the data below. "
        "Be direct, use dry humor, address the user as Master. "
        "Under 70 words — this is spoken aloud.\n\n"
        f"Data:\n{data_block}"
    )
 
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=130,
            temperature=0.75,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Finance Groq Error]: {e}")
        return "I couldn't generate recommendations right now, Master."
    
# ===== LMF2.5 DIRTY MATHEMATICAL WORK ======== #
 
def lfm25_heavy_analysis(monthly_tabs: dict[str, pd.DataFrame], voice_query: str) -> str:
    if not monthly_tabs:
        return "No data available for analysis, Master."
 
    # Build a full numeric data dump for lfm2.5 to reason over
    month_totals = {
        name: round(df["AMOUNT"].sum(), 2)
        for name, df in monthly_tabs.items()
    }
    all_df = pd.concat(monthly_tabs.values(), ignore_index=True)
 
    cat_totals = {}
    if "CATEGORY" in all_df.columns:
        cat_totals = all_df.groupby("CATEGORY")["AMOUNT"].sum().round(2).to_dict()
 
    necessity_totals = {}
    if "NECESSITY" in all_df.columns:
        necessity_totals = all_df.groupby("NECESSITY")["AMOUNT"].sum().round(2).to_dict()
 
    data_block = (
        f"Monthly spending totals (PHP): {month_totals}\n"
        f"Category totals across all months (PHP): {cat_totals}\n"
        f"Essential vs Non-Essential totals (PHP): {necessity_totals}\n"
    )
 
    prompt = (
        "You are a financial analysis engine embedded in a personal AI assistant. "
        "Analyze the expense data below and answer the user's question directly. "
        "Be concise — your response will be spoken aloud. Under 80 words. "
        "Use numbers. Be specific. No markdown.\n\n"
        f"User's question: {voice_query}\n\n"
        f"Expense data:\n{data_block}"
    )
 
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout=60,     # lfm2.5 runs locally — give it time to think
        )
        response.raise_for_status()
        result = response.json()
        return result["message"]["content"].strip()
 
    except requests.exceptions.Timeout:
        print("[Finance lfm2.5]: Timed out.")
        return "My local model took too long to respond, Master. Try again."
    except Exception as e:
        print(f"[Finance lfm2.5 Error]: {e}")
        return "Something went wrong with the local analysis engine, Master."
    
# ====== PANDAS ANALYSIS FUCNTIONS ====== #
 
def summarize_month(tab_name: str, df: pd.DataFrame) -> str:
    """Voice-friendly summary of a single month's spending."""
    total = df["AMOUNT"].sum()
    essential = df[df["NECESSITY"].str.lower() == "essential"]["AMOUNT"].sum() \
        if "NECESSITY" in df.columns else 0
    non_essential = total - essential
 
    cat_part = ""
    if "CATEGORY" in df.columns:
        cat_totals = df.groupby("CATEGORY")["AMOUNT"].sum()
        top_cat = cat_totals.idxmax()
        top_amt = cat_totals.max()
        cat_part = f"Biggest category: {top_cat} at {top_amt:.0f} pesos."
 
    return (
        f"For {tab_name}, total spending was {total:.0f} pesos. "
        f"{essential:.0f} essential, {non_essential:.0f} non-essential. "
        f"{cat_part}"
    )
 
 
def all_time_summary(monthly_tabs: dict[str, pd.DataFrame]) -> str:
    """Aggregated statistics across all monthly tabs."""
    if not monthly_tabs:
        return "No monthly data available, Master."
 
    month_totals = {name: df["AMOUNT"].sum() for name, df in monthly_tabs.items()}
    overall = sum(month_totals.values())
    avg = overall / len(month_totals)
    highest = max(month_totals, key=month_totals.get)
    lowest = min(month_totals, key=month_totals.get)
 
    return (
        f"Across {len(month_totals)} months, total spending is {overall:.0f} pesos. "
        f"Monthly average: {avg:.0f} pesos. "
        f"Highest month: {highest} at {month_totals[highest]:.0f} pesos. "
        f"Lowest: {lowest} at {month_totals[lowest]:.0f} pesos."
    )
 
 
def category_summary(
    monthly_tabs: dict[str, pd.DataFrame], specific_month: str = None
) -> str:
    """Breakdown by category, either for a specific month or all time."""
    if specific_month and specific_month in monthly_tabs:
        df = monthly_tabs[specific_month]
        label = specific_month
    else:
        df = pd.concat(monthly_tabs.values(), ignore_index=True)
        label = "all time"
 
    if "CATEGORY" not in df.columns:
        return "No category data available, Master."
 
    cat_totals = df.groupby("CATEGORY")["AMOUNT"].sum().sort_values(ascending=False)
    top3 = cat_totals.head(3)
    parts = [f"{cat} at {amt:.0f} pesos" for cat, amt in top3.items()]
    return f"For {label}, top categories: " + ", then ".join(parts) + "."
 
 
def trip_summary(trip_tabs: dict[str, pd.DataFrame], query: str) -> str:
    """Summarizes a specific trip tab's spending."""
    if not trip_tabs:
        return "No trip data on record, Master."
 
    # Match the trip name from the query
    matched = None
    for tab_name in trip_tabs:
        if any(word in query.lower() for word in tab_name.lower().split("_")):
            matched = tab_name
            break
    if not matched:
        matched = list(trip_tabs.keys())[0]
 
    df = trip_tabs[matched]
    total = df["AMOUNT"].sum()
    days = df["DATE"].nunique()
    cat_part = ""
    if "CATEGORY" in df.columns:
        top_cat = df.groupby("CATEGORY")["AMOUNT"].sum().idxmax()
        top_amt = df.groupby("CATEGORY")["AMOUNT"].sum().max()
        cat_part = f"Most spent on {top_cat} at {top_amt:.0f} pesos."
 
    display_name = matched.replace("_", " ")
    return (
        f"Your {display_name} trip totalled {total:.0f} pesos over {days} days. "
        f"{cat_part}"
    )
 
def save_and_show_plot(fig, filename: str):
    """
    Saves the figure as a PNG to PLOTS_DIR AND displays it in a native
    matplotlib popup window (via plt.show()).
 
    ORDER MATTERS HERE:
    1. Save to disk FIRST — savefig() doesn't require the window to be open.
    2. Show the window with plt.show() — this BLOCKS execution until the
       person closes the window. That's expected/standard matplotlib
       behavior; FAIRY's voice loop resumes once you close the chart.
    3. Close the figure afterward to free memory — closing before showing
       would destroy the figure before it ever renders.
    """
    path = os.path.join(PLOTS_DIR, filename)
    fig.savefig(path, dpi=150)
    print(f"[Finance]: Plot saved to {path}")
 
    try:
        plt.show()   # Opens the native interactive window; blocks until closed
    except Exception as e:
        print(f"[Finance]: Could not open native plot window: {e}")
        # Fallback: at least open the saved PNG with the OS default viewer
        try:
            os.startfile(path)
        except Exception as e2:
            print(f"[Finance]: Could not auto-open saved plot either: {e2}")
    finally:
        plt.close(fig)
 
    return path
 
def plot_monthly_totals(monthly_tabs: dict[str, pd.DataFrame]) -> str:
    if not monthly_tabs:
        return "No monthly data to plot, Master."
 
    sorted_tabs = sorted(
        monthly_tabs.items(),
        key=lambda x: MONTH_NAMES.index(x[0].lower()) if x[0].lower() in MONTH_NAMES else 99
    )
    labels = [name for name, _ in sorted_tabs]
    totals = [df["AMOUNT"].sum() for _, df in sorted_tabs]
    avg = sum(totals) / len(totals)
 
    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(labels, totals, color="#4C9BE8", edgecolor="white", linewidth=0.8)
 
    # Average line for reference
    ax.axhline(avg, color="#E84C4C", linestyle="--", linewidth=1.2, label=f"Avg ₱{avg:,.0f}")
    ax.legend(fontsize=9)
 
    ax.set_title("Monthly Spending Totals", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Amount (₱)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₱{x:,.0f}"))
 
    for bar, total in zip(bars, totals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(totals) * 0.01,
            f"₱{total:,.0f}",
            ha="center", va="bottom", fontsize=9
        )
 
    ax.set_facecolor("#f5f5f5")
    fig.tight_layout()
 
    save_and_show_plot(fig, "monthly_totals.png")
    return "Monthly totals bar chart is up, Master."
 
 
def plot_category_breakdown(monthly_tabs: dict[str, pd.DataFrame], specific_month: str = None) -> str:
    if specific_month and specific_month in monthly_tabs:
        df = monthly_tabs[specific_month]
        title = f"Category Breakdown — {specific_month}"
    else:
        df = pd.concat(monthly_tabs.values(), ignore_index=True)
        title = "Category Breakdown — All Time"
 
    if "CATEGORY" not in df.columns:
        return "No category data to plot, Master."
 
    cat_totals = df.groupby("CATEGORY")["AMOUNT"].sum().sort_values(ascending=False)
 
    # Merge small slices into "Other" for cleaner visuals
    threshold = cat_totals.sum() * 0.02
    large = cat_totals[cat_totals >= threshold]
    small = cat_totals[cat_totals < threshold]
    if not small.empty:
        large["Other"] = small.sum()
    cat_totals = large
 
    colors = list(plt.cm.Set3.colors[:len(cat_totals)])
    fig, ax = plt.subplots(figsize=(8, 7))
    wedges, texts, autotexts = ax.pie(
        cat_totals,
        labels=cat_totals.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.82,
    )
    for t in autotexts:
        t.set_fontsize(9)
 
    ax.set_title(title, fontsize=13, fontweight="bold", pad=20)
    fig.tight_layout()
 
    save_and_show_plot(fig, "category_breakdown.png")
    return "Category breakdown chart is up, Master."
 
def plot_spending_timeline(monthly_tabs: dict[str, pd.DataFrame]) -> str:
    if not monthly_tabs:
        return "No data for a timeline, Master."
 
    all_df = pd.concat(monthly_tabs.values(), ignore_index=True).sort_values("DATE")
    daily = all_df.groupby("DATE")["AMOUNT"].sum().reset_index()
    daily["CUMULATIVE"] = daily["AMOUNT"].cumsum()
 
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
 
    # ── Top: daily bars ──
    ax1.bar(daily["DATE"], daily["AMOUNT"], color="#4C9BE8", alpha=0.75, width=0.8)
    ax1.set_ylabel("Daily Spend (₱)", fontsize=10)
    ax1.set_title("All-Time Spending Timeline", fontsize=13, fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₱{x:,.0f}"))
    ax1.set_facecolor("#f5f5f5")
 
    # ── Bottom: cumulative line ──
    ax2.plot(daily["DATE"], daily["CUMULATIVE"], color="#E84C4C", linewidth=2)
    ax2.fill_between(daily["DATE"], daily["CUMULATIVE"], alpha=0.12, color="#E84C4C")
    ax2.set_ylabel("Cumulative (₱)", fontsize=10)
    ax2.set_xlabel("Date", fontsize=10)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"₱{x:,.0f}"))
    ax2.set_facecolor("#f5f5f5")
 
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
 
    save_and_show_plot(fig, "spending_timeline.png")
    return "All-time spending timeline is up, Master."
 
def handle_finance(voice_query: str) -> str:
    try:
        print("[Finance]: Connecting to Google Sheets...")
        monthly_tabs, trip_tabs = load_all_sheets()
 
        if not monthly_tabs and not trip_tabs:
            return (
                "I couldn't find any expense data in your spreadsheet, Master. "
                "Check that the tab names match month names or trip names."
            )
 
        # ── Step 2: Groq parses the natural language query ──
        parsed = classify_finance_sub_intent(voice_query)
        sub_intent = parsed.get("sub_intent", "monthly_summary")
        mentioned_month = parsed.get("month")       # e.g. "April" or None
        mentioned_trip = parsed.get("trip")         # e.g. "japan" or None
 
        print(f"[Finance Sub-Intent]: {sub_intent} | Month: {mentioned_month} | Trip: {mentioned_trip}")
 
        # ── Step 3: Route ──
 
        if sub_intent == "monthly_summary":
            if mentioned_month and mentioned_month.capitalize() in monthly_tabs:
                name = mentioned_month.capitalize()
                return summarize_month(name, monthly_tabs[name])
            tab_name, df = _get_current_month_df(monthly_tabs)
            if df is None:
                return "No month data available, Master."
            return summarize_month(tab_name, df)
 
        elif sub_intent == "all_time_summary":
            return all_time_summary(monthly_tabs)
 
        elif sub_intent == "category_summary":
            month = mentioned_month.capitalize() if mentioned_month else None
            return category_summary(monthly_tabs, month)
 
        elif sub_intent == "recommendations":
            # GROQ handles this — it's language + persona work
            return groq_recommendations(monthly_tabs)
 
        elif sub_intent == "heavy_analysis":
            # LFM2.5 handles this — it's math + statistical reasoning
            return lfm25_heavy_analysis(monthly_tabs, voice_query)
 
        elif sub_intent == "plot_monthly":
            return plot_monthly_totals(monthly_tabs)
 
        elif sub_intent == "plot_category":
            month = mentioned_month.capitalize() if mentioned_month else None
            return plot_category_breakdown(monthly_tabs, month)
 
        elif sub_intent == "plot_timeline":
            return plot_spending_timeline(monthly_tabs)
 
        elif sub_intent == "trip_summary":
            return trip_summary(trip_tabs, voice_query)
 
        else:
            # Default fallback: summarize current month
            tab_name, df = _get_current_month_df(monthly_tabs)
            if df is not None:
                return summarize_month(tab_name, df)
            return (
                "I've got your expense data loaded, Master. "
                "Ask for a summary, category breakdown, chart, or recommendations."
            )
 
    except FileNotFoundError as e:
        return f"Credentials issue, Master. {e}"
 
    except Exception as e:
        print(f"[Finance Error]: {e}")
        return "Something went wrong while accessing your expense data, Master."