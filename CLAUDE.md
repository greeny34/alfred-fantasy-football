# ALFRED - Analytical League Fantasy Resource for Elite Drafting

## Project Overview
ALFRED is a comprehensive fantasy football draft assistant that provides real-time recommendations, player rankings aggregation, and draft strategy optimization. The system integrates with multiple fantasy platforms (ESPN, Sleeper, Yahoo) and aggregates rankings from various sources.

## Current State
- **Database**: PostgreSQL with player, rankings, ADP, and strategy tables
- **Backend**: Python-based scrapers, API servers, and draft engines
- **Frontend**: React + TypeScript dashboard using Vite and D3.js
- **Integrations**: Sleeper API, ESPN scraping, FantasyPros data

## Project Structure (Current - Needs Organization)
```
ff_draft_vibe/
├── ff-dashboard/          # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   └── main.tsx       # Entry point
│   └── package.json       # Frontend dependencies
├── templates/             # HTML templates for web UI
├── *.py                   # 100+ Python files (NEEDS ORGANIZATION)
├── *.xlsx                 # Data files and rankings
└── *.csv                  # Exported data
```

## Key Components

### Database Schema (PostgreSQL)
- **players**: Player information (name, position, team)
- **ranking_sources**: ESPN, FantasyPros, Yahoo, etc.
- **player_rankings**: Rankings by source and date
- **player_adp**: Average Draft Position data
- **draft_boards**: Active draft tracking
- **draft_picks**: Pick history
- **roster_constructions**: Team composition tracking

### Core Python Modules
1. **Draft Engines**
   - `draft_assistant_app.py` - Main desktop app
   - `sleeper_draft_assistant.py` - Sleeper platform integration
   - `simple_draft_engine.py` - Core draft logic
   - `dynamic_draft_optimizer.py` - Strategy optimization

2. **Data Collection**
   - `espn_rankings_scraper.py` - ESPN data collection
   - `fantasy_rankings_aggregator.py` - Combines multiple sources
   - `data_scraper.py` - Generic scraping framework

3. **Database Management**
   - `database_setup.py` - Schema creation
   - `db_inspector.py` - Database utilities

### Frontend (React)
- Located in `ff-dashboard/`
- Uses Vite for development
- TypeScript for type safety
- D3.js for visualizations

## Known Issues
1. **File Organization**: 100+ Python files in root directory
2. **No dependency management**: Missing requirements.txt
3. **Multiple versions**: Unclear which files are current
4. **Sleeper Integration**: User ID mapping issues in mock drafts

## Development Workflow

### Starting Fresh
1. Check database connection: `python database_setup.py`
2. Run data collection: `python fantasy_rankings_aggregator.py`
3. Start React frontend: `cd ff-dashboard && npm run dev`
4. Launch draft assistant: `python draft_assistant_app.py`

### Common Tasks
- **Update rankings**: Run scrapers for each source
- **Test draft logic**: Use `simple_draft_engine.py`
- **Debug Sleeper**: Check `sleeper_draft_issues_analysis.py`

## TODO - Project Organization
1. Create proper directory structure:
   - `src/scrapers/` - Data collection scripts
   - `src/engines/` - Draft logic and algorithms
   - `src/api/` - API servers and endpoints
   - `src/db/` - Database utilities
   - `data/` - Excel and CSV files
   - `scripts/` - One-off utilities

2. Add requirements.txt with all Python dependencies

3. Clean up duplicate/obsolete files

4. Create comprehensive README.md

## Environment Variables
- `USER` - PostgreSQL username (defaults to system user)
- Database: `fantasy_draft_db` on localhost:5432

## Critical Files for AI Agents
When working on this project, always check:
1. `database_setup.py` - Database schema
2. `draft_assistant_app.py` - Main application
3. `ff-dashboard/src/` - Frontend code
4. This file (CLAUDE.md) - Project context

## Draft Board Backup Strategy (CRITICAL)
**NEVER LOSE THE WORKING VERSION AGAIN!**

### Master Working File
- `templates/live_draft_board.html` - CURRENT working version
- `templates/live_draft_board_MASTER_WORKING.html` - Master backup (never edit)

### Multiple Backup Locations
1. **Git Repository**: Committed and pushed to GitHub
2. **Local Backups**:
   - `templates/live_draft_board_WORKING_BACKUP_[timestamp].html`
   - `backups/live_draft_board_RESTORED_[timestamp].html`
   - `~/Desktop/ALFRED_Draft_Board_WORKING_BACKUP.html`

### Backup Versions for Reference
- `templates/live_draft_board_broken.html` - Sophisticated version with stats bug
- `templates/live_draft_board_broken2.html` - Identical to broken.html  
- `templates/live_draft_board_working.html` - Simple working version (not sophisticated)

### Lightweight Version Control Process
1. **Before editing critical files**: Run `./backup_critical_file.sh <file_path>`
   - Creates timestamped backup automatically
   - Commits current state to git as safety measure
2. **After completing changes**: Test functionality, then commit with clear message
3. **Recovery**: If something breaks, restore from most recent backup or use git
4. **Push frequently**: Daily or after significant changes

### Critical Files (Always backup first)
- `templates/live_draft_board.html` - Main draft board
- `src/engines/draft_assistant_app.py` - Main server app
- `src/servers/alfred_main_server.py` - Primary Flask server
- Any file in `templates/` directory

## Recent Work
- ✅ ORGANIZED codebase: Moved 100+ scattered files into logical src/ directory structure
- ✅ IMPLEMENTED lightweight version control with automated backup script
- ✅ RESTORED sophisticated draft board with all features (3-panel UI, dark theme, rankings badges)
- ✅ Fixed JavaScript initialization error (async/await in setTimeout)
- ✅ Created comprehensive backup strategy with organized templates/backups/
- ✅ Committed and pushed working version to GitHub
- Previous: Sleeper integration debugging, Mock draft functionality, React dashboard development