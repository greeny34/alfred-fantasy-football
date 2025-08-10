import React, { useState, useMemo } from 'react'

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

interface PlayerDetailViewProps {
  players: Player[]
  loading: boolean
}

interface DetailFilters {
  hasRankings: 'all' | 'ranked' | 'unranked'
  minRank: string
  maxRank: string
  sources: string[]
  sortBy: 'name' | 'position' | 'team' | 'rank' | 'sources'
  sortOrder: 'asc' | 'desc'
}

const PlayerDetailView: React.FC<PlayerDetailViewProps> = ({ players, loading }) => {
  const [filters, setFilters] = useState<DetailFilters>({
    hasRankings: 'all',
    minRank: '',
    maxRank: '',
    sources: [],
    sortBy: 'name',
    sortOrder: 'asc'
  })

  // Get all unique sources from the data
  const allSources = useMemo(() => {
    const sources = new Set<string>()
    players.forEach(player => {
      player.rankings.forEach(ranking => {
        sources.add(ranking.source)
      })
    })
    return Array.from(sources).sort()
  }, [players])

  // Filter and sort players based on current filters
  const filteredPlayers = useMemo(() => {
    let filtered = [...players]

    // Filter by ranking status
    if (filters.hasRankings === 'ranked') {
      filtered = filtered.filter(player => player.rankings.length > 0)
    } else if (filters.hasRankings === 'unranked') {  
      filtered = filtered.filter(player => player.rankings.length === 0)
    }

    // Filter by rank range
    if (filters.minRank || filters.maxRank) {
      filtered = filtered.filter(player => {
        if (player.rankings.length === 0) return false
        
        const bestRank = Math.min(...player.rankings.map(r => r.rank))
        const min = filters.minRank ? parseInt(filters.minRank) : 0
        const max = filters.maxRank ? parseInt(filters.maxRank) : 999
        
        return bestRank >= min && bestRank <= max
      })
    }

    // Filter by sources
    if (filters.sources.length > 0) {
      filtered = filtered.filter(player => {
        return player.rankings.some(ranking => 
          filters.sources.includes(ranking.source)
        )
      })
    }

    // Sort players
    filtered.sort((a, b) => {
      let comparison = 0
      
      switch (filters.sortBy) {
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
        case 'sources':
          comparison = b.rankings.length - a.rankings.length
          break
      }
      
      return filters.sortOrder === 'desc' ? -comparison : comparison
    })

    return filtered
  }, [players, filters])

  const handleFilterChange = (key: keyof DetailFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleSourceToggle = (source: string) => {
    setFilters(prev => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
    }))
  }

  const clearFilters = () => {
    setFilters({
      hasRankings: 'all',
      minRank: '',
      maxRank: '',
      sources: [],
      sortBy: 'name',
      sortOrder: 'asc'
    })
  }

  if (loading) {
    return (
      <div className="loading" style={{ padding: '60px' }}>
        🔄 Loading player details...
      </div>
    )
  }

  if (!players || players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#666' }}>
        <h3>📊 Player Detail View</h3>
        <p>Use the search form above to load players and see detailed analysis</p>
      </div>
    )
  }

  return (
    <div className="player-detail-view">
      <div style={{ marginBottom: '20px' }}>
        <h3>📊 Player Detail Analysis</h3>
        <p style={{ color: '#666', margin: '5px 0' }}>
          Comprehensive spreadsheet view with advanced filtering and sorting
        </p>
      </div>

      {/* Advanced Filters */}
      <div className="detail-filters" style={{ 
        background: '#f8f9fa', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '20px',
        border: '1px solid #e9ecef'
      }}>
        <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>🔍 Advanced Filters</h4>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          {/* Ranking Status Filter */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Ranking Status:</label>
            <select 
              value={filters.hasRankings}
              onChange={(e) => handleFilterChange('hasRankings', e.target.value)}
              style={{ width: '100%', padding: '6px' }}
            >
              <option value="all">All Players</option>
              <option value="ranked">Ranked Only</option>
              <option value="unranked">Unranked Only</option>
            </select>
          </div>

          {/* Rank Range */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Rank Range:</label>
            <div style={{ display: 'flex', gap: '5px' }}>
              <input 
                type="number" 
                placeholder="Min"
                value={filters.minRank}
                onChange={(e) => handleFilterChange('minRank', e.target.value)}
                style={{ width: '50%', padding: '6px' }}
              />
              <input 
                type="number" 
                placeholder="Max"
                value={filters.maxRank}
                onChange={(e) => handleFilterChange('maxRank', e.target.value)}
                style={{ width: '50%', padding: '6px' }}
              />
            </div>
          </div>

          {/* Sort Options */}
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Sort By:</label>
            <div style={{ display: 'flex', gap: '5px' }}>
              <select 
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                style={{ flex: 1, padding: '6px' }}
              >
                <option value="name">Name</option>
                <option value="position">Position</option>
                <option value="team">Team</option>
                <option value="rank">Best Rank</option>
                <option value="sources">Source Count</option>
              </select>
              <select 
                value={filters.sortOrder}
                onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                style={{ width: '80px', padding: '6px' }}
              >
                <option value="asc">↑ Asc</option>
                <option value="desc">↓ Desc</option>
              </select>
            </div>
          </div>

          {/* Clear Filters */}
          <div style={{ display: 'flex', alignItems: 'end' }}>
            <button 
              onClick={clearFilters}
              style={{ 
                padding: '8px 16px', 
                background: '#6c757d', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px', 
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Source Filters */}
        {allSources.length > 0 && (
          <div style={{ marginTop: '15px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
              Ranking Sources ({filters.sources.length} selected):
            </label>
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '8px',
              maxHeight: '100px',
              overflowY: 'auto',
              padding: '8px',
              background: 'white',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}>
              {allSources.map(source => (
                <label 
                  key={source} 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '4px', 
                    fontSize: '12px',
                    background: filters.sources.includes(source) ? '#e3f2fd' : 'transparent',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    cursor: 'pointer'
                  }}
                >
                  <input 
                    type="checkbox"
                    checked={filters.sources.includes(source)}
                    onChange={() => handleSourceToggle(source)}
                  />
                  {source}
                </label>
              ))}
            </div>
          </div>
        )}
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
        <span>
          <strong>Showing {filteredPlayers.length}</strong> of {players.length} players
        </span>
        <span style={{ fontSize: '12px', color: '#666' }}>
          Sorted by {filters.sortBy} ({filters.sortOrder === 'asc' ? 'ascending' : 'descending'})
        </span>
      </div>

      {/* Player Table */}
      <div style={{ overflowX: 'auto', border: '1px solid #ddd', borderRadius: '8px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
          <thead>
            <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: 'bold', fontSize: '14px' }}>Player</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold', fontSize: '14px' }}>Position</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold', fontSize: '14px' }}>Team</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold', fontSize: '14px' }}>Best Rank</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', fontWeight: 'bold', fontSize: '14px' }}>Sources</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', fontWeight: 'bold', fontSize: '14px' }}>All Rankings</th>
            </tr>
          </thead>
          <tbody>
            {filteredPlayers.map((player, index) => {
              const bestRank = player.rankings.length > 0 ? Math.min(...player.rankings.map(r => r.rank)) : null
              const status = player.rankings.length > 0 ? 'ranked' : 'unranked'
              
              return (
                <tr 
                  key={index} 
                  style={{ 
                    borderBottom: '1px solid #dee2e6',
                    background: index % 2 === 0 ? '#fff' : '#f8f9fa'
                  }}
                >
                  <td style={{ padding: '10px 8px' }}>
                    <div style={{ fontWeight: 'bold' }}>{player.name}</div>
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                      Status: <span style={{ 
                        color: status === 'ranked' ? '#28a745' : '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        {status === 'ranked' ? 'Ranked' : 'Unranked'}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                    <span className={`badge badge-primary`} style={{ 
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
                        background: getRankColor(bestRank), 
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontWeight: 'bold',
                        fontSize: '12px'
                      }}>
                        #{bestRank}
                      </span>
                    ) : (
                      <span style={{ color: '#999', fontSize: '12px' }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                    <span style={{ 
                      background: player.rankings.length > 0 ? '#17a2b8' : '#6c757d',
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: 'bold'
                    }}>
                      {player.rankings.length}
                    </span>
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
                                background: '#28a745',
                                color: 'white',
                                padding: '2px 6px',
                                borderRadius: '3px',
                                fontSize: '10px',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {ranking.source}: #{ranking.rank}
                            </span>
                          ))
                        }
                      </div>
                    ) : (
                      <span style={{ color: '#999', fontSize: '12px', fontStyle: 'italic' }}>
                        No rankings available
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {filteredPlayers.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '8px',
          border: '1px solid #e9ecef'
        }}>
          <h4>No players match your current filters</h4>
          <p>Try adjusting your filter criteria or clearing all filters</p>
        </div>
      )}
    </div>
  )
}

// Helper functions
const getPositionColor = (position: string): string => {
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

const getRankColor = (rank: number): string => {
  if (rank <= 12) return '#28a745' // Top tier - green
  if (rank <= 24) return '#ffc107' // Mid tier - yellow
  if (rank <= 50) return '#fd7e14' // Lower tier - orange
  return '#dc3545' // Deep tier - red
}

export default PlayerDetailView