#!/usr/bin/env python3
"""
ALFRED Clean - Master Player Index View
Shows exactly what's in the database - no fluff, just facts
"""

from flask import Flask, render_template_string, jsonify, request, render_template
import psycopg2
import os
import sys
import json
import webbrowser
import signal
import threading

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': os.environ.get('USER', 'jeffgreenfield'),
    'database': 'fantasy_draft_db'
}

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Master index template - clean and simple
MASTER_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Master Player Index</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .header { background-color: #1e3a8a; color: white; padding: 20px 0; margin-bottom: 30px; }
        .player-table { background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .position-QB { color: #dc3545; font-weight: bold; }
        .position-RB { color: #28a745; font-weight: bold; }
        .position-WR { color: #007bff; font-weight: bold; }
        .position-TE { color: #ffc107; font-weight: bold; }
        .position-K { color: #6c757d; font-weight: bold; }
        .position-DST { color: #6f42c1; font-weight: bold; }
        .stats-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .filter-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .active-badge { color: #28a745; }
        .inactive-badge { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1>🏈 ALFRED - Master Player Index</h1>
                    <p class="mb-0">The single source of truth for all player data</p>
                </div>
                <div class="col-md-4 text-end">
                    <a href="/rankings" class="btn btn-primary me-2">
                        <i class="fas fa-list-ol"></i> Player Rankings
                    </a>
                    <a href="/draft-board" class="btn btn-success me-2">
                        <i class="fas fa-chess-board"></i> Draft Board
                    </a>
                    <a href="/shutdown" class="btn btn-danger">
                        <i class="fas fa-power-off"></i> Shutdown
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Statistics -->
        <div class="stats-card">
            <h5>Database Statistics</h5>
            <div class="row" id="stats">
                <div class="col-md-2">
                    <strong>Total Players:</strong> <span id="totalPlayers">-</span>
                </div>
                <div class="col-md-2">
                    <strong>Active:</strong> <span id="activePlayers" class="active-badge">-</span>
                </div>
                <div class="col-md-2">
                    <strong>Inactive:</strong> <span id="inactivePlayers" class="inactive-badge">-</span>
                </div>
                <div class="col-md-6" id="positionCounts">
                    <!-- Position counts will go here -->
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="filter-section">
            <h5>Filters</h5>
            <div class="row">
                <div class="col-md-3">
                    <label>Search Name:</label>
                    <input type="text" id="searchName" class="form-control" placeholder="Player name...">
                </div>
                <div class="col-md-2">
                    <label>Position:</label>
                    <select id="filterPosition" class="form-select">
                        <option value="">All Positions</option>
                        <option value="QB">QB</option>
                        <option value="RB">RB</option>
                        <option value="WR">WR</option>
                        <option value="TE">TE</option>
                        <option value="K">K</option>
                        <option value="DST">DST</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label>Team:</label>
                    <select id="filterTeam" class="form-select">
                        <option value="">All Teams</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label>Status:</label>
                    <select id="filterActive" class="form-select">
                        <option value="">All</option>
                        <option value="true">Active Only</option>
                        <option value="false">Inactive Only</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label>&nbsp;</label>
                    <div>
                        <button class="btn btn-primary" onclick="applyFilters()">
                            <i class="fas fa-filter"></i> Apply Filters
                        </button>
                        <button class="btn btn-secondary" onclick="clearFilters()">
                            <i class="fas fa-times"></i> Clear
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Player Table -->
        <div class="player-table">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Team</th>
                        <th>Status</th>
                        <th>Year</th>
                        <th>Rookie</th>
                    </tr>
                </thead>
                <tbody id="playerTableBody">
                    <tr>
                        <td colspan="7" class="text-center">Loading players...</td>
                    </tr>
                </tbody>
            </table>
            
            <!-- Pagination -->
            <div class="d-flex justify-content-between align-items-center p-3">
                <div>
                    Showing <span id="showingCount">0</span> of <span id="totalCount">0</span> players
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-primary" onclick="previousPage()" id="prevBtn">
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <span class="mx-3">Page <span id="currentPage">1</span> of <span id="totalPages">1</span></span>
                    <button class="btn btn-sm btn-outline-primary" onclick="nextPage()" id="nextBtn">
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentPage = 1;
        const playersPerPage = 50;
        let allPlayers = [];
        let filteredPlayers = [];
        let teams = [];

        // Load initial data
        async function loadData() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/stats');
                const stats = await statsResponse.json();
                updateStats(stats);
                
                // Load all players
                const playersResponse = await fetch('/api/master-index');
                allPlayers = await playersResponse.json();
                
                // Extract unique teams
                teams = [...new Set(allPlayers.map(p => p.team))].sort();
                populateTeamFilter();
                
                // Show all players initially
                filteredPlayers = allPlayers;
                displayPlayers();
                
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        function updateStats(stats) {
            document.getElementById('totalPlayers').textContent = stats.total;
            document.getElementById('activePlayers').textContent = stats.active;
            document.getElementById('inactivePlayers').textContent = stats.inactive;
            
            // Position counts
            let positionHtml = '';
            for (const [pos, count] of Object.entries(stats.by_position)) {
                positionHtml += `<span class="position-${pos} me-3">${pos}: ${count}</span>`;
            }
            document.getElementById('positionCounts').innerHTML = positionHtml;
        }

        function populateTeamFilter() {
            const select = document.getElementById('filterTeam');
            select.innerHTML = '<option value="">All Teams</option>';
            teams.forEach(team => {
                select.innerHTML += `<option value="${team}">${team}</option>`;
            });
        }

        function displayPlayers() {
            const tbody = document.getElementById('playerTableBody');
            const start = (currentPage - 1) * playersPerPage;
            const end = start + playersPerPage;
            const pagePlayers = filteredPlayers.slice(start, end);
            
            if (pagePlayers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">No players found</td></tr>';
                return;
            }
            
            tbody.innerHTML = pagePlayers.map(player => `
                <tr>
                    <td>${player.player_id}</td>
                    <td><strong>${player.name}</strong></td>
                    <td class="position-${player.position}">${player.position}</td>
                    <td>${player.team}</td>
                    <td>
                        ${player.is_active ? 
                            '<span class="badge bg-success">Active</span>' : 
                            '<span class="badge bg-danger">Inactive</span>'}
                    </td>
                    <td>${player.year}</td>
                    <td>
                        ${player.rookie_year === 2025 ? 
                            '<span class="badge bg-warning text-dark">2025 Rookie</span>' : 
                            '-'}
                    </td>
                </tr>
            `).join('');
            
            updatePagination();
        }

        function updatePagination() {
            const totalPages = Math.ceil(filteredPlayers.length / playersPerPage);
            document.getElementById('currentPage').textContent = currentPage;
            document.getElementById('totalPages').textContent = totalPages;
            document.getElementById('showingCount').textContent = filteredPlayers.length;
            document.getElementById('totalCount').textContent = allPlayers.length;
            
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage === totalPages;
        }

        function applyFilters() {
            const name = document.getElementById('searchName').value.toLowerCase();
            const position = document.getElementById('filterPosition').value;
            const team = document.getElementById('filterTeam').value;
            const active = document.getElementById('filterActive').value;
            
            filteredPlayers = allPlayers.filter(player => {
                if (name && !player.name.toLowerCase().includes(name)) return false;
                if (position && player.position !== position) return false;
                if (team && player.team !== team) return false;
                if (active && player.is_active.toString() !== active) return false;
                return true;
            });
            
            currentPage = 1;
            displayPlayers();
        }

        function clearFilters() {
            document.getElementById('searchName').value = '';
            document.getElementById('filterPosition').value = '';
            document.getElementById('filterTeam').value = '';
            document.getElementById('filterActive').value = '';
            filteredPlayers = allPlayers;
            currentPage = 1;
            displayPlayers();
        }

        function previousPage() {
            if (currentPage > 1) {
                currentPage--;
                displayPlayers();
            }
        }

        function nextPage() {
            const totalPages = Math.ceil(filteredPlayers.length / playersPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                displayPlayers();
            }
        }

        // Auto-search on enter key
        document.getElementById('searchName').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });

        // Load data on page load
        loadData();
    </script>
</body>
</html>
"""

# Enhanced Player Rankings template with statistics and source selection
PLAYER_RANKINGS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Player Rankings</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-size: 13px; }
        .header { background-color: #1e3a8a; color: white; padding: 15px 0; margin-bottom: 20px; }
        .rankings-table { background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .position-QB { color: #dc3545; font-weight: bold; }
        .position-RB { color: #28a745; font-weight: bold; }
        .position-WR { color: #007bff; font-weight: bold; }
        .position-TE { color: #ffc107; font-weight: bold; }
        .position-K { color: #6c757d; font-weight: bold; }
        .position-DST { color: #6f42c1; font-weight: bold; }
        .sortable { cursor: pointer; user-select: none; font-size: 11px; }
        .sortable:hover { background-color: #e9ecef !important; }
        .sort-arrow { font-size: 0.7em; opacity: 0.5; }
        .sort-arrow.active { opacity: 1; color: #007bff; }
        .table-container { overflow-x: auto; }
        .sticky-column { position: sticky; left: 0; background: white; z-index: 10; min-width: 120px; max-width: 120px; }
        .ranking-section { border-left: 2px solid #007bff; font-size: 11px; min-width: 35px; max-width: 35px; }
        .adp-section { border-left: 2px solid #28a745; font-size: 11px; min-width: 40px; max-width: 40px; }
        .stats-section { border-left: 2px solid #dc3545; font-size: 10px; min-width: 45px; max-width: 45px; }
        .section-header { background-color: #f8f9fa !important; font-weight: bold; text-align: center; font-size: 11px; }
        .compact-cell { padding: 2px 4px !important; text-align: center; }
        .ordinal { font-weight: bold; color: #666; font-size: 12px; min-width: 30px; }
        .player-name { font-size: 12px; font-weight: bold; }
        .source-controls { background: white; padding: 10px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .source-section { margin-bottom: 15px; }
        .source-title { font-weight: bold; margin-bottom: 8px; color: #333; }
        .source-group { display: flex; flex-wrap: wrap; gap: 10px; }
        .source-item { display: flex; align-items: center; margin-right: 15px; }
        .source-item input[type="radio"] { margin-right: 5px; }
        .source-item label { font-size: 11px; cursor: pointer; }
        .stats-value { font-size: 10px; }
        .short-name { max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container-fluid">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h3>🏈 ALFRED - Player Rankings</h3>
                    <p class="mb-0" style="font-size: 14px;">Enhanced Rankings with Statistics</p>
                </div>
                <div class="col-md-4 text-end">
                    <a href="/" class="btn btn-light btn-sm me-2">
                        <i class="fas fa-home"></i> Index
                    </a>
                    <a href="/draft-board" class="btn btn-success btn-sm me-2">
                        <i class="fas fa-chess-board"></i> Draft Board
                    </a>
                    <a href="/shutdown" class="btn btn-danger btn-sm">
                        <i class="fas fa-power-off"></i> Exit
                    </a>
                </div>
            </div>
        </div>
    </div>

    <div class="container-fluid">
        <!-- Source Selection Controls -->
        <div class="source-controls">
            <div class="row">
                <div class="col-md-6">
                    <div class="source-section">
                        <div class="source-title">📊 Position Rankings Sources:</div>
                        <div class="source-group" id="rankingSourceControls">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="source-section">
                        <div class="source-title">📈 ADP Sources:</div>
                        <div class="source-group" id="adpSourceControls">
                            <!-- Dynamic content -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Position Filter -->
        <div class="mb-3 bg-white p-2 rounded shadow-sm">
            <div class="row align-items-center">
                <div class="col-md-2">
                    <label class="fw-bold" style="font-size: 12px;">Position:</label>
                    <select id="positionFilter" class="form-select form-select-sm" onchange="filterByPosition()">
                        <option value="">All</option>
                        <option value="QB">QB</option>
                        <option value="RB">RB</option>
                        <option value="WR">WR</option>
                        <option value="TE">TE</option>
                        <option value="K">K</option>
                        <option value="DST">DST</option>
                    </select>
                </div>
                <div class="col-md-10">
                    <small class="text-muted">
                        <i class="fas fa-info-circle"></i> 
                        Select ranking sources above, then filter by position. Statistics calculated from selected sources only.
                    </small>
                </div>
            </div>
        </div>

        <!-- Loading indicator -->
        <div id="loading" class="text-center p-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading rankings...</p>
        </div>

        <!-- Rankings Table -->
        <div id="rankingsContainer" style="display: none;">
            <div class="rankings-table table-container">
                <table class="table table-hover table-sm table-bordered" id="rankingsTable">
                    <thead class="table-light">
                        <tr>
                            <!-- Fixed columns -->
                            <th class="ordinal">#</th>
                            <th class="sticky-column sortable" onclick="sortTable('name')">
                                Name <span class="sort-arrow" data-column="name">↕</span>
                            </th>
                            <th class="sortable compact-cell" onclick="sortTable('position')">
                                Pos <span class="sort-arrow" data-column="position">↕</span>
                            </th>
                            <th class="sortable compact-cell" onclick="sortTable('team')">
                                Tm <span class="sort-arrow" data-column="team">↕</span>
                            </th>
                            
                            <!-- Position Rankings Section -->
                            <th class="section-header ranking-section" id="rankingHeaders" colspan="1">Position Rankings</th>
                            
                            <!-- Ranking Stats Section -->
                            <th class="section-header stats-section" id="rankingStatsHeaders" colspan="5">Rank Stats</th>
                            
                            <!-- ADP Section -->
                            <th class="section-header adp-section" id="adpHeaders" colspan="1">ADP Data</th>
                            
                            <!-- ADP Stats Section -->
                            <th class="section-header stats-section" id="adpStatsHeaders" colspan="5">ADP Stats</th>
                        </tr>
                        <tr id="columnHeaders">
                            <!-- Dynamic headers will be inserted here -->
                        </tr>
                    </thead>
                    <tbody id="rankingsTableBody">
                        <!-- Data will be inserted here -->
                    </tbody>
                </table>
            </div>
            
            <div class="mt-2 text-center text-muted">
                <small>Showing <span id="playerCount">0</span> players | Avg=Ordinal Ranks (1=best) | Min/Max/Std/CV=Raw Values</small>
            </div>
        </div>
    </div>

    <script>
        let playersData = [];
        let allPlayersData = [];
        let allRankingSources = [];
        let allAdpSources = [];
        let selectedRankingSources = [];
        let selectedAdpSources = [];
        let currentSort = { column: null, ascending: true };

        async function loadRankings() {
            try {
                const response = await fetch('/api/player-rankings');
                const data = await response.json();
                
                allPlayersData = data.players;
                playersData = allPlayersData;
                allRankingSources = data.ranking_sources;
                allAdpSources = data.adp_sources;
                
                // Select all sources by default
                selectedRankingSources = [...allRankingSources];
                selectedAdpSources = [...allAdpSources];
                
                setupSourceControls();
                setupTable();
                calculateStatistics();
                displayData();
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('rankingsContainer').style.display = 'block';
                
            } catch (error) {
                console.error('Error loading rankings:', error);
                document.getElementById('loading').innerHTML = 
                    '<div class="alert alert-danger">Error loading rankings data</div>';
            }
        }

        function setupSourceControls() {
            // Ranking sources
            const rankingControls = document.getElementById('rankingSourceControls');
            rankingControls.innerHTML = allRankingSources.map(source => `
                <div class="source-item">
                    <input type="checkbox" id="rank_${source}" checked onchange="updateSelectedSources()">
                    <label for="rank_${source}">${shortenSourceName(source)}</label>
                </div>
            `).join('');
            
            // ADP sources  
            const adpControls = document.getElementById('adpSourceControls');
            adpControls.innerHTML = allAdpSources.map(source => `
                <div class="source-item">
                    <input type="checkbox" id="adp_${source}" checked onchange="updateSelectedSources()">
                    <label for="adp_${source}">${source}</label>
                </div>
            `).join('');
        }

        function shortenSourceName(name) {
            const shortNames = {
                'ESPN_Bowen': 'Bowen',
                'ESPN_Cockcroft': 'Cockcroft', 
                'ESPN_Dopp': 'Dopp',
                'ESPN_Karabell': 'Karabell',
                'ESPN_Loza': 'Loza',
                'ESPN_Moody': 'Moody',
                'ESPN_Yates': 'Yates',
                'FantasyPros': 'FPros',
                'Mike_Clay_Position_Rankings': 'M.Clay',
                'Rotowire': 'Roto',
                'Underdog': 'Under'
            };
            return shortNames[name] || name.substring(0, 6);
        }

        function updateSelectedSources() {
            // Update selected ranking sources
            selectedRankingSources = allRankingSources.filter(source => 
                document.getElementById(`rank_${source}`).checked
            );
            
            // Update selected ADP sources
            selectedAdpSources = allAdpSources.filter(source => 
                document.getElementById(`adp_${source}`).checked
            );
            
            setupTable();
            calculateStatistics();
            displayData();
        }

        function setupTable() {
            // Update column spans
            document.getElementById('rankingHeaders').setAttribute('colspan', selectedRankingSources.length || 1);
            document.getElementById('adpHeaders').setAttribute('colspan', selectedAdpSources.length || 1);
            
            // Build column headers
            let headers = '<th></th><th></th><th></th><th></th>'; // Empty cells for #, name, pos, team
            
            // Ranking source headers
            selectedRankingSources.forEach(source => {
                headers += `<th class="sortable ranking-section compact-cell" onclick="sortTable('rank_${source}')" title="${source}">
                    ${shortenSourceName(source)}<br>
                    <span class="sort-arrow" data-column="rank_${source}">↕</span>
                </th>`;
            });
            
            // Ranking stats headers
            headers += `
                <th class="sortable stats-section compact-cell" onclick="sortTable('rank_avg')" title="Ordinal Ranking (1=best average rank)">
                    Avg<br><span class="sort-arrow" data-column="rank_avg">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('rank_min')" title="Best Rank">
                    Min<br><span class="sort-arrow" data-column="rank_min">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('rank_max')" title="Worst Rank">
                    Max<br><span class="sort-arrow" data-column="rank_max">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('rank_std')" title="Standard Deviation">
                    Std<br><span class="sort-arrow" data-column="rank_std">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('rank_cv')" title="Coefficient of Variation">
                    CV<br><span class="sort-arrow" data-column="rank_cv">↕</span>
                </th>
            `;
            
            // ADP source headers
            selectedAdpSources.forEach(source => {
                headers += `<th class="sortable adp-section compact-cell" onclick="sortTable('adp_${source}')" title="${source}">
                    ${source}<br>
                    <span class="sort-arrow" data-column="adp_${source}">↕</span>
                </th>`;
            });
            
            // ADP stats headers
            headers += `
                <th class="sortable stats-section compact-cell" onclick="sortTable('adp_avg')" title="Ordinal ADP Ranking (1=best average ADP)">
                    Avg<br><span class="sort-arrow" data-column="adp_avg">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('adp_min')" title="Best ADP">
                    Min<br><span class="sort-arrow" data-column="adp_min">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('adp_max')" title="Worst ADP">
                    Max<br><span class="sort-arrow" data-column="adp_max">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('adp_std')" title="Standard Deviation">
                    Std<br><span class="sort-arrow" data-column="adp_std">↕</span>
                </th>
                <th class="sortable stats-section compact-cell" onclick="sortTable('adp_cv')" title="Coefficient of Variation">
                    CV<br><span class="sort-arrow" data-column="adp_cv">↕</span>
                </th>
            `;
            
            document.getElementById('columnHeaders').innerHTML = headers;
        }

        function calculateStatistics() {
            // First pass: calculate raw averages and other stats
            playersData.forEach(player => {
                // Calculate ranking statistics
                const rankValues = selectedRankingSources
                    .map(source => player.rankings[source])
                    .filter(val => val != null && !isNaN(val))
                    .map(val => parseInt(val));
                
                if (rankValues.length > 0) {
                    player.rank_avg_raw = rankValues.reduce((a, b) => a + b, 0) / rankValues.length;
                    player.rank_min = Math.min(...rankValues);
                    player.rank_max = Math.max(...rankValues);
                    
                    const mean = player.rank_avg_raw;
                    const variance = rankValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / rankValues.length;
                    player.rank_std = Math.sqrt(variance).toFixed(1);
                    player.rank_cv = mean > 0 ? (Math.sqrt(variance) / mean * 100).toFixed(0) + '%' : '-';
                } else {
                    player.rank_avg_raw = null;
                    player.rank_min = player.rank_max = player.rank_std = player.rank_cv = '-';
                }
                
                // Calculate ADP statistics
                const adpValues = selectedAdpSources
                    .map(source => player.adp[source])
                    .filter(val => val != null && !isNaN(val))
                    .map(val => parseFloat(val));
                
                if (adpValues.length > 0) {
                    player.adp_avg_raw = adpValues.reduce((a, b) => a + b, 0) / adpValues.length;
                    player.adp_min = Math.min(...adpValues).toFixed(1);
                    player.adp_max = Math.max(...adpValues).toFixed(1);
                    
                    const mean = player.adp_avg_raw;
                    const variance = adpValues.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / adpValues.length;
                    player.adp_std = Math.sqrt(variance).toFixed(1);
                    player.adp_cv = mean > 0 ? (Math.sqrt(variance) / mean * 100).toFixed(0) + '%' : '-';
                } else {
                    player.adp_avg_raw = null;
                    player.adp_min = player.adp_max = player.adp_std = player.adp_cv = '-';
                }
            });
            
            // Second pass: convert averages to ordinal rankings
            convertAveragesToOrdinals();
        }

        function convertAveragesToOrdinals() {
            // Convert ranking averages to ordinals (better rank = lower number = higher ordinal position)
            const playersWithRankings = playersData.filter(p => p.rank_avg_raw !== null);
            playersWithRankings.sort((a, b) => a.rank_avg_raw - b.rank_avg_raw);
            
            playersWithRankings.forEach((player, index) => {
                player.rank_avg = index + 1;
            });
            
            // Set ordinal to '-' for players without rankings
            playersData.filter(p => p.rank_avg_raw === null).forEach(player => {
                player.rank_avg = '-';
            });
            
            // Convert ADP averages to ordinals (better ADP = lower number = higher ordinal position)  
            const playersWithADP = playersData.filter(p => p.adp_avg_raw !== null);
            playersWithADP.sort((a, b) => a.adp_avg_raw - b.adp_avg_raw);
            
            playersWithADP.forEach((player, index) => {
                player.adp_avg = index + 1;
            });
            
            // Set ordinal to '-' for players without ADP
            playersData.filter(p => p.adp_avg_raw === null).forEach(player => {
                player.adp_avg = '-';
            });
        }

        function displayData() {
            const tbody = document.getElementById('rankingsTableBody');
            
            if (playersData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="100" class="text-center">No ranking data available</td></tr>';
                return;
            }
            
            tbody.innerHTML = playersData.map((player, index) => {
                let row = `<tr>
                    <td class="ordinal compact-cell">${index + 1}</td>
                    <td class="sticky-column player-name short-name" title="${player.name}">${player.name}</td>
                    <td class="position-${player.position} compact-cell">${player.position}</td>
                    <td class="compact-cell">${player.team}</td>`;
                
                // Add ranking columns
                selectedRankingSources.forEach(source => {
                    const value = player.rankings[source];
                    row += `<td class="compact-cell ranking-section">${value || '-'}</td>`;
                });
                
                // Add ranking stats
                row += `
                    <td class="compact-cell stats-section stats-value">${player.rank_avg}</td>
                    <td class="compact-cell stats-section stats-value">${player.rank_min}</td>
                    <td class="compact-cell stats-section stats-value">${player.rank_max}</td>
                    <td class="compact-cell stats-section stats-value">${player.rank_std}</td>
                    <td class="compact-cell stats-section stats-value">${player.rank_cv}</td>
                `;
                
                // Add ADP columns
                selectedAdpSources.forEach(source => {
                    const value = player.adp[source];
                    row += `<td class="compact-cell adp-section">${value || '-'}</td>`;
                });
                
                // Add ADP stats
                row += `
                    <td class="compact-cell stats-section stats-value">${player.adp_avg}</td>
                    <td class="compact-cell stats-section stats-value">${player.adp_min}</td>
                    <td class="compact-cell stats-section stats-value">${player.adp_max}</td>
                    <td class="compact-cell stats-section stats-value">${player.adp_std}</td>
                    <td class="compact-cell stats-section stats-value">${player.adp_cv}</td>
                `;
                
                row += '</tr>';
                return row;
            }).join('');
            
            document.getElementById('playerCount').textContent = playersData.length;
        }

        function sortTable(column) {
            // Update sort arrows
            document.querySelectorAll('.sort-arrow').forEach(arrow => {
                arrow.classList.remove('active');
                arrow.textContent = '↕';
            });
            
            const arrow = document.querySelector(`[data-column="${column}"]`);
            
            // Toggle sort direction
            if (currentSort.column === column) {
                currentSort.ascending = !currentSort.ascending;
            } else {
                currentSort.column = column;
                currentSort.ascending = true;
            }
            
            // Update arrow
            if (arrow) {
                arrow.classList.add('active');
                arrow.textContent = currentSort.ascending ? '↑' : '↓';
            }
            
            // Sort data
            playersData.sort((a, b) => {
                let aVal, bVal;
                
                if (column === 'name') {
                    aVal = a.name;
                    bVal = b.name;
                } else if (column === 'position') {
                    aVal = a.position;
                    bVal = b.position;
                } else if (column === 'team') {
                    aVal = a.team;
                    bVal = b.team;
                } else if (column.startsWith('rank_')) {
                    const source = column.substring(5);
                    if (['avg', 'min', 'max', 'std'].includes(source)) {
                        // For ordinal averages and integer stats, convert to numbers
                        aVal = (a[column] === '-') ? 999 : parseInt(a[column]) || 999;
                        bVal = (b[column] === '-') ? 999 : parseInt(b[column]) || 999;
                    } else if (source === 'cv') {
                        // Handle percentage values for CV
                        aVal = (a[column] === '-') ? 999 : parseFloat(a[column]) || 999;
                        bVal = (b[column] === '-') ? 999 : parseFloat(b[column]) || 999;
                    } else {
                        aVal = a.rankings[source] || 999;
                        bVal = b.rankings[source] || 999;
                    }
                } else if (column.startsWith('adp_')) {
                    const source = column.substring(4);
                    if (source === 'avg') {
                        // For ordinal ADP averages, convert to numbers
                        aVal = (a[column] === '-') ? 999 : parseInt(a[column]) || 999;
                        bVal = (b[column] === '-') ? 999 : parseInt(b[column]) || 999;
                    } else if (['min', 'max', 'std'].includes(source)) {
                        aVal = (a[column] === '-') ? 999 : parseFloat(a[column]) || 999;
                        bVal = (b[column] === '-') ? 999 : parseFloat(b[column]) || 999;
                    } else if (source === 'cv') {
                        // Handle percentage values for CV
                        aVal = (a[column] === '-') ? 999 : parseFloat(a[column]) || 999;
                        bVal = (b[column] === '-') ? 999 : parseFloat(b[column]) || 999;
                    } else {
                        aVal = a.adp[source] || 999;
                        bVal = b.adp[source] || 999;
                    }
                }
                
                // Handle string vs number comparison
                if (typeof aVal === 'string' && typeof bVal === 'string') {
                    return currentSort.ascending ? 
                        aVal.localeCompare(bVal) : 
                        bVal.localeCompare(aVal);
                } else {
                    return currentSort.ascending ? 
                        aVal - bVal : 
                        bVal - aVal;
                }
            });
            
            displayData();
        }

        function filterByPosition() {
            const position = document.getElementById('positionFilter').value;
            
            if (position === '') {
                playersData = [...allPlayersData];
            } else {
                playersData = allPlayersData.filter(p => p.position === position);
            }
            
            // Recalculate statistics with filtered data for proper ordinal rankings
            calculateStatistics();
            displayData();
        }

        // Load data on page load
        loadRankings();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Master player index view"""
    return render_template_string(MASTER_INDEX_TEMPLATE)

@app.route('/rankings')
def rankings():
    """Player rankings view"""
    return render_template_string(PLAYER_RANKINGS_TEMPLATE)

@app.route('/draft-board')
def draft_board():
    """Live draft board view"""
    return render_template('live_draft_board.html')

@app.route('/team-analysis/<int:team_number>')
def team_analysis(team_number):
    """Team analysis view"""
    # Will implement this next
    return f"<h1>Team {team_number} Analysis - Coming Soon</h1>"

@app.route('/position-analysis')
def position_analysis():
    """Position analysis view"""
    # Will implement this next
    return "<h1>Position Analysis - Coming Soon</h1>"

@app.route('/api/master-index')
def api_master_index():
    """Get all players from master index"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT player_id, name, position, team, is_active, year, rookie_year
            FROM players
            ORDER BY position, team, name
        """)
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'is_active': row[4],
                'year': row[5],
                'rookie_year': row[6]
            })
        
        cur.close()
        conn.close()
        return jsonify(players)
        
    except Exception as e:
        print(f"Error fetching players: {e}")
        if conn:
            conn.close()
        return jsonify([])

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({})
    
    try:
        cur = conn.cursor()
        
        # Total count
        cur.execute("SELECT COUNT(*) FROM players")
        total = cur.fetchone()[0]
        
        # Active/Inactive
        cur.execute("SELECT COUNT(*) FROM players WHERE is_active = TRUE")
        active = cur.fetchone()[0]
        
        # By position
        cur.execute("""
            SELECT position, COUNT(*) 
            FROM players 
            GROUP BY position 
            ORDER BY position
        """)
        by_position = dict(cur.fetchall())
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total': total,
            'active': active,
            'inactive': total - active,
            'by_position': by_position
        })
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        if conn:
            conn.close()
        return jsonify({})

@app.route('/api/player-rankings')
def api_player_rankings():
    """Get all players with their ranking and ADP data"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'players': [], 'ranking_sources': [], 'adp_sources': []})
    
    try:
        cur = conn.cursor()
        
        # Get ranking sources that have actual data
        cur.execute("""
            SELECT rs.source_name 
            FROM ranking_sources rs
            WHERE EXISTS (
                SELECT 1 FROM player_rankings pr 
                WHERE pr.source_id = rs.source_id
            )
            ORDER BY rs.source_name
        """)
        ranking_sources = [row[0] for row in cur.fetchall()]
        
        # Get all ADP sources
        cur.execute("""
            SELECT source_name 
            FROM adp_sources 
            WHERE is_active = true
            ORDER BY source_name
        """)
        adp_sources = [row[0] for row in cur.fetchall()]
        
        # Get players with at least one ranking or ADP value
        cur.execute("""
            SELECT DISTINCT p.player_id, p.name, p.position, p.team
            FROM players p
            WHERE EXISTS (
                SELECT 1 FROM player_rankings pr WHERE pr.player_id = p.player_id
            ) OR EXISTS (
                SELECT 1 FROM adp_rankings ar WHERE ar.player_id = p.player_id
            )
            ORDER BY p.position, p.name
        """)
        
        players_data = []
        for row in cur.fetchall():
            player_id, name, position, team = row
            
            # Get all position rankings for this player
            cur.execute("""
                SELECT rs.source_name, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE pr.player_id = %s
            """, (player_id,))
            
            rankings = {}
            for ranking_row in cur.fetchall():
                source, rank = ranking_row
                rankings[source] = rank
            
            # Get all ADP values for this player
            cur.execute("""
                SELECT ads.source_name, ar.adp_value
                FROM adp_rankings ar
                JOIN adp_sources ads ON ar.adp_source_id = ads.adp_source_id
                WHERE ar.player_id = %s
            """, (player_id,))
            
            adp_values = {}
            for adp_row in cur.fetchall():
                source, adp = adp_row
                if adp is not None:
                    adp_values[source] = round(float(adp), 1)
            
            players_data.append({
                'player_id': player_id,
                'name': name,
                'position': position,
                'team': team,
                'rankings': rankings,
                'adp': adp_values
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'players': players_data,
            'ranking_sources': ranking_sources,
            'adp_sources': adp_sources
        })
        
    except Exception as e:
        print(f"Error fetching rankings: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return jsonify({'players': [], 'ranking_sources': [], 'adp_sources': [], 'error': str(e)})

@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    """Shutdown the server gracefully"""
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Shutdown ALFRED</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-danger text-white">
                                <h4 class="mb-0">🛑 Shutdown ALFRED</h4>
                            </div>
                            <div class="card-body">
                                <p>Are you sure you want to shut down the ALFRED server?</p>
                                <form method="POST">
                                    <button type="submit" class="btn btn-danger">Yes, Shutdown</button>
                                    <a href="/" class="btn btn-secondary">Cancel</a>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    else:
        def shutdown_server():
            os.kill(os.getpid(), signal.SIGINT)
        
        threading.Timer(1.0, shutdown_server).start()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ALFRED Shutting Down</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h4 class="mb-0">👋 ALFRED Shutting Down</h4>
                            </div>
                            <div class="card-body text-center">
                                <p>The ALFRED server is shutting down...</p>
                                <p>You can close this browser window.</p>
                                <hr>
                                <p class="text-muted">Thank you for using ALFRED!</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

# Draft API Endpoints
@app.route('/api/draft/config')
def api_draft_config():
    """Get current draft configuration"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT draft_id, draft_name, num_teams, roster_positions, 
                   current_pick, rounds, is_active
            FROM draft_config
            WHERE is_active = TRUE
            LIMIT 1
        """)
        
        row = cur.fetchone()
        if row:
            config = {
                'draft_id': row[0],
                'draft_name': row[1],
                'num_teams': row[2],
                'roster_positions': row[3],
                'current_pick': row[4],
                'rounds': row[5],
                'is_active': row[6]
            }
        else:
            config = {'error': 'No active draft found'}
        
        cur.close()
        conn.close()
        return jsonify(config)
        
    except Exception as e:
        print(f"Error fetching draft config: {e}")
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/undrafted')
def api_undrafted_players():
    """Get undrafted players sorted by ADP"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Get ALL undrafted players
        cur.execute("""
            SELECT * FROM get_undrafted_players(%s)
        """, (draft_id,))
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'player_name': row[1],
                'player_position': row[2],
                'player_team': row[3],
                'avg_adp': float(row[4]) if row[4] else 999,
                'consensus_rank': row[5] if row[5] else 999
            })
        
        cur.close()
        conn.close()
        return jsonify(players)
        
    except Exception as e:
        print(f"Error fetching undrafted players: {e}")
        if conn:
            conn.close()
        return jsonify([])

@app.route('/api/draft/comprehensive-rankings')
def api_comprehensive_rankings():
    """Get comprehensive player rankings with ADP and position rankings"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Get all players with comprehensive ranking data
        cur.execute("""
            WITH player_adp AS (
                SELECT 
                    p.player_id,
                    p.name,
                    p.position,
                    p.team,
                    p.is_active,
                    p.rookie_year,
                    ROUND(AVG(ar.adp_value), 1) as avg_adp,
                    COUNT(ar.adp_value) as adp_sources
                FROM players p
                LEFT JOIN adp_rankings ar ON p.player_id = ar.player_id
                WHERE p.is_active = TRUE
                GROUP BY p.player_id, p.name, p.position, p.team, p.is_active, p.rookie_year
            ),
            deduplicated_rankings AS (
                SELECT DISTINCT
                    pr.player_id,
                    rs.source_name,
                    pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE pr.position_rank IS NOT NULL
            ),
            player_position_ranks AS (
                SELECT 
                    p.player_id,
                    ROUND(AVG(dr.position_rank::numeric), 1) as avg_position_rank,
                    COUNT(dr.source_name) as position_rank_sources
                FROM players p
                LEFT JOIN deduplicated_rankings dr ON p.player_id = dr.player_id
                WHERE p.is_active = TRUE
                GROUP BY p.player_id
            ),
            drafted_players AS (
                SELECT DISTINCT player_id 
                FROM draft_picks 
                WHERE draft_id = %s
            )
            SELECT 
                pa.player_id,
                pa.name,
                pa.position,
                pa.team,
                pa.avg_adp,
                pa.adp_sources,
                COALESCE(ppr.avg_position_rank, 999) as avg_position_rank,
                COALESCE(ppr.position_rank_sources, 0) as position_rank_sources,
                CASE WHEN dp.player_id IS NOT NULL THEN TRUE ELSE FALSE END as is_drafted,
                pa.rookie_year
            FROM player_adp pa
            LEFT JOIN player_position_ranks ppr ON pa.player_id = ppr.player_id
            LEFT JOIN drafted_players dp ON pa.player_id = dp.player_id
            ORDER BY 
                CASE 
                    WHEN pa.position = 'DST' AND pa.avg_adp IS NULL THEN COALESCE(ppr.avg_position_rank, 999)
                    ELSE COALESCE(pa.avg_adp, 999)
                END,
                pa.name
        """, (draft_id,))
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'avg_adp': float(row[4]) if row[4] else 999,
                'adp_sources': row[5] if row[5] else 0,
                'avg_position_rank': float(row[6]) if row[6] else 999,
                'position_rank_sources': row[7] if row[7] else 0,
                'is_drafted': row[8],
                'rookie_year': row[9] if row[9] else None
            })
        
        # Calculate ordinal rankings using the same method as rankings page
        # This ensures consistency between the rankings page and draft board
        
        # Convert ADP averages to ordinals (better ADP = lower number = higher ordinal position)
        players_with_adp = [p for p in players if p['avg_adp'] < 999]
        players_with_adp.sort(key=lambda x: x['avg_adp'])
        
        for i, player in enumerate(players_with_adp):
            player['overall_rank'] = i + 1
        
        # Set default overall rank for unranked players
        for player in players:
            if 'overall_rank' not in player:
                player['overall_rank'] = 999
        
        # Convert position rank averages to ordinals by position
        for position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            # Get players with position rankings for this position
            pos_players_with_ranks = [
                p for p in players 
                if p['position'] == position and p['avg_position_rank'] < 999
            ]
            # Sort by average position rank (lower is better)
            pos_players_with_ranks.sort(key=lambda x: x['avg_position_rank'])
            
            # Assign ordinal position ranks
            for i, player in enumerate(pos_players_with_ranks):
                player['position_rank'] = i + 1
        
        # Set default position rank for unranked players
        for player in players:
            if 'position_rank' not in player:
                player['position_rank'] = 999
                
        undrafted_players = [p for p in players if not p['is_drafted']]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'all_players': players,
            'undrafted_players': undrafted_players
        })
        
    except Exception as e:
        print(f"Error fetching player rankings: {e}")
        if conn:
            conn.close()
        return jsonify({'all_players': [], 'undrafted_players': []})

@app.route('/api/draft/pick', methods=['POST'])
def api_make_pick():
    """Record a draft pick"""
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Calculate round and pick in round
        pick_number = data.get('pick_number', 1)
        round_number = ((pick_number - 1) // 10) + 1
        pick_in_round = ((pick_number - 1) % 10) + 1
        
        # Insert the pick
        cur.execute("""
            INSERT INTO draft_picks 
            (draft_id, player_id, pick_number, round_number, pick_in_round, 
             team_number, roster_position)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            draft_id,
            data['player_id'],
            pick_number,
            round_number,
            pick_in_round,
            data['team_number'],
            data.get('roster_position', 'BENCH')
        ))
        
        # Update draft current pick
        cur.execute("""
            UPDATE draft_config 
            SET current_pick = current_pick + 1
            WHERE draft_id = %s
        """, (draft_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error making pick: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/history')
def api_draft_history():
    """Get draft pick history"""
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Get draft history
        cur.execute("""
            SELECT dp.pick_number, dp.team_number, dp.round_number,
                   p.name, p.position, p.team
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.draft_id = %s
            ORDER BY dp.pick_number DESC
        """, (draft_id,))
        
        picks = []
        for row in cur.fetchall():
            picks.append({
                'pick_number': row[0],
                'team_number': row[1],
                'round': row[2],
                'player_name': row[3],
                'position': row[4],
                'team': row[5]
            })
        
        cur.close()
        conn.close()
        return jsonify(picks)
        
    except Exception as e:
        print(f"Error fetching draft history: {e}")
        if conn:
            conn.close()
        return jsonify([])

@app.route('/api/draft/undo', methods=['POST'])
def api_undo_pick():
    """Undo the last draft pick"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Get the last pick info before deleting
        cur.execute("""
            SELECT dp.pick_number, dp.team_number, dp.roster_position, 
                   dp.player_id, p.name as player_name, p.position
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.draft_id = %s 
            AND dp.pick_number = (
                SELECT MAX(pick_number) 
                FROM draft_picks 
                WHERE draft_id = %s
            )
        """, (draft_id, draft_id))
        
        undone_pick = cur.fetchone()
        
        if undone_pick:
            # Delete the last pick
            cur.execute("""
                DELETE FROM draft_picks 
                WHERE draft_id = %s 
                AND pick_number = %s
            """, (draft_id, undone_pick[0]))
            
            # Update draft current pick
            cur.execute("""
                UPDATE draft_config 
                SET current_pick = GREATEST(1, current_pick - 1)
                WHERE draft_id = %s
            """, (draft_id,))
            
            conn.commit()
            
            # Return the undone pick data
            undone_pick_data = {
                'pick_number': undone_pick[0],
                'team_number': undone_pick[1],
                'roster_position': undone_pick[2],
                'player_id': undone_pick[3],
                'player_name': undone_pick[4],
                'position': undone_pick[5]
            }
            
            cur.close()
            conn.close()
            
            return jsonify({'success': True, 'undone_pick': undone_pick_data})
        else:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'No picks to undo'})
        
    except Exception as e:
        print(f"Error undoing pick: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/restart', methods=['POST'])
def api_restart_draft():
    """Restart the draft by clearing all picks"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        
        # Get active draft ID
        cur.execute("SELECT draft_id FROM draft_config WHERE is_active = TRUE LIMIT 1")
        draft_result = cur.fetchone()
        draft_id = draft_result[0] if draft_result else 1
        
        # Delete all picks for this draft
        cur.execute("DELETE FROM draft_picks WHERE draft_id = %s", (draft_id,))
        
        # Reset draft configuration
        cur.execute("""
            UPDATE draft_config 
            SET current_pick = 1, started_at = NULL, completed_at = NULL
            WHERE draft_id = %s
        """, (draft_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Draft restarted successfully'})
        
    except Exception as e:
        print(f"Error restarting draft: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🏈 ALFRED Clean - Master Player Index")
    print("=" * 50)
    
    # Test database connection
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed!")
        sys.exit(1)
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM players")
        total = cur.fetchone()[0]
        print(f"✅ Connected to database with {total} players")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    
    print("\n🌐 Starting server...")
    print("📍 Master Index: http://localhost:5555/")
    print("📊 Player Rankings: http://localhost:5555/rankings")
    print("🏈 Draft Board: http://localhost:5555/draft-board")
    print("🛑 Shutdown: http://localhost:5555/shutdown")
    print("\nPress Ctrl+C to stop")
    
    # Open browser
    webbrowser.open('http://localhost:5555/')
    
    try:
        app.run(host='127.0.0.1', port=5555, debug=False)
    except KeyboardInterrupt:
        print("\n👋 ALFRED shutting down...")