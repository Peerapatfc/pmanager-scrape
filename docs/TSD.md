# Technical Specification Document (TSD)
**Project Name:** PManager Open Market Scraper & Analyzer
**Version:** 1.0

## 1. Technology Stack
*   **Language**: Python 3.11+
*   **Browser Automation**: Playwright (Chromium)
*   **HTML Parsing**: BeautifulSoup4
*   **Data Handling**: Pandas
*   **API Integration**:
    *   `gspread` (Google Sheets V4 API)
    *   `requests` (Telegram Bot API)
*   **CI/CD**: GitHub Actions

## 2. Dependencies
```text
playwright
beautifulsoup4
pandas
requests
gspread
google-auth
python-dotenv
```

## 3. Data Schema (Google Sheets)

### 3.1 Sheet: "All Players"
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique Player ID |
| `name` | String | Player Name |
| `estimated_value` | Integer | Scout's valuation |
| `bids_avg` | Integer | Average scout bid |
| `last_transfer_price` | Integer | **New**: Actual sold price |
| `sale_to_bid_ratio` | Float | **New**: `last_transfer_price / bids_avg` |
| `deadline` | DateTime | Auction end time (UTC+7) |
| ... | ... | (Attributes like Speed, Strength, etc.) |

## 4. Key Algorithms

### 4.1 Deadline Parsing
*   **Input**: "Today at 10:00", "Tomorrow at 14:00"
*   **Logic**:
    1.  Parse HH:MM using Regex.
    2.  Get Current UTC date.
    3.  If "Tomorrow", add 1 day.
    4.  Convert to UTC+7 (Thailand Time).
*   **Output**: Datetime Object.

### 4.2 Ratio Calculation
*   **Context**: Executed in `update_final_prices.py`.
*   **Formula**:
    ```python
    if bids_avg > 0:
        ratio = last_transfer_price / bids_avg
    else:
        ratio = 0
    ```

## 5. Security & Configuration
*   **Credentials**:
    *   `credentials.json`: Google Service Account Key (JSON).
    *   `.env`: Stores sensitive passwords (`PM_PASSWORD`) and Tokens.
*   **Secrets**: GitHub Secrets used for CI/CD injection of environment variables.
