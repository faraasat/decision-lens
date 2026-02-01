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
        self.headers = {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json"
        }
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.warning("No valid GRID_API_KEY found. Falling back to mock data.")

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch general match metadata."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info(f"No API key, using mock details for match {match_id}")
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
                        return response.json()
                    elif response.status_code == 404:
                        logger.warning(f"Match {match_id} not found at {url}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching from {url}: {str(e)}")
                    continue
        
        logger.warning(f"Match {match_id} not found on any GRID endpoint. Falling back to mock data.")
        return self._get_mock_data(match_id)

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data (events, snapshots)."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info(f"No API key, using mock timeline for match {match_id}")
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
                        return response.json()
                    elif response.status_code == 404:
                        logger.warning(f"Timeline for match {match_id} not found at {url}")
                        continue
                except Exception as e:
                    logger.error(f"Error fetching timeline from {url}: {str(e)}")
                    continue

        logger.warning(f"Timeline for match {match_id} not found on any GRID endpoint. Falling back to mock data.")
        return self._get_mock_data(match_id)

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
