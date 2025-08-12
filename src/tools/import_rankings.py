#!/usr/bin/env python3
"""
ALFRED Rankings Import Tool - Streamlined Import Process
Easy-to-use command line tool for importing new ranking sources
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from ranking_importer import RankingImporter

def main():
    parser = argparse.ArgumentParser(
        description='Import fantasy football rankings into ALFRED database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Examine a file structure
  python3 import_rankings.py examine data/rankings/new_rankings.xlsx
  
  # Import with auto-detection
  python3 import_rankings.py import data/rankings/new_rankings.xlsx "Source Name"
  
  # Import with specific parameters
  python3 import_rankings.py import data/rankings/new_rankings.xlsx "Source Name" \\
    --sheet "Rankings" --name-col "Player" --position-col "Pos" --rank-col "Rank"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Examine command
    examine_parser = subparsers.add_parser('examine', help='Examine XLSX file structure')
    examine_parser.add_argument('file_path', help='Path to XLSX file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import rankings from XLSX file')
    import_parser.add_argument('file_path', help='Path to XLSX file')
    import_parser.add_argument('source_name', help='Name for the ranking source (e.g., "FantasyPros", "Rotowire")')
    import_parser.add_argument('--sheet', help='Specific sheet name to import from')
    import_parser.add_argument('--name-col', help='Column name containing player names')
    import_parser.add_argument('--position-col', help='Column name containing positions')
    import_parser.add_argument('--force-position', help='Force all players to this position (e.g., "DST" for defense-only sheets)')
    import_parser.add_argument('--rank-col', help='Column name containing rankings')
    import_parser.add_argument('--team-col', help='Column name containing team names')
    import_parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without actually importing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Validate file exists
    if not os.path.exists(args.file_path):
        print(f"❌ Error: File not found: {args.file_path}")
        return 1
    
    importer = RankingImporter()
    
    if args.command == 'examine':
        print(f"🏈 ALFRED Rankings Import Tool - Examine Mode")
        print("=" * 60)
        
        file_info = importer.examine_xlsx_file(args.file_path)
        
        if 'error' in file_info:
            print(f"❌ Error: {file_info['error']}")
            return 1
        
        print(f"\\n📋 Summary:")
        print(f"   File: {file_info['file_path']}")
        print(f"   Sheets: {len(file_info['sheets'])}")
        if file_info.get('recommended_sheet'):
            print(f"   Recommended sheet: {file_info['recommended_sheet']}")
        
        print(f"\\n💡 Next steps:")
        if file_info.get('recommended_sheet'):
            print(f"   python3 import_rankings.py import \"{args.file_path}\" \"YourSourceName\" --sheet \"{file_info['recommended_sheet']}\"")
        else:
            print(f"   python3 import_rankings.py import \"{args.file_path}\" \"YourSourceName\" --sheet \"SheetName\"")
    
    elif args.command == 'import':
        print(f"🏈 ALFRED Rankings Import Tool - Import Mode")
        print("=" * 60)
        
        if args.dry_run:
            print("🧪 DRY RUN MODE - No data will be imported")
            print("-" * 40)
        
        result = importer.import_rankings(
            file_path=args.file_path,
            source_name=args.source_name,
            sheet_name=args.sheet,
            name_col=args.name_col,
            position_col=args.position_col,
            rank_col=args.rank_col,
            team_col=args.team_col,
            force_position=args.force_position
        )
        
        print(f"\\n📊 Import Results:")
        print(f"   Source: {result.source_name}")
        print(f"   Total rows processed: {result.total_rows}")
        print(f"   ✅ Matched players: {result.matched_players}")
        print(f"   ❌ Unmatched players: {result.unmatched_players}")
        print(f"   ⚠️  Warnings: {len(result.warnings)}")
        print(f"   🚨 Errors: {len(result.errors)}")
        print(f"   📈 Success: {result.success}")
        
        if result.errors:
            print(f"\\n🚨 Errors:")
            for error in result.errors[:5]:  # Show first 5
                print(f"   • {error}")
            if len(result.errors) > 5:
                print(f"   ... and {len(result.errors) - 5} more")
        
        if result.warnings:
            print(f"\\n⚠️  Warnings:")
            for warning in result.warnings[:5]:  # Show first 5
                print(f"   • {warning}")
            if len(result.warnings) > 5:
                print(f"   ... and {len(result.warnings) - 5} more")
        
        if result.success:
            print(f"\\n🎉 Successfully imported {result.matched_players} rankings for {result.source_name}!")
            print(f"   Rankings are now available in the ALFRED interface at http://localhost:5555/rankings")
        else:
            print(f"\\n💥 Import failed. Please check the errors above and try again.")
            return 1

if __name__ == "__main__":
    sys.exit(main() or 0)