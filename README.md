# Planetarium Manager Scraper

A web scraper for finding high-value players on the Planetarium Manager transfer list with automated Google Sheets integration.

## Features

- **Automated Authentication**: Logs into the game securely.
- **Advanced Filtering**: Finds players with strict criteria (e.g., Age < 31, Quality > Very Good, Asking Price < 1M).
    - *Note: Uses a verified direct URL to bypass some website filter issues.*
- **Deep Extraction**: Visits individual negotiation pages to extract:
    - Estimated Transfer Value
    - Asking Price (Strictly verified < 1M)
    - Transfer Deadline
    - Bids Count & Average Bid (Scout)
- **ROI Calculation**: Automatically calculates Return on Investment for each player.
- **Auto-Pagination**: Scrapes all available result pages.
- **Google Sheets Integration**: Uploads results directly to Google Sheets.
- **GitHub Actions**: Automated daily scraping at 7:30 AM Thailand time.

## Setup

### Local Development

1. **Install Python 3.x**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. **Configure Credentials**:
   - Rename `.env.example` to `.env`
   - Add your login details:
     ```
     PM_USERNAME=your_email
     PM_PASSWORD=your_password
     ```
4. **Google Sheets Setup** (Optional):
   - Create a Google Cloud project and enable Sheets API
   - Create a service account and download `credentials.json`
   - Share your spreadsheet with the service account email

### GitHub Actions (Automated)

The scraper can run automatically via GitHub Actions:

1. **Add Repository Secrets** (Settings → Secrets → Actions):
   | Secret Name | Value |
   |-------------|-------|
   | `PM_USERNAME` | Your pmanager.org username |
   | `PM_PASSWORD` | Your pmanager.org password |
   | `GOOGLE_CREDENTIALS_JSON` | Full contents of `credentials.json` |

2. **Schedule**: Runs daily at 7:30 AM Thailand time (0:30 UTC)

3. **Manual Trigger**: Go to Actions → Run PManager Scraper → Run workflow

## Usage

There are two scraping strategies available:

### 1. Low Price Scraper
*Target: Age < 31, Price <= 20,000*
```bash
python main_low_price.py
```
Results saved to: `transfer_targets.csv`

### 2. High Quality Scraper
*Target: Age < 31, Quality > Very Good (7)*
```bash
python main_high_quality.py
```
Results saved to: `transfer_targets_high_quality.csv`

## Output Format

The CSV contains:
- Player ID
- Estimated Value
- Asking Price
- Buy Price (max of Asking Price and Bids Average)
- Value Difference
- ROI (Return on Investment %)
- Deadline
- Bids Count
- Average Bid

## Google Sheets

Results are automatically uploaded to:
- **High Quality**: "High Quality" sheet tab
- **Low Price**: "Low Price" sheet tab

## License

Private use only.
