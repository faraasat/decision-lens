import httpx
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("decision-lens.grid")

class GridService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRID_API_KEY")
        self.base_url = base_url or os.getenv("GRID_BASE_URL", "https://api.grid.gg")
        self.graphql_url = "https://api.grid.gg/central-data/graphql"
        self.headers = {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json"
        }
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.warning("No valid GRID_API_KEY found. Falling back to mock data.")

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch general match metadata."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info(f"Using mock details for match {match_id} (No API key)")
            return self._get_mock_data(match_id)
            
        # Try both versioned and unversioned endpoints for robustness
        endpoints = [
            f"{self.base_url}/series-data/v1/matches/{match_id}",
            f"{self.base_url}/series-data/matches/{match_id}"
        ]
        
        async with httpx.AsyncClient() as client:
            for url in endpoints:
                try:
                    logger.info(f"Fetching match details from {url}")
                    response = await client.get(url, headers=self.headers, timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Successfully fetched match details from GRID: {match_id}")
                        return data
                    elif response.status_code == 401:
                        logger.error(f"Unauthorized (401) fetching from {url}. Check GRID_API_KEY.")
                        break
                    elif response.status_code == 404:
                        logger.warning(f"Match {match_id} not found at {url}")
                        continue
                    else:
                        logger.warning(f"GRID API returned {response.status_code} for {url}")
                except Exception as e:
                    logger.error(f"Error fetching from {url}: {str(e)}")
                    continue
        
        logger.warning(f"Match {match_id} fallback to mock data (Not found or API error)")
        return self._get_mock_data(match_id)

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data (events, snapshots)."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info(f"Using mock timeline for match {match_id} (No API key)")
            return self._get_mock_data(match_id)

        endpoints = [
            f"{self.base_url}/series-data/v1/matches/{match_id}/timeline",
            f"{self.base_url}/series-data/matches/{match_id}/timeline"
        ]
        
        async with httpx.AsyncClient() as client:
            for url in endpoints:
                try:
                    logger.info(f"Fetching match timeline from {url}")
                    response = await client.get(url, headers=self.headers, timeout=10.0)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"Successfully fetched match timeline from GRID: {match_id}")
                        return data
                    elif response.status_code == 401:
                        logger.error(f"Unauthorized (401) fetching timeline from {url}. Check GRID_API_KEY.")
                        break
                    elif response.status_code == 404:
                        logger.warning(f"Timeline for match {match_id} not found at {url}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching timeline from {url}: {str(e)}")
                    continue

        logger.warning(f"Timeline for match {match_id} fallback to mock data")
        return self._get_mock_data(match_id)

    async def get_live_matches(self, game: str = "lol") -> List[Dict[str, Any]]:
        """Fetch a list of live or recent matches using GRID GraphQL API."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info("Using mock match list (No API key)")
            return [
                {"id": "4063857", "game": "lol", "title": "Cloud9 vs T1", "status": "live", "tournament": "Worlds 2025"},
                {"id": "val-match-1", "game": "valorant", "title": "Sentinels vs Fnatic", "status": "live", "tournament": "VCT Masters"}
            ]

        # Map game string to titleId
        title_id = 3 if game == "lol" else 6
        
        query = """
        query GetRecentSeries($titleId: Int!) {
            allSeries (
                first: 20,
                filter: {
                    titleId: $titleId
                    types: ESPORTS
                }
                orderBy: StartTimeScheduled
                orderDirection: DESC
            ) {
                edges {
                    node {
                        id
                        tournament {
                            name
                        }
                        teams {
                            name
                        }
                    }
                }
            }
        }
        """
        
        variables = {"titleId": title_id}
        
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Fetching live matches from GraphQL for titleId: {title_id}")
                response = await client.post(
                    self.graphql_url, 
                    headers=self.headers, 
                    json={"query": query, "variables": variables},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    edges = data.get("data", {}).get("allSeries", {}).get("edges", [])
                    matches = []
                    for edge in edges:
                        node = edge.get("node", {})
                        teams = node.get("teams", [])
                        team_names = " vs ".join([t.get("name", "Unknown") for t in teams]) if teams else "TBD"
                        matches.append({
                            "id": node.get("id"),
                            "game": game,
                            "title": team_names,
                            "tournament": node.get("tournament", {}).get("name", "Unknown Tournament"),
                            "status": "live"
                        })
                    return matches
                else:
                    logger.warning(f"GRID GraphQL API returned {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error fetching GraphQL match list: {str(e)}")

        return []

    def _get_mock_data(self, match_id: str) -> Dict[str, Any]:
        # Determine which mock data to use based on match_id prefix or pattern
        if str(match_id).startswith("val"):
            mock_file = Path(__file__).parent / "mock_match_valorant.json"
        else:
            mock_file = Path(__file__).parent / "mock_match.json"
            
        try:
            with open(mock_file, "r") as f:
                data = json.load(f)
                # Update matchId in mock data to match requested ID for consistency
                if "metadata" in data:
                    data["metadata"]["matchId"] = match_id
                return data
        except Exception as e:
            logger.error(f"Error reading mock file {mock_file}: {str(e)}")
            raise

# Singleton instance
grid_service = GridService()
