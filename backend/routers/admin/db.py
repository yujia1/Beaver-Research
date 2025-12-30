from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any, Optional
from database import get_db, engine
from routers.admin.auth import get_current_user
import models

router = APIRouter()

def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access database management tools"
        )
    return current_user

@router.get("/tables", response_model=List[str])
async def get_tables(
    current_user: models.User = Depends(require_admin)
):
    """List all tables in the database"""
    inspector = inspect(engine)
    return inspector.get_table_names()

@router.get("/table/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_desc: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Get data from a specific table with pagination"""
    # Verify table exists to prevent SQL injection via table name
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{table_name}' not found"
        )
    
    # Get columns
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    # Construct query safely
    # Note: table_name is verified against inspector above
    query_str = f"SELECT * FROM {table_name}"
    
    # Add sorting if requested
    if sort_by and sort_by in columns:
        direction = "DESC" if sort_desc else "ASC"
        query_str += f" ORDER BY {sort_by} {direction}"
    
    # Add pagination
    query_str += f" LIMIT {limit} OFFSET {offset}"
    
    # Execute query
    result = db.execute(text(query_str))
    
    # Fetch rows
    rows = []
    for row in result:
        # Convert row to dict
        row_dict = {}
        for idx, col in enumerate(columns):
            row_dict[col] = row[idx]
        rows.append(row_dict)
        
    # Get total count
    count_query = f"SELECT COUNT(*) FROM {table_name}"
    total_count = db.execute(text(count_query)).scalar()
    
    return {
        "table": table_name,
        "columns": columns,
        "total_count": total_count,
        "rows": rows,
        "limit": limit,
        "offset": offset
    }
