from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

# Placeholder to restore backend health
@router.get("/regional")
async def get_regional_indices():
    return {}

