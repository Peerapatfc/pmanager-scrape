# Planetarium Manager Scraper

A web scraper for finding high-value players on the Planetarium Manager transfer list.

## Features
- **Automated Authentication**: Logs into the game securely.
- **Advanced Filtering**: Finds players with strict criteria (e.g., Age < 31, Quality > Very Good, Asking Price < 1M).
    - *Note: Uses a verified direct URL to bypass some website filter issues.*
- **Deep Extraction**: Visits individual negotiation pages to extract:
    - Estimated Transfer Value
    - Asking Price (Strictly verified < 1M)
    - Transfer Deadline
    - Bids Count & Average Bid (Scout)
- **Auto-Pagination**: Scrapes all available result pages.
- **Smart Output**: Generates a sorted CSV of the best targets.

## Setup

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

## Usage
There are two scraping strategies available:

### 1. Low Price Scraper (Original)
*Target: Age < 31, Price <= 20,000*
```bash
./venv/Scripts/python main_low_price.py
```
Results saved to: `transfer_targets.csv`

### 2. High Quality Scraper
*Target: Age < 31, Quality > Very Good (7)*
```bash
./venv/Scripts/python main_high_quality.py
```
Results saved to: `transfer_targets_high_quality.csv`

## Output Format
The CSV contains:
- Player ID
- Estimated Value
- Asking Price
- Deadline
- Bids Count
- Average Bid
