"""
GraphQL queries for GRID API endpoints.
Based on official GRID API documentation.
"""

LOL = 3
VALORANT = 6

# Central Data Feed - Get Series with Available Data
# Endpoint: https://api-op.grid.gg/central-data/graphql
# Uses productServiceLevels filter to only get series with live data available
GET_RECENT_SERIES = """
query GetRecentSeries($titleId: ID!) {
    allSeries(
        first: 50, 
        filter: {
            titleId: $titleId,
            types: ESPORTS,
            productServiceLevels: {
                productName: "liveDataFeed",
                serviceLevel: FULL
            }
        },
        orderBy: StartTimeScheduled,
        orderDirection: DESC
    ) {
        totalCount
        pageInfo {
            hasPreviousPage
            hasNextPage
            startCursor
            endCursor
        }
        edges {
            node {
                id
                title {
                    name
                }
                tournament {
                    name
                }
                startTimeScheduled
            }
        }
    }
}
"""

# Central Data Feed - Get Series Details
# Endpoint: https://api-op.grid.gg/central-data/graphql
GET_SERIES_DETAILS = """
query GetSeriesDetails($id: ID!) {
    series(id: $id) {
        id
        title {
            id
            name
        }
        tournament {
            name
        }
        startTimeScheduled
        teams {
            base {
                id
                name
                code
            }
            roster {
                id
                nickname
            }
        }
        format {
            name
        }
    }
}
"""

# Statistics Feed - Get Series Stats
# Endpoint: https://api-op.grid.gg/statistics-feed/graphql
GET_SERIES_STATS = """
query GetSeriesStats($seriesId: ID!) {
    seriesStats(seriesId: $seriesId) {
        seriesId
        games {
            gameId
            matchNumber
            winnerId
            duration
            playerStats {
                playerId
                teamId
                kills
                deaths
                assists
                goldEarned
                damageDealtToChampions
                cs
                visionScore
                # Valorant specific
                averageCombatScore
                averageDamagePerRound
                headshots
            }
            teamStats {
                teamId
                goldEarned
                kills
                towersDestroyed
                dragonsKilled
                baronsKilled
                # Valorant
                roundsWon
            }
        }
    }
}
"""
