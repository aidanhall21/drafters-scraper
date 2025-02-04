# Sports Prop Line Scraper and Auto-Poster

This script automatically scrapes prop betting lines from leading sportsbooks, compares them to Drafters Pick'em lines, identifies value opportunities, and automatically posts pick slips.

## Prerequisites

1. An account at [odds-api.com](https://odds-api.com)
2. A [Drafters.com](https://drafters.com) account

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Configure your `.env` file with:
   - Your Odds API key (`ODDS_API_KEY`)
   - Your Drafters auth token
   - Your Drafters display name
   - Location information

### Finding Your Drafters Auth Token

1. Open your browser's Developer Tools (F12)
2. Navigate to the Network tab
3. Visit the Drafters Pick'em page
4. Look for Authorization: Bearer token in the request headers

## Customization

The script is configurable in several ways:

- **Sports**: Add or remove sports in the `SPORT_CONFIGS` dictionary at the top of `sports_main.py`
- **Player Names**: Add name mappings between odds API and Drafters in the `name_replacements` dictionary within the `process_all_sports` function

## Features

- Automated prop line scraping from multiple sportsbooks
- Comparison with Drafters Pick'em lines
- Value identification
- Automatic pick slip posting
- Support for multiple sports (NBA, NFL, NHL, etc.)
- Configurable name mappings for player consistency
