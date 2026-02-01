import asyncio
import json
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.services.grid_service import GridService
from dotenv import load_dotenv

load_dotenv()

async def ingest_match(match_id: str):
    print(f"Ingesting match: {match_id}...")
    service = GridService()
    
    try:
        # Create data directory if it doesn't exist
        data_dir = Path(__file__).parent.parent / "data" / "raw"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch data
        details = await service.get_match_details(match_id)
        timeline = await service.get_match_timeline(match_id)
        
        # Save to files
        with open(data_dir / f"{match_id}_details.json", "w") as f:
            json.dump(details, f, indent=2)
            
        with open(data_dir / f"{match_id}_timeline.json", "w") as f:
            json.dump(timeline, f, indent=2)
            
        print(f"Successfully ingested data for match {match_id} into {data_dir}")
        
    except Exception as e:
        print(f"Error ingesting match: {e}")

if __name__ == "__main__":
    match_id = os.getenv("MATCH_ID")
    if not match_id:
        print("Please set MATCH_ID in your .env file.")
        sys.exit(1)
        
    asyncio.run(ingest_match(match_id))
