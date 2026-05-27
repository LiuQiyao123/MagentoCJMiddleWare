from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.sync_log import SyncLog

router = APIRouter()

@router.get("/sync-history", response_model=List[dict])
async def get_sync_history(
    limit: int = Query(10, le=100, description="Number of records to return"),
    session: AsyncSession = Depends(get_db)
):
    """
    Get recent sync operation logs from database.
    """
    try:
        from sqlalchemy import text
        # Use raw SQL to avoid enum conversion issues
        query = text("""
            SELECT id, sync_type, entity_type, entity_id, status, message, 
                   error_details, started_at, completed_at, duration_ms, created_at
            FROM sync_logs 
            ORDER BY created_at DESC 
            LIMIT :limit
        """)
        result = await session.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        return [
            {
                "id": row[0],
                "sync_type": row[1],
                "entity_type": row[2],
                "entity_id": row[3],
                "status": row[4],
                "message": row[5],
                "error_details": row[6],
                "started_at": row[7].strftime("%Y-%m-%d %H:%M:%S") if row[7] else None,
                "completed_at": row[8].strftime("%Y-%m-%d %H:%M:%S") if row[8] else None,
                "duration_ms": row[9],
                "created_at": row[10].strftime("%Y-%m-%d %H:%M:%S") if row[10] else None
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sync history: {str(e)}")
