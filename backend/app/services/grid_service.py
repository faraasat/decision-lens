import httpx
import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from .grid_queries import GET_RECENT_SERIES, GET_SERIES_DETAILS, GET_SERIES_STATS

load_dotenv()
logger = logging.getLogger("decision-lens.grid")


class GridService:
    """
    GRID API Service based on official documentation:
    - Central Data Feed (GraphQL): https://api-op.grid.gg/central-data/graphql
    - Statistics Feed (GraphQL): https://api-op.grid.gg/statistics-feed/graphql
    - Series State API: WebSocket only (not REST)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRID_API_KEY")

        # Official GRID API endpoints per documentation
        self.central_data_url = "https://api-op.grid.gg/central-data/graphql"
        self.statistics_url = "https://api-op.grid.gg/statistics-feed/graphql"
        self.file_download_url = "https://api.grid.gg/file-download"

        self.headers = {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json",
        }

        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.error("No valid GRID_API_KEY found.")

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """
        Fetch match data using GRID File Download API for full timeline.
        Falls back to GraphQL if file is not available.
        """
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            raise ValueError("GRID_API_KEY is missing or invalid.")

        async with httpx.AsyncClient() as client:
            # Try to fetch full end-state data from File Download API
            try:
                logger.info(f"Fetching end-state data for series {match_id}")
                file_res = await client.get(
                    f"{self.file_download_url}/end-state/grid/series/{match_id}",
                    headers={"x-api-key": self.api_key},
                    timeout=30.0,
                )
                
                if file_res.status_code == 200:
                    logger.info(f"Successfully fetched full timeline for {match_id}")
                    return file_res.json()
                else:
                    logger.warning(f"File Download API not available (Status: {file_res.status_code}), falling back to GraphQL")
            except Exception as e:
                logger.error(f"Error calling File Download API: {str(e)}")

            # Fallback to GraphQL (Original implementation)
            # 1. Fetch Series Details (Teams, Tournament)
            try:
                logger.info(f"Fetching details for series {match_id}")
                details_res = await client.post(
                    self.central_data_url,
                    headers=self.headers,
                    json={"query": GET_SERIES_DETAILS, "variables": {"id": match_id}},
                    timeout=10.0,
                )

                details_data = {}
                if details_res.status_code == 200:
                    d_json = details_res.json()
                    details_data = d_json.get("data", {}).get("series", {})
                else:
                    logger.error(f"Failed to fetch details: {details_res.status_code}")
            except Exception as e:
                logger.error(f"Error fetching details: {str(e)}")
                details_data = {}

            # 2. Fetch Series Stats
            try:
                logger.info(f"Fetching stats for series {match_id}")
                stats_res = await client.post(
                    self.statistics_url,
                    headers=self.headers,
                    json={
                        "query": GET_SERIES_STATS,
                        "variables": {"seriesId": match_id},
                    },
                    timeout=10.0,
                )

                stats_data = {}
                if stats_res.status_code == 200:
                    s_json = stats_res.json()
                    stats_data = s_json.get("data", {}).get("seriesStats", {})
                else:
                    logger.error(f"Failed to fetch stats: {stats_res.status_code}")
            except Exception as e:
                logger.error(f"Error fetching stats: {str(e)}")
                stats_data = {}

        # Construct the response object
        # We need to adapt the GraphQL data to look like the legacy file download data
        # so that the normalizer and frontend can consume it without major refactors.

        games = stats_data.get("games", [])
        current_game = games[-1] if games else {}

        # Construct metadata
        teams = details_data.get("teams", [])
        team1 = teams[0] if len(teams) > 0 else {}
        team2 = teams[1] if len(teams) > 1 else {}

        timestamp = 0
        if current_game:
            # Duration is in seconds or something? format usually "PT34M12S" or similar ISO
            # For now assume we just use current time or 0
            timestamp = 0

        return {
            "series_id": match_id,
            "metadata": {
                "teams": [
                    {
                        "id": 100,
                        "name": team1.get("base", {}).get("name", "Team 1"),
                        "roster": team1.get("roster", []),
                    },
                    {
                        "id": 200,
                        "name": team2.get("base", {}).get("name", "Team 2"),
                        "roster": team2.get("roster", []),
                    },
                ],
                "tournament": details_data.get("tournament", {}).get("name"),
                "title": details_data.get("title", {}).get("name"),
            },
            # We pass the raw stats to be used by the app.
            # The app's normalizer might need updates if it strictly expects file format.
            "stats": current_game,
            "raw_details": details_data,
        }

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Alias for get_match_timeline since we fetch everything together now."""
        return await self.get_match_timeline(match_id)

    async def get_live_matches(self, game: str = "lol") -> List[Dict[str, Any]]:
        """
        Fetch a list of series with available live data using GRID Central Data API.
        Uses productServiceLevels filter to only return series with FULL live data available.
        """
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            raise ValueError("GRID_API_KEY is missing or invalid.")

        # Map game to titleId (LoL: 3, Valorant: 6)
        title_id = 3 if game == "lol" else 6

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching series with live data for titleId: {title_id}")
                response = await client.post(
                    self.central_data_url,
                    headers=self.headers,
                    json={
                        "query": GET_RECENT_SERIES,
                        "variables": {"titleId": str(title_id)},
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    res_json = response.json()

                    if res_json.get("errors"):
                        logger.error(f"GraphQL errors: {res_json.get('errors')}")
                        return []

                    data = res_json.get("data", {})
                    all_series = data.get("allSeries", {})
                    edges = all_series.get("edges", [])

                    matches = []
                    for edge in edges[:10]:
                        node = edge.get("node", {})
                        if not node:
                            continue

                        matches.append(
                            {
                                "id": str(node.get("id")),
                                "game": game,
                                "title": node.get("title", {}).get("name", "Unknown"),
                                "tournament": node.get("tournament", {}).get(
                                    "name", "Unknown"
                                ),
                                "status": "available",
                            }
                        )

                    logger.info(f"Found {len(matches)} live matches")
                    return matches
                else:
                    logger.error(f"Central Data error: {response.status_code}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching live matches: {str(e)}")
                return []


# Singleton instance
grid_service = GridService()
