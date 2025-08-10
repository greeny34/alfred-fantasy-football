#!/usr/bin/env python3
"""
Organize ALFRED project files into a clean directory structure
This script will move files into appropriate directories
"""

import os
import shutil
from pathlib import Path

# Define the new directory structure
DIRECTORIES = {
    'src/scrapers': 'Web scraping and data collection scripts',
    'src/engines': 'Draft engines and core logic',
    'src/api': 'API servers and endpoints',
    'src/db': 'Database utilities and setup',
    'src/utils': 'Helper utilities and tools',
    'data/rankings': 'Excel and CSV ranking files',
    'data/exports': 'Exported data files',
    'scripts': 'One-off scripts and utilities',
    'docs': 'Documentation files',
    'tests': 'Test files'
}

# File mapping rules
FILE_MAPPINGS = {
    'src/scrapers': [
        '*scraper*.py',
        'espn_*.py',
        'fantasy_rankings_aggregator.py',
        'data_scraper.py',
        'raw_data_scraper.py',
        'comprehensive_position_scraper.py',
        'mike_clay_*.py',
        'nfl_roster_scraper.py'
    ],
    'src/engines': [
        '*draft_engine*.py',
        'draft_simulator.py',
        'draft_assistant*.py',
        'dynamic_draft_optimizer.py',
        'draft_recommendations.py',
        'mock_draft_*.py',
        'simple_draft_*.py'
    ],
    'src/api': [
        '*server*.py',
        'sleeper_api_*.py',
        'web_scraper_draft_assistant.py'
    ],
    'src/db': [
        'database_setup.py',
        'db_*.py',
        'create_*_schema.py',
        'query_db.py'
    ],
    'src/utils': [
        'check_*.py',
        'debug_*.py',
        'verify_*.py',
        'fix_*.py',
        'add_*.py',
        'load_*.py',
        'export_*.py',
        'show_*.py'
    ],
    'data/rankings': [
        '*.xlsx',
        '*.csv'
    ],
    'scripts': [
        'test_*.py',
        'run_*.py',
        'make_*.py',
        'install_*.py',
        '*.sh',
        '*.command'
    ],
    'docs': [
        '*.md',
        '!README.md',
        '!CLAUDE.md'
    ]
}

def create_directories():
    """Create the directory structure"""
    print("🏗️  Creating directory structure...")
    for dir_path, description in DIRECTORIES.items():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created {dir_path}/ - {description}")

def should_skip_file(filename):
    """Check if file should be skipped"""
    skip_patterns = [
        '.pyc',
        '__pycache__',
        '.DS_Store',
        '~$',  # Temporary Excel files
        'organize_project.py'  # Don't move this script
    ]
    return any(pattern in filename for pattern in skip_patterns)

def find_matching_files(pattern, existing_files):
    """Find files matching a pattern"""
    import fnmatch
    return [f for f in existing_files if fnmatch.fnmatch(f, pattern)]

def organize_files():
    """Move files to appropriate directories"""
    print("\n📁 Organizing files...")
    
    # Get list of all files in current directory
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    moved_files = set()
    
    # Process each directory's patterns
    for target_dir, patterns in FILE_MAPPINGS.items():
        for pattern in patterns:
            matching_files = find_matching_files(pattern, all_files)
            
            for filename in matching_files:
                if filename in moved_files or should_skip_file(filename):
                    continue
                    
                src = filename
                dst = os.path.join(target_dir, filename)
                
                try:
                    # Actually move the file
                    shutil.move(src, dst)
                    print(f"   ✓ Moved: {src} → {dst}")
                    moved_files.add(filename)
                except Exception as e:
                    print(f"   ❌ Error with {filename}: {e}")

    # Report unmoved files
    unmoved = [f for f in all_files if f not in moved_files and not should_skip_file(f)]
    if unmoved:
        print(f"\n⚠️  Files that won't be moved ({len(unmoved)}):")
        for f in unmoved[:10]:  # Show first 10
            print(f"   - {f}")
        if len(unmoved) > 10:
            print(f"   ... and {len(unmoved) - 10} more")

def create_gitignore():
    """Create appropriate .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
~$*
*.tmp
*.temp

# Data files (consider if you want these in git)
*.xlsx
*.csv

# Node (for frontend)
node_modules/
dist/
build/

# Logs
*.log

# Database
*.db
*.sqlite
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    print("\n✅ Created .gitignore file")

def main():
    """Main organization function"""
    print("🏈 ALFRED Project Organizer")
    print("=" * 50)
    
    # Show what will happen
    print("\n🚀 ORGANIZING PROJECT - Files will be moved")
    print("Creating clean directory structure\n")
    
    # Create directories
    create_directories()
    
    # Show file organization plan
    organize_files()
    
    # Create .gitignore
    create_gitignore()
    
    print("\n" + "=" * 50)
    print("📋 To actually organize files, modify this script to move files")
    print("   Change the organize_files() function to use shutil.move()")
    print("\n💡 Next steps:")
    print("   1. Review the proposed file movements")
    print("   2. Run with actual file moving enabled")
    print("   3. Update imports in Python files")
    print("   4. Create requirements.txt")

if __name__ == "__main__":
    main()