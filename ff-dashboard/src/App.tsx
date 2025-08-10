import React, { useState, useEffect } from 'react'
import './App.css'

interface Player {
  name: string
  position: string
  team: string
  rankings: Ranking[]
}

interface Ranking {
  source: string
  rank: number
  date: string
}

interface Filters {
  search: string
  position: string
  team: string
}

type ViewMode = 'team' | 'position' | 'detail'

function App() {
  const [players, setPlayers] = useState<Player[]>([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState<ViewMode>('detail')
  const [filters, setFilters] = useState<Filters>({
    search: '',
    position: '',
    team: ''
  })
  const [teams, setTeams] = useState<string[]>([])
  const [stats, setStats] = useState({
    QB: 0, RB: 0, WR: 0, TE: 0, K: 0, DST: 0, totalTeams: 0
  })

  // Load initial data
  useEffect(() => {
    loadStats()
    loadTeams()
  }, [])

  const loadStats = async () => {
    try {
      setStats({ QB: 120, RB: 211, WR: 402, TE: 199, K: 46, DST: 32, totalTeams: 32 })
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadTeams = async () => {
    try {
      const mockTeams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
      ]
      setTeams(mockTeams)
    } catch (error) {
      console.error('Error loading teams:', error)
    }
  }

  const loadPlayers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.position) params.append('position', filters.position)
      if (filters.team) params.append('team', filters.team)

      const response = await fetch(`/api/players?${params}`)
      const data = await response.json()
      setPlayers(data)
    } catch (error) {
      console.error('Error loading players:', error)
      setPlayers([])
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearFilters = () => {
    setFilters({ search: '', position: '', team: '' })
    setPlayers([])
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    loadPlayers()
  }

  return (
    <div className="container">
      <header style={{ marginBottom: '30px' }}>
        <h1>🏈 Fantasy Football Data Explorer</h1>
        
        <div className="stats-summary" style={{ 
          display: 'flex', 
          gap: '20px', 
          background: '#f8f9fa', 
          padding: '16px', 
          borderRadius: '8px',
          marginTop: '16px'
        }}>
          <div><strong>QB:</strong> <span className="badge badge-secondary">{stats.QB}</span></div>
          <div><strong>RB:</strong> <span className="badge badge-secondary">{stats.RB}</span></div>
          <div><strong>WR:</strong> <span className="badge badge-secondary">{stats.WR}</span></div>
          <div><strong>TE:</strong> <span className="badge badge-secondary">{stats.TE}</span></div>
          <div><strong>K:</strong> <span className="badge badge-secondary">{stats.K}</span></div>
          <div><strong>DST:</strong> <span className="badge badge-secondary">{stats.DST}</span></div>
          <div><strong>Teams:</strong> <span className="badge badge-primary">{stats.totalTeams}</span></div>
        </div>
      </header>

      {/* View Mode Selection - Radio Buttons at Top */}
      <div style={{ 
        marginBottom: '30px',
        padding: '20px',
        background: '#ffffff',
        border: '2px solid #007bff',
        borderRadius: '10px',
        textAlign: 'center'
      }}>
        <h3 style={{ marginBottom: '15px', color: '#007bff' }}>📊 Select View Mode</h3>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center',
          gap: '30px',
          flexWrap: 'wrap'
        }}>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '18px', 
            fontWeight: 'bold', 
            cursor: 'pointer',
            padding: '10px 15px',
            borderRadius: '8px',
            background: viewMode === 'team' ? '#e3f2fd' : 'transparent'
          }}>
            <input 
              type="radio" 
              value="team" 
              checked={viewMode === 'team'} 
              onChange={(e) => setViewMode(e.target.value as ViewMode)}
              style={{ transform: 'scale(1.5)' }}
            />
            🏟️ Team View
          </label>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '18px', 
            fontWeight: 'bold', 
            cursor: 'pointer',
            padding: '10px 15px',
            borderRadius: '8px',
            background: viewMode === 'position' ? '#e3f2fd' : 'transparent'
          }}>
            <input 
              type="radio" 
              value="position" 
              checked={viewMode === 'position'} 
              onChange={(e) => setViewMode(e.target.value as ViewMode)}
              style={{ transform: 'scale(1.5)' }}
            />
            🎯 Position View
          </label>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            fontSize: '18px', 
            fontWeight: 'bold', 
            cursor: 'pointer',
            padding: '10px 15px',
            borderRadius: '8px',
            background: viewMode === 'detail' ? '#e3f2fd' : 'transparent'
          }}>
            <input 
              type="radio" 
              value="detail" 
              checked={viewMode === 'detail'} 
              onChange={(e) => setViewMode(e.target.value as ViewMode)}
              style={{ transform: 'scale(1.5)' }}
            />
            📋 Player Detail
          </label>
        </div>
      </div>

      {/* Dynamic Filters Based on View Mode */}
      <div className="search-controls">
        <h3>🔍 {getFilterTitle(viewMode)}</h3>
        
        <form onSubmit={handleSearch}>
          <div className="filters">
            {/* Always show player name search */}
            <div className="filter-group">
              <label>Player Name:</label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Type player name..."
                style={{ minWidth: '200px' }}
              />
            </div>

            {/* Show position filter for team view and detail view */}
            {(viewMode === 'team' || viewMode === 'detail') && (
              <div className="filter-group">
                <label>Position:</label>
                <select
                  value={filters.position}
                  onChange={(e) => handleFilterChange('position', e.target.value)}
                >
                  <option value="">All Positions</option>
                  <option value="QB">QB</option>
                  <option value="RB">RB</option>
                  <option value="WR">WR</option>
                  <option value="TE">TE</option>
                  <option value="K">K</option>
                  <option value="DST">DST</option>
                </select>
              </div>
            )}

            {/* Show team filter for position view and detail view */}
            {(viewMode === 'position' || viewMode === 'detail') && (
              <div className="filter-group">
                <label>Team:</label>
                <select
                  value={filters.team}
                  onChange={(e) => handleFilterChange('team', e.target.value)}
                >
                  <option value="">All Teams</option>
                  {teams.map(team => (
                    <option key={team} value={team}>{team}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="filter-group">
              <button type="submit" className="btn btn-primary">
                Load Data
              </button>
            </div>

            <div className="filter-group">
              <button type="button" className="btn btn-secondary" onClick={clearFilters}>
                Clear
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Results Section */}
      <div className="results-section">
        {viewMode === 'team' ? (
          <TeamView players={players} loading={loading} />
        ) : viewMode === 'position' ? (
          <PositionView players={players} loading={loading} />
        ) : (
          <PlayerDetailView players={players} loading={loading} />
        )}
      </div>
    </div>
  )
}

// Helper function to get filter title
function getFilterTitle(viewMode: ViewMode): string {
  switch (viewMode) {
    case 'team': return 'Team View Filters'
    case 'position': return 'Position View Filters'
    case 'detail': return 'Player Detail Filters'
  }
}

// Team Tree View Component
function TeamView({ players, loading }: { players: Player[], loading: boolean }) {
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set())
  const [expandedPositions, setExpandedPositions] = useState<Set<string>>(new Set())

  if (loading) {
    return <div className="loading">🔄 Loading team data...</div>
  }

  if (players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#666' }}>
        <h3>🏟️ Team Tree View</h3>
        <p>Use the filters above to load team data</p>
      </div>
    )
  }

  // Team to division mapping
  const teamToDivision = {
    'BAL': 'AFC North', 'CIN': 'AFC North', 'CLE': 'AFC North', 'PIT': 'AFC North',
    'HOU': 'AFC South', 'IND': 'AFC South', 'JAX': 'AFC South', 'TEN': 'AFC South',
    'BUF': 'AFC East', 'MIA': 'AFC East', 'NE': 'AFC East', 'NYJ': 'AFC East',
    'DEN': 'AFC West', 'KC': 'AFC West', 'LV': 'AFC West', 'LAC': 'AFC West',
    'CHI': 'NFC North', 'DET': 'NFC North', 'GB': 'NFC North', 'MIN': 'NFC North',
    'ATL': 'NFC South', 'CAR': 'NFC South', 'NO': 'NFC South', 'TB': 'NFC South',
    'DAL': 'NFC East', 'NYG': 'NFC East', 'PHI': 'NFC East', 'WAS': 'NFC East',
    'ARI': 'NFC West', 'LAR': 'NFC West', 'SF': 'NFC West', 'SEA': 'NFC West'
  } as Record<string, string>

  // Group players by team, then by position
  const teamGroups = players.reduce((groups, player) => {
    const team = player.team || 'Unknown'
    const division = teamToDivision[team] || 'Unknown'
    
    if (!groups[division]) groups[division] = {}
    if (!groups[division][team]) groups[division][team] = {}
    
    const position = player.position || 'Unknown'
    if (!groups[division][team][position]) groups[division][team][position] = []
    groups[division][team][position].push(player)
    
    return groups
  }, {} as Record<string, Record<string, Record<string, Player[]>>>)

  const toggleTeam = (team: string) => {
    const newExpanded = new Set(expandedTeams)
    if (newExpanded.has(team)) {
      newExpanded.delete(team)
    } else {
      newExpanded.add(team)
    }
    setExpandedTeams(newExpanded)
  }

  const togglePosition = (key: string) => {
    const newExpanded = new Set(expandedPositions)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedPositions(newExpanded)
  }

  const divisionOrder = ['AFC North', 'AFC South', 'AFC East', 'AFC West', 'NFC North', 'NFC South', 'NFC East', 'NFC West']
  
  return (
    <div>
      <h3>🏟️ Team Tree View - {players.length} Players</h3>
      <div style={{ background: '#f8f9fa', border: '1px solid #dee2e6', borderRadius: '8px' }}>
        {divisionOrder
          .filter(division => teamGroups[division])
          .map(division => (
            <div key={division}>
              {/* Division Header */}
              <div style={{ 
                background: '#e9ecef', 
                padding: '10px 15px', 
                borderBottom: '1px solid #dee2e6',
                fontWeight: 'bold',
                color: '#495057'
              }}>
                {division}
              </div>
              
              {/* Teams in Division */}
              {Object.entries(teamGroups[division])
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([team, positions]) => {
                  const teamPlayerCount = Object.values(positions).flat().length
                  const isTeamExpanded = expandedTeams.has(team)
                  
                  return (
                    <div key={team}>
                      {/* Team Row */}
                      <div 
                        onClick={() => toggleTeam(team)}
                        style={{ 
                          padding: '12px 30px', 
                          borderBottom: '1px solid #f1f3f4',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          background: isTeamExpanded ? '#fff3cd' : 'white',
                          ':hover': { background: '#f8f9fa' }
                        }}
                      >
                        <span style={{ fontSize: '14px' }}>
                          {isTeamExpanded ? '▼' : '▶'}
                        </span>
                        <strong style={{ color: '#007bff' }}>
                          {team} ({teamPlayerCount})
                        </strong>
                      </div>
                      
                      {/* Positions (when team expanded) */}
                      {isTeamExpanded && (
                        <div style={{ background: '#f8f9fa' }}>
                          {Object.entries(positions)
                            .sort((a, b) => a[0].localeCompare(b[0]))
                            .map(([position, positionPlayers]) => {
                              const positionKey = `${team}-${position}`
                              const isPositionExpanded = expandedPositions.has(positionKey)
                              
                              return (
                                <div key={position}>
                                  {/* Position Row */}
                                  <div 
                                    onClick={() => togglePosition(positionKey)}
                                    style={{ 
                                      padding: '10px 60px', 
                                      borderBottom: '1px solid #f1f3f4',
                                      cursor: 'pointer',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '10px',
                                      background: isPositionExpanded ? '#d1ecf1' : 'white'
                                    }}
                                  >
                                    <span style={{ fontSize: '12px' }}>
                                      {isPositionExpanded ? '▼' : '▶'}
                                    </span>
                                    <span style={{ 
                                      backgroundColor: getPositionColor(position),
                                      color: 'white',
                                      padding: '3px 8px',
                                      borderRadius: '4px',
                                      fontSize: '12px',
                                      fontWeight: 'bold'
                                    }}>
                                      {position} ({positionPlayers.length})
                                    </span>
                                  </div>
                                  
                                  {/* Players (when position expanded) */}
                                  {isPositionExpanded && (
                                    <div style={{ background: '#ffffff', padding: '10px 90px' }}>
                                      {positionPlayers
                                        .sort((a, b) => {
                                          const aRank = a.rankings.length > 0 ? Math.min(...a.rankings.map(r => r.rank)) : 999
                                          const bRank = b.rankings.length > 0 ? Math.min(...b.rankings.map(r => r.rank)) : 999
                                          return aRank - bRank
                                        })
                                        .map((player, idx) => (
                                          <div key={idx} style={{ 
                                            padding: '8px 12px',
                                            margin: '4px 0',
                                            background: '#f8f9fa',
                                            border: '1px solid #e9ecef',
                                            borderRadius: '4px',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center'
                                          }}>
                                            <div>
                                              <strong>{player.name}</strong>
                                              {player.rankings.length > 0 && (
                                                <span style={{ color: '#28a745', marginLeft: '8px' }}>✓ Ranked</span>
                                              )}
                                            </div>
                                            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                              {player.rankings
                                                .sort((a, b) => a.rank - b.rank)
                                                .slice(0, 3)
                                                .map((ranking, ridx) => (
                                                  <span key={ridx} style={{ 
                                                    background: '#17a2b8',
                                                    color: 'white',
                                                    padding: '2px 6px',
                                                    borderRadius: '3px',
                                                    fontSize: '10px'
                                                  }}>
                                                    {ranking.source}: #{ranking.rank}
                                                  </span>
                                                ))
                                              }
                                            </div>
                                          </div>
                                        ))
                                      }
                                    </div>
                                  )}
                                </div>
                              )
                            })
                          }
                        </div>
                      )}
                    </div>
                  )
                })
              }
            </div>
          ))
        }
      </div>
    </div>
  )
}

// Position Tree View Component
function PositionView({ players, loading }: { players: Player[], loading: boolean }) {
  const [expandedPositions, setExpandedPositions] = useState<Set<string>>(new Set())
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set())

  if (loading) {
    return <div className="loading">🔄 Loading position data...</div>
  }

  if (players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#666' }}>
        <h3>🎯 Position Tree View</h3>
        <p>Use the filters above to load position data</p>
      </div>
    )
  }

  // Group players by position, then by team
  const positionGroups = players.reduce((groups, player) => {
    const position = player.position || 'Unknown'
    const team = player.team || 'Unknown'
    
    if (!groups[position]) groups[position] = {}
    if (!groups[position][team]) groups[position][team] = []
    groups[position][team].push(player)
    
    return groups
  }, {} as Record<string, Record<string, Player[]>>)

  const togglePosition = (position: string) => {
    const newExpanded = new Set(expandedPositions)
    if (newExpanded.has(position)) {
      newExpanded.delete(position)
    } else {
      newExpanded.add(position)
    }
    setExpandedPositions(newExpanded)
  }

  const toggleTeam = (key: string) => {
    const newExpanded = new Set(expandedTeams)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedTeams(newExpanded)
  }

  const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
  
  return (
    <div>
      <h3>🎯 Position Tree View - {players.length} Players</h3>
      <div style={{ background: '#f8f9fa', border: '1px solid #dee2e6', borderRadius: '8px' }}>
        {positionOrder
          .filter(position => positionGroups[position])
          .map(position => {
            const teams = positionGroups[position]
            const positionPlayerCount = Object.values(teams).flat().length
            const isPositionExpanded = expandedPositions.has(position)
            
            return (
              <div key={position}>
                {/* Position Row */}
                <div 
                  onClick={() => togglePosition(position)}
                  style={{ 
                    padding: '15px 20px', 
                    borderBottom: '1px solid #dee2e6',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    background: isPositionExpanded ? '#fff3cd' : 'white',
                    ':hover': { background: '#f8f9fa' }
                  }}
                >
                  <span style={{ fontSize: '16px' }}>
                    {isPositionExpanded ? '▼' : '▶'}
                  </span>
                  <span style={{ 
                    backgroundColor: getPositionColor(position),
                    color: 'white',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}>
                    {position} ({positionPlayerCount})
                  </span>
                </div>
                
                {/* Teams (when position expanded) */}
                {isPositionExpanded && (
                  <div style={{ background: '#f8f9fa' }}>
                    {Object.entries(teams)
                      .sort((a, b) => a[0].localeCompare(b[0]))
                      .map(([team, teamPlayers]) => {
                        const teamKey = `${position}-${team}`
                        const isTeamExpanded = expandedTeams.has(teamKey)
                        
                        return (
                          <div key={team}>
                            {/* Team Row */}
                            <div 
                              onClick={() => toggleTeam(teamKey)}
                              style={{ 
                                padding: '12px 50px', 
                                borderBottom: '1px solid #f1f3f4',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                background: isTeamExpanded ? '#d1ecf1' : 'white'
                              }}
                            >
                              <span style={{ fontSize: '14px' }}>
                                {isTeamExpanded ? '▼' : '▶'}
                              </span>
                              <strong style={{ color: '#007bff' }}>
                                {team} ({teamPlayers.length})
                              </strong>
                            </div>
                            
                            {/* Players (when team expanded) */}
                            {isTeamExpanded && (
                              <div style={{ background: '#ffffff', padding: '10px 80px' }}>
                                {teamPlayers
                                  .sort((a, b) => {
                                    const aRank = a.rankings.length > 0 ? Math.min(...a.rankings.map(r => r.rank)) : 999
                                    const bRank = b.rankings.length > 0 ? Math.min(...b.rankings.map(r => r.rank)) : 999
                                    return aRank - bRank
                                  })
                                  .map((player, idx) => (
                                    <div key={idx} style={{ 
                                      padding: '8px 12px',
                                      margin: '4px 0',
                                      background: '#f8f9fa',
                                      border: '1px solid #e9ecef',
                                      borderRadius: '4px',
                                      display: 'flex',
                                      justifyContent: 'space-between',
                                      alignItems: 'center'
                                    }}>
                                      <div>
                                        <strong>{player.name}</strong>
                                        {player.rankings.length > 0 && (
                                          <span style={{ color: '#28a745', marginLeft: '8px' }}>✓ Ranked</span>
                                        )}
                                      </div>
                                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                        {player.rankings
                                          .sort((a, b) => a.rank - b.rank)
                                          .slice(0, 3)
                                          .map((ranking, ridx) => (
                                            <span key={ridx} style={{ 
                                              background: '#17a2b8',
                                              color: 'white',
                                              padding: '2px 6px',
                                              borderRadius: '3px',
                                              fontSize: '10px'
                                            }}>
                                              {ranking.source}: #{ranking.rank}
                                            </span>
                                          ))
                                        }
                                      </div>
                                    </div>
                                  ))
                                }
                              </div>
                            )}
                          </div>
                        )
                      })
                    }
                  </div>
                )}
              </div>
            )
          })
        }
      </div>
    </div>
  )
}

// Comprehensive Player Detail View
function PlayerDetailView({ players, loading }: { players: Player[], loading: boolean }) {
  const [detailFilters, setDetailFilters] = useState({
    hasRankings: 'all' as 'all' | 'ranked' | 'unranked',
    minRank: '',
    maxRank: '',
    sortBy: 'name' as 'name' | 'position' | 'team' | 'rank',
    sortOrder: 'asc' as 'asc' | 'desc'
  })

  if (loading) {
    return <div className="loading">🔄 Loading player details...</div>
  }

  if (players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#666' }}>
        <h3>📋 Player Detail View</h3>
        <p>Use the filters above to load player data for detailed analysis</p>
      </div>
    )
  }

  // Apply detail filters
  let filteredPlayers = [...players]

  if (detailFilters.hasRankings === 'ranked') {
    filteredPlayers = filteredPlayers.filter(p => p.rankings.length > 0)
  } else if (detailFilters.hasRankings === 'unranked') {
    filteredPlayers = filteredPlayers.filter(p => p.rankings.length === 0)
  }

  if (detailFilters.minRank || detailFilters.maxRank) {
    filteredPlayers = filteredPlayers.filter(player => {
      if (player.rankings.length === 0) return false
      const bestRank = Math.min(...player.rankings.map(r => r.rank))
      const min = detailFilters.minRank ? parseInt(detailFilters.minRank) : 0
      const max = detailFilters.maxRank ? parseInt(detailFilters.maxRank) : 999
      return bestRank >= min && bestRank <= max
    })
  }

  // Sort players
  filteredPlayers.sort((a, b) => {
    let comparison = 0
    
    switch (detailFilters.sortBy) {
      case 'name':
        comparison = a.name.localeCompare(b.name)
        break
      case 'position':
        comparison = a.position.localeCompare(b.position)
        break
      case 'team':
        comparison = a.team.localeCompare(b.team)
        break
      case 'rank':
        const aRank = a.rankings.length > 0 ? Math.min(...a.rankings.map(r => r.rank)) : 999
        const bRank = b.rankings.length > 0 ? Math.min(...b.rankings.map(r => r.rank)) : 999
        comparison = aRank - bRank
        break
    }
    
    return detailFilters.sortOrder === 'desc' ? -comparison : comparison
  })

  return (
    <div>
      <h3>📋 Player Detail View</h3>
      
      {/* Detail Filters */}
      <div style={{ 
        background: '#f8f9fa', 
        padding: '15px', 
        borderRadius: '8px', 
        marginBottom: '20px',
        border: '1px solid #e9ecef'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>Advanced Filters</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Ranking Status:</label>
            <select 
              value={detailFilters.hasRankings}
              onChange={(e) => setDetailFilters(prev => ({ ...prev, hasRankings: e.target.value as 'all' | 'ranked' | 'unranked' }))}
              style={{ width: '100%', padding: '6px' }}
            >
              <option value="all">All Players</option>
              <option value="ranked">Ranked Only</option>
              <option value="unranked">Unranked Only</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Rank Range:</label>
            <div style={{ display: 'flex', gap: '5px' }}>
              <input 
                type="number" 
                placeholder="Min"
                value={detailFilters.minRank}
                onChange={(e) => setDetailFilters(prev => ({ ...prev, minRank: e.target.value }))}
                style={{ width: '50%', padding: '6px' }}
              />
              <input 
                type="number" 
                placeholder="Max"
                value={detailFilters.maxRank}
                onChange={(e) => setDetailFilters(prev => ({ ...prev, maxRank: e.target.value }))}
                style={{ width: '50%', padding: '6px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Sort By:</label>
            <div style={{ display: 'flex', gap: '5px' }}>
              <select 
                value={detailFilters.sortBy}
                onChange={(e) => setDetailFilters(prev => ({ ...prev, sortBy: e.target.value as 'name' | 'position' | 'team' | 'rank' }))}
                style={{ flex: 1, padding: '6px' }}
              >
                <option value="name">Name</option>
                <option value="position">Position</option>
                <option value="team">Team</option>
                <option value="rank">Best Rank</option>
              </select>
              <select 
                value={detailFilters.sortOrder}
                onChange={(e) => setDetailFilters(prev => ({ ...prev, sortOrder: e.target.value as 'asc' | 'desc' }))}
                style={{ width: '80px', padding: '6px' }}
              >
                <option value="asc">↑ Asc</option>
                <option value="desc">↓ Desc</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div style={{ 
        marginBottom: '15px', 
        padding: '10px', 
        background: '#e9ecef', 
        borderRadius: '4px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span><strong>Showing {filteredPlayers.length}</strong> of {players.length} players</span>
      </div>

      {/* Player Table */}
      <div style={{ overflowX: 'auto', border: '1px solid #ddd', borderRadius: '8px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: 'bold' }}>Player</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold' }}>Position</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold' }}>Team</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold' }}>Best Rank</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: 'bold' }}>All Rankings</th>
            </tr>
          </thead>
          <tbody>
            {filteredPlayers.map((player, index) => {
              const bestRank = player.rankings.length > 0 ? Math.min(...player.rankings.map(r => r.rank)) : null
              
              return (
                <tr key={index} style={{ 
                  borderBottom: '1px solid #dee2e6',
                  background: index % 2 === 0 ? '#fff' : '#f8f9fa'
                }}>
                  <td style={{ padding: '10px 8px', fontWeight: 'bold' }}>{player.name}</td>
                  <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                    <span style={{ 
                      backgroundColor: getPositionColor(player.position),
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '11px'
                    }}>
                      {player.position}
                    </span>
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'center', fontWeight: 'bold' }}>
                    {player.team}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                    {bestRank ? (
                      <span style={{ 
                        background: '#28a745', 
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontWeight: 'bold'
                      }}>
                        #{bestRank}
                      </span>
                    ) : (
                      <span style={{ color: '#999' }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 8px' }}>
                    {player.rankings.length > 0 ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {player.rankings
                          .sort((a, b) => a.rank - b.rank)
                          .map((ranking, idx) => (
                            <span 
                              key={idx}
                              style={{ 
                                background: '#17a2b8',
                                color: 'white',
                                padding: '2px 6px',
                                borderRadius: '3px',
                                fontSize: '10px'
                              }}
                            >
                              {ranking.source}: #{ranking.rank}
                            </span>
                          ))
                        }
                      </div>
                    ) : (
                      <span style={{ color: '#999', fontStyle: 'italic' }}>No rankings</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Helper function
function getPositionColor(position: string): string {
  switch (position) {
    case 'QB': return '#dc3545'
    case 'RB': return '#28a745'
    case 'WR': return '#007bff'
    case 'TE': return '#ffc107'
    case 'K': return '#6f42c1'
    case 'DST': return '#20c997'
    default: return '#6c757d'
  }
}

export default App