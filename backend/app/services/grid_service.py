import httpx
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class GridService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRID_API_KEY")
        self.base_url = base_url or os.getenv("GRID_BASE_URL", "https://api.grid.gg")
        self.headers = {
            "x-api-key": self.api_key or "",
            "Content-Type": "application/json"
        }

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch general match metadata."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            # Fallback to mock data for demo
            return self._get_mock_data()
            
        url = f"{self.base_url}/series-data/matches/{match_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data (events, snapshots)."""
        if not self.api_key or self.api_key == "YOUR_GRID_API_KEY":
            # Fallback to mock data for demo
            return self._get_mock_data()

        url = f"{self.base_url}/series-data/matches/{match_id}/timeline"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def _get_mock_data(self) -> Dict[str, Any]:
        mock_file = Path(__file__).parent / "mock_match.json"
        with open(mock_file, "r") as f:
            return json.load(f)

# Singleton instance
grid_service = GridService()
