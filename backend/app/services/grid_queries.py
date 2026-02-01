"""
GraphQL queries for GRID API endpoints.
Based on official GRID API documentation.
"""

LOL = 3
VALORANT = 6

types = "ESPORTS"

# Central Data Feed - Get Recent Series
# Endpoint: https://api-op.grid.gg/central-data/graphql
GET_RECENT_SERIES = """
query GetRecentSeries($titleId: ID!) {
    allSeries(first: 30, filter: {titleId: $titleId}) {
        edges {
            node {
                id
                title {
                    name
                }
                tournament {
                    name
                }
            }
        }
    }
}
"""

# Live Data Feed - Get Live Series State
# Endpoint: https://api-op.grid.gg/live-data-feed/graphql
GET_LIVE_SERIES_STATE = """
query GetLiveSeriesState($titleIds: [ID!]!) {
    allSeries(titleIds: $titleIds) {
        id
        state
        title {
            id
            name
        }
        tournament {
            id
            name
        }
    }
}
"""
