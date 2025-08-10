# ALFRED - Analytical League Fantasy Resource for Elite Drafting

A comprehensive fantasy football draft assistant that provides real-time recommendations, player rankings aggregation, and draft strategy optimization.

## Features

- **Multi-Source Rankings Aggregation**: Combines rankings from ESPN, FantasyPros, Yahoo, CBS, and more
- **Real-Time Draft Assistant**: Live recommendations during your draft
- **Platform Integration**: Works with Sleeper, ESPN, and Yahoo leagues
- **Advanced Analytics**: VORP calculations, position scarcity analysis, roster construction optimization
- **Mock Draft Simulator**: Practice your draft strategy
- **React Dashboard**: Modern web UI for draft visualization

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (for React frontend)

### Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd ff_draft_vibe
   ```

2. **Set up PostgreSQL database**
   ```bash
   # Create database (adjust username as needed)
   createdb fantasy_draft_db
   
   # Run database setup
   python database_setup.py
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd ff-dashboard
   npm install
   ```

### Running the Application

#### Option 1: Desktop App (Recommended for drafts)
```bash
python draft_assistant_app.py
```

#### Option 2: Web Interface
```bash
# Terminal 1: Start backend server
python simple_draft_server.py

# Terminal 2: Start React frontend
cd ff-dashboard
npm run dev
```

#### Option 3: Sleeper Integration
```bash
python sleeper_draft_assistant.py --draft-id YOUR_DRAFT_ID
```

## Project Structure

```
ff_draft_vibe/
├── src/
│   ├── scrapers/      # Data collection from various sources
│   ├── engines/       # Core draft logic and algorithms
│   ├── api/           # API servers and integrations
│   ├── db/            # Database utilities
│   └── utils/         # Helper functions
├── ff-dashboard/      # React frontend
├── data/              # Rankings and export files
├── templates/         # HTML templates
└── scripts/           # Utility scripts
```

## Usage Guide

### 1. Update Rankings Data
```bash
# Scrape latest rankings
python fantasy_rankings_aggregator.py

# Or update specific source
python espn_rankings_scraper.py
```

### 2. Configure Your League
- Edit league settings in the app
- Set scoring system (PPR, half-PPR, standard)
- Configure roster positions

### 3. During Your Draft
- Launch the assistant before your draft starts
- Enter picks as they happen
- Follow the recommendations for optimal team building

## Key Components

- **Draft Engines**: Core algorithms for pick recommendations
- **Data Scrapers**: Automated collection of player rankings
- **Database**: PostgreSQL schema for players, rankings, and drafts
- **React Dashboard**: Visual draft board and analytics

## Development

### Adding New Data Sources
1. Create scraper in `src/scrapers/`
2. Add source to `ranking_sources` table
3. Update aggregation logic

### Running Tests
```bash
pytest tests/
```

## Troubleshooting

- **Database Connection Issues**: Check PostgreSQL is running and credentials in `database_setup.py`
- **Scraping Errors**: Some sites may require updated selectors
- **Sleeper Integration**: See `SLEEPER_DRAFT_DEBUG_SUMMARY.md` for common issues

## AI Development Notes

This project is designed for collaborative AI development. See `CLAUDE.md` for detailed context and structure information that helps AI agents understand and work on the codebase.

## License

[Your license here]

## Contributing

[Contributing guidelines]