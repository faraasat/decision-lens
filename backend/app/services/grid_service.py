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
            logger.info(f"Using mock details for match {match_id}")
            return self._get_mock_data()
            
        url = f"{self.base_url}/series-data/matches/{match_id}"
        logger.info(f"Fetching match details from {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch match details: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data (events, snapshots)."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            logger.info(f"Using mock timeline for match {match_id}")
            return self._get_mock_data()

        url = f"{self.base_url}/series-data/matches/{match_id}/timeline"
        logger.info(f"Fetching match timeline from {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch match timeline: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()

    def _get_mock_data(self) -> Dict[str, Any]:
        mock_file = Path(__file__).parent / "mock_match.json"
        try:
            with open(mock_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading mock file {mock_file}: {str(e)}")
            raise

# Singleton instance
grid_service = GridService()
