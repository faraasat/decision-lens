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
            timeline_data = {}
            try:
                logger.info(f"Fetching end-state data for series {match_id}")
                file_res = await client.get(
                    f"{self.file_download_url}/end-state/grid/series/{match_id}",
                    headers={"x-api-key": self.api_key},
                    timeout=30.0,
                )
                
                if file_res.status_code == 200:
                    logger.info(f"Successfully fetched full timeline for {match_id}")
                    timeline_data = file_res.json()
                else:
                    logger.warning(f"File Download API not available (Status: {file_res.status_code}), falling back to Series State")
                    # Fallback to Series State API for live matches
                    state_res = await client.get(
                        f"https://api.grid.gg/series-state/grid/series/{match_id}",
                        headers={"x-api-key": self.api_key},
                        timeout=10.0,
                    )
                    if state_res.status_code == 200:
                        timeline_data = state_res.json()
                        logger.info(f"Successfully fetched live state for {match_id}")
                    else:
                        logger.error(f"Failed to fetch live state: {state_res.status_code}")
            except Exception as e:
                logger.error(f"Error calling GRID APIs: {str(e)}")

            # Fetch Series Details (Teams, Tournament) - always good to have
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
                    details_data = d_json.get("data", {}).get("series", {}) or {}
                else:
                    logger.error(f"Failed to fetch details: {details_res.status_code}")
            except Exception as e:
                logger.error(f"Error fetching details: {str(e)}")
                details_data = {}

            # Fetch Series Stats
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
                    stats_data = s_json.get("data", {}).get("seriesStats", {}) or {}
                else:
                    logger.error(f"Failed to fetch stats: {stats_res.status_code}")
            except Exception as e:
                logger.error(f"Error fetching stats: {str(e)}")
                stats_data = {}

        # Construct the response object
        teams = details_data.get("teams", [])
        
        # Determine game title and ID
        title_name = details_data.get("title", {}).get("name")
        if not title_name:
            if "seriesState" in timeline_data:
                title_name = timeline_data["seriesState"].get("title", {}).get("name")
            else:
                title_name = timeline_data.get("title", {}).get("name")
        
        game = "lol"
        if title_name:
            title_lower = title_name.lower()
            if "valorant" in title_lower:
                game = "valorant"
            elif "league of legends" in title_lower or "lol" in title_lower:
                game = "lol"
        
        # If we still don't know, try titleId
        title_id = str(details_data.get("title", {}).get("id") or 
                       timeline_data.get("seriesState", {}).get("titleId") or 
                       timeline_data.get("titleId", ""))
        
        if title_id == "6":
            game = "valorant"
        elif title_id == "3":
            game = "lol"

        team_list = []
        
        # Strategy: Use details_data as base, then enrich with timeline_data
        base_teams = details_data.get("teams", [])
        
        # Find where the game state is (seriesState or root)
        state = timeline_data.get("seriesState") or timeline_data
        
        # Collect all unique teams from across the data structure
        timeline_teams = state.get("teams", [])
        if "games" in state:
            for g in state["games"]:
                for t in g.get("teams", []):
                    if not any(et.get("name") == t.get("name") for et in timeline_teams):
                        timeline_teams.append(t)

        if base_teams:
            for i, t in enumerate(base_teams):
                draft = []
                team_name = t.get("base", {}).get("name")
                
                # Try to find matching team and extract characters
                matching_t = next((tt for tt in timeline_teams if tt.get("name") == team_name), None)
                if not matching_t and i < len(timeline_teams):
                    matching_t = timeline_teams[i]
                
                if matching_t:
                    # Method 1: from players
                    for p in matching_t.get("players", []):
                        char = p.get("champion") or p.get("agent")
                        if char and char.get("name"):
                            draft.append(char.get("name"))
                    
                    # Method 2: from draftActions (fallback)
                    if not draft and "draftActions" in matching_t:
                        for action in matching_t["draftActions"]:
                            if action.get("type") == "PICK":
                                char = action.get("champion") or action.get("agent")
                                if char and char.get("name"):
                                    draft.append(char.get("name"))

                # Method 3: Search all games in state for this team's draft
                if not draft and "games" in state:
                    for g in state["games"]:
                        for gt in g.get("teams", []):
                            if gt.get("name") == team_name:
                                for p in gt.get("players", []):
                                    char = p.get("champion") or p.get("agent")
                                    if char and char.get("name"):
                                        draft.append(char.get("name"))
                
                team_list.append({
                    "id": 100 if i == 0 else 200,
                    "name": team_name or f"Team {i+1}",
                    "code": t.get("base", {}).get("code"),
                    "roster": t.get("roster", []),
                    "side": "blue" if i == 0 else "red",
                    "draft": list(set(draft)) if draft else []
                })
        elif timeline_teams:
            # Fallback to timeline teams if details missing
            for i, t in enumerate(timeline_teams):
                draft = []
                for p in t.get("players", []):
                    char = p.get("champion") or p.get("agent")
                    if char and char.get("name"):
                        draft.append(char.get("name"))
                
                if not draft and "draftActions" in t:
                    for action in t["draftActions"]:
                        if action.get("type") == "PICK":
                            char = action.get("champion") or action.get("agent")
                            if char and char.get("name"):
                                draft.append(char.get("name"))

                team_list.append({
                    "id": 100 if i == 0 else 200,
                    "name": t.get("name", f"Team {i+1}"),
                    "side": "blue" if i == 0 else "red",
                    "draft": list(set(draft)) if draft else []
                })

        result = {
            "series_id": match_id,
            "metadata": {
                "teams": team_list,
                "tournament": details_data.get("tournament", {}).get("name") or state.get("tournament", {}).get("name") or "Unknown Tournament",
                "title": title_name or "Unknown Title",
                "game": game,
                "video_url": f"https://player.grid.gg/video-widget?seriesId={match_id}&key={self.api_key}"
            },
            "stats": stats_data,
            "raw_details": details_data,
        }
        
        # Merge timeline data if present
        if timeline_data:
            result.update(timeline_data)
        
        return result

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
                                "startTimeScheduled": node.get("startTimeScheduled"),
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
