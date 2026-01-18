from fastapi import APIRouter, Depends
from routers.admin.auth import get_current_user, create_role_dependency
import models

router = APIRouter()

# Create role-specific access dependency (tiered: creator/contributor bypass payment)
require_academy_access = create_role_dependency('/academy')


@router.get("/")
async def get_academy_home(
    current_user: models.User = Depends(require_academy_access)
):
    """Get Academy home page data"""
    return {
        "message": "Welcome to Academy",
        "user": {
            "username": current_user.username,
            "role": current_user.role
        }
    }


@router.get("/courses")
async def get_courses(
    current_user: models.User = Depends(require_academy_access)
):
    """Get available courses"""
    # Placeholder for course data
    return {
        "courses": [
            {
                "id": 1,
                "title": "Introduction to Financial Analysis",
                "description": "Learn the basics of financial statement analysis",
                "level": "beginner"
            },
            {
                "id": 2,
                "title": "Advanced Trading Strategies",
                "description": "Master advanced trading techniques and risk management",
                "level": "advanced"
            }
        ]
    }


@router.get("/courses/{course_id}")
async def get_course(
    course_id: int,
    current_user: models.User = Depends(require_academy_access)
):
    """Get specific course details"""
    # Placeholder for course details
    return {
        "id": course_id,
        "title": "Course Title",
        "description": "Course description",
        "modules": []
    }
