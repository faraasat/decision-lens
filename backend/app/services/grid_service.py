import httpx
import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from .grid_queries import GET_RECENT_SERIES, GET_LIVE_SERIES_STATE

load_dotenv()
logger = logging.getLogger("decision-lens.grid")

class GridService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRID_API_KEY")
        self.base_url = base_url or os.getenv("GRID_BASE_URL", "https://api-op.grid.gg")
        
        # Official GRID API endpoints
        self.central_data_url = f"{self.base_url}/central-data/graphql"
        self.live_data_feed_url = f"{self.base_url}/live-data-feed/graphql"
        self.stats_feed_url = f"{self.base_url}/statistics-feed/graphql"
        
        self.headers = {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json"
        }
        
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.error("No valid GRID_API_KEY found.")

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch general match metadata from GRID File Download API."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            raise ValueError("GRID_API_KEY is missing or invalid.")
            
        # GRID File Download API endpoints
        url = f"{self.base_url}/file-download/end-state/grid/series/{match_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching match details for series {match_id}")
                response = await client.get(url, headers=self.headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched match details for series {match_id}")
                    return data
                else:
                    logger.warning(f"Failed to fetch match details: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching match details: {str(e)}")
        
        raise ValueError(f"Match {match_id} details not found on GRID API.")

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data from GRID File Download API."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            raise ValueError("GRID_API_KEY is missing or invalid.")

        # GRID File Download API for timeline data
        url = f"{self.base_url}/file-download/end-state/grid/series/{match_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching timeline for series {match_id}")
                response = await client.get(url, headers=self.headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched timeline for series {match_id}")
                    return data
                else:
                    logger.warning(f"Failed to fetch timeline: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching timeline: {str(e)}")

        raise ValueError(f"Timeline for match {match_id} not found on GRID API.")

    async def get_live_matches(self, game: str = "lol") -> List[Dict[str, Any]]:
        """Fetch a list of live or recent matches using GRID APIs."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            raise ValueError("GRID_API_KEY is missing or invalid.")

        # Map game to titleId (LoL: 3, Valorant: 6)
        title_id = 3 if game == "lol" else 6
        
        # 1. Try Live Data Feed GraphQL API for live matches
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Checking Live Data Feed GraphQL for titleId: {title_id}")
                response = await client.post(
                    self.live_data_feed_url,
                    headers=self.headers,
                    json={"query": GET_LIVE_SERIES_STATE, "variables": {"titleIds": [str(title_id)]}},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    res_json = response.json()
                    
                    # Check for GraphQL errors
                    if res_json.get("errors"):
                        error_messages = [err.get("message", str(err)) for err in res_json["errors"]]
                        logger.warning(f"Live Data Feed errors: {error_messages}")
                    
                    # Extract live series data
                    data = res_json.get("data", {})
                    series_list = data.get("allSeries", [])
                    
                    if series_list and isinstance(series_list, list) and len(series_list) > 0:
                        matches = []
                        for series in series_list:
                            series_id = series.get("id")
                            if not series_id:
                                continue
                            
                            title_obj = series.get("title", {})
                            tournament_obj = series.get("tournament", {})
                            state = series.get("state", "unknown")
                            
                            matches.append({
                                "id": str(series_id),
                                "game": game,
                                "title": title_obj.get("name", "Live Match"),
                                "tournament": tournament_obj.get("name", "Live Tournament"),
                                "status": "live" if state == "running" else state
                            })
                        
                        if matches:
                            logger.info(f"Found {len(matches)} live series in Live Data Feed")
                            return matches
                else:
                    logger.warning(f"Live Data Feed returned {response.status_code}")
            except Exception as e:
                logger.warning(f"Live Data Feed unavailable: {str(e)}")

        # 2. Fallback to Central Data API for recent series
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching from Central Data for titleId: {title_id}")
                response = await client.post(
                    self.central_data_url,
                    headers=self.headers,
                    json={"query": GET_RECENT_SERIES, "variables": {"titleId": str(title_id)}},
                    timeout=10.0
                )

                if response.status_code == 200:
                    res_json = response.json()
                    
                    # Check for GraphQL errors
                    if res_json.get("errors"):
                        error_messages = [err.get("message", str(err)) for err in res_json["errors"]]
                        logger.error(f"Central Data GraphQL errors: {error_messages}")
                        return []
                    
                    # Extract data
                    data = res_json.get("data", {})
                    all_series = data.get("allSeries", {})
                    edges = all_series.get("edges", [])
                    
                    if not edges:
                        logger.info(f"No series found for titleId {title_id}")
                        return []
                    
                    matches = []
                    for edge in edges:
                        node = edge.get("node", {})
                        if not node or not node.get("id"):
                            continue

                        title = node.get("title", {})
                        tournament = node.get("tournament", {})

                        matches.append({
                            "id": str(node.get("id")),
                            "game": game,
                            "title": title.get("name", "Unknown Series"),
                            "tournament": tournament.get("name", "Unknown Tournament"),
                            "status": "completed"
                        })
                    
                    logger.info(f"Found {len(matches)} series in Central Data")
                    return matches
                else:
                    logger.error(f"Central Data returned {response.status_code}: {response.text[:200]}")
                    return []
            except Exception as e:
                logger.error(f"Error fetching from Central Data: {str(e)}")
                return []

        return []

# Singleton instance
grid_service = GridService()
