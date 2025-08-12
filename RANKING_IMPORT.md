# ALFRED Rankings Import Guide

This guide explains how to import new ranking sources into ALFRED using the streamlined import process.

## Quick Start

1. **Examine a new rankings file:**
   ```bash
   python3 import_rankings.py examine path/to/rankings.xlsx
   ```

2. **Import the rankings:**
   ```bash
   python3 import_rankings.py import path/to/rankings.xlsx "Source Name"
   ```

## Examples

### Import Rotowire Rankings
```bash
# First, examine the file structure
python3 import_rankings.py examine "data/rankings/rotowire rankings.xlsx"

# Then import with the recommended settings
python3 import_rankings.py import "data/rankings/rotowire rankings.xlsx" "Rotowire" --sheet "CheatSheetTE"
```

### Import Custom Rankings File
```bash
# For a file with custom column names
python3 import_rankings.py import "my_rankings.xlsx" "My Custom Source" \
  --sheet "Player Rankings" \
  --name-col "Full Name" \
  --position-col "Position" \
  --rank-col "Positional Rank" \
  --team-col "NFL Team"
```

### Import Position-Specific Rankings
```bash
# For sheets containing only one position (like D/ST only)
python3 import_rankings.py import "rankings.xlsx" "Source Name" \
  --sheet "D_ST_Rankings" \
  --force-position "DST" \
  --name-col "Player_Name" \
  --rank-col "Position_Rank" \
  --team-col "Team"
```

## File Format Requirements

The import system expects Excel (.xlsx) files with the following information:
- **Player names** (required) - Full player names
- **Positions** (required) - QB, RB, WR, TE, K, DST
- **Rankings** (required) - Numerical position rankings (1, 2, 3, etc.)
- **Team names** (optional but recommended) - 3-letter team abbreviations

### Supported Team Abbreviations
ARI, ATL, BAL, BUF, CAR, CHI, CIN, CLE, DAL, DEN, DET, GB, HOU, IND, JAX, KC, LAC, LAR, LV, MIA, MIN, NE, NO, NYG, NYJ, PHI, PIT, SEA, SF, TB, TEN, WAS

## Smart Matching Features

The import system includes intelligent player matching:

### Name Variations Handled
- **Jr./Sr. suffixes**: "Brian Thomas" → "Brian Thomas Jr."
- **Roman numerals**: "Kenneth Walker" → "Kenneth Walker III"
- **Case variations**: Automatically handles case differences
- **D/ST variations**: "SF Defense" → "San Francisco 49ers DST"

### Validation Process
1. **Exact match**: Direct name, position, and team match
2. **Fuzzy match**: Tries suffix variations if exact match fails
3. **Suggestions**: Provides similar player suggestions for manual review

## Import Results

After import, you'll see:
- ✅ **Matched players**: Successfully imported rankings
- ❌ **Unmatched players**: Players not found in master index
- ⚠️ **Warnings**: Non-critical issues (invalid ranks, etc.)
- 🚨 **Errors**: Critical problems that prevented processing

## Troubleshooting

### Common Issues

**"Player not found in master index"**
- The player name might have suffix differences (Jr., III, etc.)
- Check team abbreviation is correct
- Player might be inactive or not in database

**"Column not detected"**
- Use specific column parameters: `--name-col`, `--position-col`, etc.
- Check column names in Excel file match expected patterns

**"Database connection failed"**
- Ensure PostgreSQL is running
- Verify `fantasy_draft_db` database exists

### Getting Help

1. **Examine first**: Always run `examine` command to understand file structure
2. **Check suggestions**: Unmatched players show suggestions for corrections
3. **Use dry-run**: Add `--dry-run` flag to see what would be imported

## Technical Details

### Data Validation
- All players validated against master player index
- Only active players are matched
- Rankings must be valid integers
- Duplicate rankings for same source are replaced

### Database Integration
- Creates new ranking source if needed
- Clears existing rankings for the source before importing
- Maintains referential integrity with master player index

### Performance
- Processes files with hundreds of players in seconds
- Fuzzy matching handles common name variations
- Batch database operations for efficiency