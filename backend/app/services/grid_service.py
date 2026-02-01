import httpx
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class GridService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRID_API_KEY")
        self.base_url = base_url or os.getenv("GRID_BASE_URL", "https://api.grid.gg")
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Fetch general match metadata."""
        url = f"{self.base_url}/series-data/matches/{match_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_match_timeline(self, match_id: str) -> Dict[str, Any]:
        """Fetch detailed match timeline data (events, snapshots)."""
        # GRID often uses different paths for timeline data, placeholder for now
        url = f"{self.base_url}/series-data/matches/{match_id}/timeline"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

# Singleton instance
grid_service = GridService()
