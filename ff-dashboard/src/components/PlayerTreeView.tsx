import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

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

interface TreeNode {
  name: string
  children?: TreeNode[]
  _children?: TreeNode[] // Hidden children for collapse functionality
  data?: Player
  type: 'root' | 'position' | 'division' | 'team' | 'status' | 'player'
}

interface PlayerTreeViewProps {
  players: Player[]
  loading: boolean
  viewMode: 'position' | 'team'
}

type TreeViewMode = 'position' | 'team'

// Helper functions moved outside component to prevent recreation
const groupBy = <T,>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const group = (item[key] as string) || 'Unknown'
    groups[group] = groups[group] || []
    groups[group].push(item)
    return groups
  }, {} as Record<string, T[]>)
}

const groupByDivision = (players: Player[]): Record<string, Player[]> => {
  const teamToDivision: Record<string, string> = {
    'BAL': 'AFC North', 'CIN': 'AFC North', 'CLE': 'AFC North', 'PIT': 'AFC North',
    'HOU': 'AFC South', 'IND': 'AFC South', 'JAX': 'AFC South', 'TEN': 'AFC South',
    'BUF': 'AFC East', 'MIA': 'AFC East', 'NE': 'AFC East', 'NYJ': 'AFC East',
    'DEN': 'AFC West', 'KC': 'AFC West', 'LV': 'AFC West', 'LAC': 'AFC West',
    'CHI': 'NFC North', 'DET': 'NFC North', 'GB': 'NFC North', 'MIN': 'NFC North',
    'ATL': 'NFC South', 'CAR': 'NFC South', 'NO': 'NFC South', 'TB': 'NFC South',
    'DAL': 'NFC East', 'NYG': 'NFC East', 'PHI': 'NFC East', 'WAS': 'NFC East',
    'ARI': 'NFC West', 'LAR': 'NFC West', 'SF': 'NFC West', 'SEA': 'NFC West'
  }

  return players.reduce((groups, player) => {
    const division = teamToDivision[player.team] || 'Unknown'
    groups[division] = groups[division] || []
    groups[division].push(player)
    return groups
  }, {} as Record<string, Player[]>)
}

const groupByStatus = (players: Player[]): Record<string, Player[]> => {
  return players.reduce((groups, player) => {
    // Players with rankings are considered "Active"
    // Players without rankings are "Inactive" (less likely to be fantasy relevant)
    const status = player.rankings.length > 0 ? 'Active' : 'Inactive'
    groups[status] = groups[status] || []
    groups[status].push(player)
    return groups
  }, {} as Record<string, Player[]>)
}

const PlayerTreeView: React.FC<PlayerTreeViewProps> = ({ players, loading, viewMode }) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  // Update dimensions based on container size
  useEffect(() => {
    const updateDimensions = () => {
      const container = containerRef.current
      if (container) {
        const rect = container.getBoundingClientRect()
        // Use actual container width but constrain to fit viewport
        const containerWidth = rect.width > 0 ? rect.width : container.clientWidth
        const containerHeight = rect.height > 0 ? rect.height : container.clientHeight
        
        const newWidth = Math.max(containerWidth - 10, 600)
        const newHeight = Math.max(containerHeight - 10, 600)
        
        // Only update if dimensions actually changed
        setDimensions(prev => {
          if (prev.width !== newWidth || prev.height !== newHeight) {
            return { width: newWidth, height: newHeight }
          }
          return prev
        })
      }
    }

    updateDimensions()
    
    const resizeHandler = () => {
      setTimeout(updateDimensions, 100) // Debounce resize
    }
    
    window.addEventListener('resize', resizeHandler)
    
    return () => window.removeEventListener('resize', resizeHandler)
  }, []) // Remove players dependency to prevent loop

  // Initial dimension setup after container is mounted
  useEffect(() => {
    const timer = setTimeout(() => {
      const container = containerRef.current
      if (container && dimensions.width === 0) {
        const containerWidth = container.clientWidth || 800
        const containerHeight = container.clientHeight || 600
        
        setDimensions({
          width: Math.max(containerWidth - 10, 600),
          height: Math.max(containerHeight - 10, 600)
        })
      }
    }, 300) // Give more time for container to be ready

    return () => clearTimeout(timer)
  }, [dimensions.width]) // Only run when width is 0

  useEffect(() => {
    if (!players || players.length === 0 || loading || dimensions.width === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove() // Clear previous render

    // Create hierarchical data structure based on view mode
    const treeData = React.useMemo(() => {
      return viewMode === 'position' ? buildPositionTreeData(players) : buildTeamTreeData(players)
    }, [players, viewMode])
    
    // Set up D3 tree layout with balanced margins
    const margin = { top: 50, right: 120, bottom: 50, left: 100 } // Balanced margins
    const width = Math.max(dimensions.width - margin.left - margin.right, 500)
    const height = Math.max(dimensions.height - margin.top - margin.bottom, 400)

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`)

    const tree = d3.tree<TreeNode>()
      .size([height, width])
      .separation((a, b) => {
        // Tighter spacing to fit in container
        if (a.parent === b.parent) {
          if (a.data.type === 'player') return 0.6
          if (a.data.type === 'team') return 0.8
          return 1.0
        }
        return 1.5 / (a.depth + 1)
      })

    let root = d3.hierarchy(treeData)
    
    // Initialize collapse state based on view mode
    root.descendants().forEach((d: any) => {
      if (viewMode === 'position' && d.data.type === 'position') {
        d._children = d.children
        d.children = null
      } else if (viewMode === 'team' && d.data.type === 'team') {
        d._children = d.children
        d.children = null
      }
    })

    function update(source: any) {
      // Compute the new tree layout
      const treeRoot = tree(root)
      const nodes = treeRoot.descendants()
      const links = treeRoot.links()

      // Update nodes
      const node = g.selectAll<SVGGElement, any>("g.node")
        .data(nodes, (d: any) => d.id || (d.id = ++nodeId))

      // Enter new nodes
      const nodeEnter = node.enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${source.y0 || 0},${source.x0 || 0})`)
        .style("opacity", 0)

      // Add circles (skip empty root node)
      nodeEnter.filter(d => d.data.name !== "")
        .append("circle")
        .attr("r", d => getNodeRadius(d.data.type))
        .style("fill", d => getNodeColor(d.data))
        .style("stroke", "#333")
        .style("stroke-width", "2px")
        .style("cursor", d => d.data.type !== 'player' ? "pointer" : "default")
        .on("click", clicked)

      // Add text labels (skip empty root node)
      nodeEnter.filter(d => d.data.name !== "")
        .append("text")
        .attr("dy", ".35em")
        .attr("x", d => {
          const hasChildren = d.children || d._children
          if (d.data.type === 'position') return hasChildren ? -20 : 20
          if (d.data.type === 'team') return hasChildren ? -18 : 18
          return hasChildren ? -15 : 15
        })
        .style("text-anchor", d => {
          const hasChildren = d.children || d._children
          return hasChildren ? "end" : "start"
        })
        .style("font-size", d => getFontSize(d.data.type))
        .style("font-weight", d => d.data.type === 'player' ? 'normal' : 'bold')
        .style("cursor", d => d.data.type !== 'player' ? "pointer" : "default")
        .style("fill", d => d.data.type === 'player' ? '#333' : '#000')
        .text(d => truncateText(d.data.name, d.data.type))
        .on("click", clicked)

      // Add tooltips for players
      nodeEnter.filter(d => d.data.type === 'player')
        .append("title")
        .text(d => {
          const player = d.data.data!
          const rankings = player.rankings.length > 0 
            ? player.rankings.map(r => `${r.source}: ${player.position}${r.rank}`).join(', ')
            : 'No rankings'
          return `${player.name} (${player.position}) - ${player.team}\n${rankings}`
        })

      // Transition nodes to their new position
      const nodeUpdate = nodeEnter.merge(node)
      nodeUpdate.transition()
        .duration(750)
        .attr("transform", d => `translate(${d.y},${d.x})`)
        .style("opacity", 1)

      // Update circle fill for collapsed/expanded state
      nodeUpdate.select("circle")
        .style("fill", d => {
          if (d._children) return "#lightsteelblue" // Collapsed node
          return getNodeColor(d.data)
        })

      // Remove exiting nodes
      const nodeExit = node.exit().transition()
        .duration(750)
        .attr("transform", d => `translate(${source.y},${source.x})`)
        .style("opacity", 0)
        .remove()

      // Update links
      const link = g.selectAll<SVGPathElement, any>("path.link")
        .data(links, (d: any) => d.target.id)

      const linkEnter = link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", d => {
          const o = { x: source.x0 || 0, y: source.y0 || 0 }
          return diagonal(o, o)
        })
        .style("fill", "none")
        .style("stroke", "#ccc")
        .style("stroke-width", "2px")

      const linkUpdate = linkEnter.merge(link)
      linkUpdate.transition()
        .duration(750)
        .attr("d", d => diagonal(d.source, d.target))

      link.exit().transition()
        .duration(750)
        .attr("d", d => {
          const o = { x: source.x, y: source.y }
          return diagonal(o, o)
        })
        .remove()

      // Store the old positions for transition
      nodes.forEach((d: any) => {
        d.x0 = d.x
        d.y0 = d.y
      })
    }

    // Click handler for collapse/expand
    function clicked(event: any, d: any) {
      if (d.data.type === 'player') return // Don't collapse players
      
      if (d.children) {
        d._children = d.children
        d.children = null
      } else {
        d.children = d._children
        d._children = null
      }
      update(d)
    }

    // Diagonal path generator
    function diagonal(s: any, d: any) {
      return `M ${s.y} ${s.x}
              C ${(s.y + d.y) / 2} ${s.x},
                ${(s.y + d.y) / 2} ${d.x},
                ${d.y} ${d.x}`
    }

    let nodeId = 0

    // Initial render
    update(root)

  }, [players, loading, dimensions, viewMode])

  const buildPositionTreeData = (players: Player[]): TreeNode => {
    // Position → Division → Team → Player hierarchy
    const root: TreeNode = {
      name: "",
      type: 'root',
      children: []
    }

    // Group by position first
    const positionGroups = groupBy(players, 'position')
    
    Object.entries(positionGroups).forEach(([position, positionPlayers]) => {
      const positionNode: TreeNode = {
        name: `${position} (${positionPlayers.length})`,
        type: 'position',
        children: []
      }

      // Group by division within position
      const divisionGroups = groupByDivision(positionPlayers)
      
      Object.entries(divisionGroups).forEach(([division, divisionPlayers]) => {
        const divisionNode: TreeNode = {
          name: `${division} (${divisionPlayers.length})`,
          type: 'division',
          children: []
        }

        // Group by team within division
        const teamGroups = groupBy(divisionPlayers, 'team')
        
        Object.entries(teamGroups).forEach(([team, teamPlayers]) => {
          const teamNode: TreeNode = {
            name: `${team} (${teamPlayers.length})`,
            type: 'team',
            children: []
          }

          // Add individual players
          teamPlayers.forEach(player => {
            const rankText = player.rankings.length > 0 
              ? ` - #${player.rankings[0].rank}` 
              : ''
            
            teamNode.children!.push({
              name: `${player.name}${rankText}`,
              type: 'player',
              data: player
            })
          })

          // Sort players by ranking
          teamNode.children!.sort((a, b) => {
            const aRank = a.data?.rankings[0]?.rank || 999
            const bRank = b.data?.rankings[0]?.rank || 999
            return aRank - bRank
          })

          divisionNode.children!.push(teamNode)
        })

        // Sort teams alphabetically
        divisionNode.children!.sort((a, b) => a.name.localeCompare(b.name))
        positionNode.children!.push(divisionNode)
      })

      // Sort divisions
      const divisionOrder = ['AFC North', 'AFC South', 'AFC East', 'AFC West', 'NFC North', 'NFC South', 'NFC East', 'NFC West']
      positionNode.children!.sort((a, b) => {
        const aDiv = a.name.split(' (')[0]
        const bDiv = b.name.split(' (')[0]
        return divisionOrder.indexOf(aDiv) - divisionOrder.indexOf(bDiv)
      })
      
      root.children!.push(positionNode)
    })

    // Sort positions by fantasy relevance
    const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    root.children!.sort((a, b) => {
      const aPos = a.name.split(' ')[0]
      const bPos = b.name.split(' ')[0]
      return positionOrder.indexOf(aPos) - positionOrder.indexOf(bPos)
    })

    return root
  }

  const buildTeamTreeData = (players: Player[]): TreeNode => {
    // Team → Position → Status → Player hierarchy
    const root: TreeNode = {
      name: "",
      type: 'root',
      children: []
    }

    // Group by team first
    const teamGroups = groupBy(players, 'team')
    
    Object.entries(teamGroups).forEach(([team, teamPlayers]) => {
      const teamNode: TreeNode = {
        name: `${team} (${teamPlayers.length})`,
        type: 'team',
        children: []
      }

      // Group by position within team
      const positionGroups = groupBy(teamPlayers, 'position')
      
      Object.entries(positionGroups).forEach(([position, positionPlayers]) => {
        const positionNode: TreeNode = {
          name: `${position} (${positionPlayers.length})`,
          type: 'position',
          children: []
        }

        // Group by status within position
        const statusGroups = groupByStatus(positionPlayers)
        
        Object.entries(statusGroups).forEach(([status, statusPlayers]) => {
          const statusNode: TreeNode = {
            name: `${status} (${statusPlayers.length})`,
            type: 'status',
            children: []
          }

          // Add individual players
          statusPlayers.forEach(player => {
            const rankText = player.rankings.length > 0 
              ? ` - #${player.rankings[0].rank}` 
              : ''
            
            statusNode.children!.push({
              name: `${player.name}${rankText}`,
              type: 'player',
              data: player
            })
          })

          // Sort players by ranking
          statusNode.children!.sort((a, b) => {
            const aRank = a.data?.rankings[0]?.rank || 999
            const bRank = b.data?.rankings[0]?.rank || 999
            return aRank - bRank
          })

          positionNode.children!.push(statusNode)
        })

        // Sort status (Active first)
        positionNode.children!.sort((a, b) => {
          const statusOrder = ['Active', 'Inactive']
          const aStatus = a.name.split(' (')[0]
          const bStatus = b.name.split(' (')[0]
          return statusOrder.indexOf(aStatus) - statusOrder.indexOf(bStatus)
        })

        teamNode.children!.push(positionNode)
      })

      // Sort positions by fantasy relevance
      const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
      teamNode.children!.sort((a, b) => {
        const aPos = a.name.split(' ')[0]
        const bPos = b.name.split(' ')[0]
        return positionOrder.indexOf(aPos) - positionOrder.indexOf(bPos)
      })
      
      root.children!.push(teamNode)
    })

    // Sort teams alphabetically
    root.children!.sort((a, b) => a.name.localeCompare(b.name))

    return root
  }


  const getNodeRadius = (type: string): number => {
    switch (type) {
      case 'root': return 8
      case 'position': return 6
      case 'division': return 5
      case 'team': return 4
      case 'status': return 4
      case 'player': return 3
      default: return 3
    }
  }

  const getNodeColor = (node: TreeNode): string => {
    if (node.type === 'position') {
      const position = node.name.split(' ')[0]
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
    
    if (node.type === 'division') return '#fd7e14' // Orange for divisions
    if (node.type === 'team') return '#17a2b8'
    if (node.type === 'status') {
      const status = node.name.split(' ')[0]
      return status === 'Active' ? '#28a745' : '#6c757d' // Green for active, gray for inactive
    }
    if (node.type === 'player') {
      const player = node.data!
      const position = player.position
      switch (position) {
        case 'QB': return '#f8d7da'
        case 'RB': return '#d4edda'
        case 'WR': return '#cce7ff'
        case 'TE': return '#fff3cd'
        case 'K': return '#e2d9f3'
        case 'DST': return '#c3f0e8'
        default: return '#f8f9fa'
      }
    }
    
    return '#333'
  }

  const getFontSize = (type: string): string => {
    // Make font sizes more responsive and readable
    switch (type) {
      case 'root': return '16px'
      case 'position': return '14px'
      case 'division': return '13px'
      case 'team': return '12px'
      case 'status': return '11px'
      case 'player': return '10px'
      default: return '10px'
    }
  }

  const truncateText = (text: string, type: string): string => {
    // More aggressive truncation to prevent overflow
    if (type === 'player' && text.length > 20) {
      return text.substring(0, 17) + '...'
    }
    if (type === 'team' && text.length > 18) {
      return text.substring(0, 15) + '...'
    }
    if (type === 'division' && text.length > 22) {
      return text.substring(0, 19) + '...'
    }
    if (type === 'status' && text.length > 16) {
      return text.substring(0, 13) + '...'
    }
    return text
  }

  if (loading || dimensions.width === 0) {
    return (
      <div 
        className="loading" 
        style={{ 
          textAlign: 'center', 
          padding: '60px',
          width: '100%',
          height: '70vh',
          minHeight: '600px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          border: '2px solid #ddd',
          borderRadius: '8px',
          background: '#fafafa'
        }}
      >
        <h3>🌳 Building player tree...</h3>
        <p>Loading D3.js visualization and calculating dimensions</p>
        <div style={{ marginTop: '20px' }}>
          <div className="spinner" style={{
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #007bff',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            animation: 'spin 2s linear infinite',
            margin: '0 auto'
          }}></div>
        </div>
      </div>
    )
  }

  if (!players || players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#666' }}>
        <h3>🌳 Fantasy Football Player Tree</h3>
        <p>Use the search form to load players and see the tree visualization</p>
      </div>
    )
  }

  return (
    <div className="tree-container">
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <h3>🌳 Fantasy Football Player Tree</h3>
        <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
          {viewMode === 'position' 
            ? 'Position → Division → Team → Players' 
            : 'Team → Position → Status → Players'
          }
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px' }}>
          <small>📋 <strong>Instructions:</strong></small>
          <small>🖱️ Click nodes to expand/collapse</small>
          <small>🔍 Hover over players for details</small>
          <small>📜 Scroll to explore large dataset</small>
        </div>
      </div>
      
      <div 
        ref={containerRef}
        style={{ 
          width: '100%',
          height: '70vh', // Use viewport height for better responsiveness
          minHeight: '600px',
          maxHeight: '90vh',
          overflow: 'auto', 
          border: '2px solid #ddd', 
          borderRadius: '8px',
          background: '#fafafa',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          position: 'relative'
        }}
      >
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          style={{ 
            display: 'block',
            width: '100%',
            height: '100%',
            maxWidth: '100%'
          }}
        />
      </div>

      <div style={{ marginTop: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap', marginBottom: '10px' }}>
          <div><span style={{ backgroundColor: '#dc3545', padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' }}>QB</span></div>
          <div><span style={{ backgroundColor: '#28a745', padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' }}>RB</span></div>
          <div><span style={{ backgroundColor: '#007bff', padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' }}>WR</span></div>
          <div><span style={{ backgroundColor: '#ffc107', padding: '4px 8px', borderRadius: '4px', color: 'black', fontSize: '12px' }}>TE</span></div>
          <div><span style={{ backgroundColor: '#6f42c1', padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' }}>K</span></div>
          <div><span style={{ backgroundColor: '#20c997', padding: '4px 8px', borderRadius: '4px', color: 'white', fontSize: '12px' }}>DST</span></div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <small style={{ color: '#666' }}>
            💡 Collapsed nodes show <span style={{ backgroundColor: '#lightsteelblue', padding: '2px 4px', borderRadius: '3px' }}>light blue</span> • 
            Tree starts with positions collapsed for easier navigation
          </small>
        </div>
      </div>
    </div>
  )
}

export default PlayerTreeView