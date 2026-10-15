"""Content package API endpoints.

This provides endpoints for serving JSON packages to the client:
- Lesson JSON packages (with signs, videos, recognition labels)
- Minigame JSON packages (with config)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any, List

from database.postgre_session import get_postgres_session
from security import get_current_user_id

router = APIRouter(prefix="/api/v1/packages", tags=["packages"])


@router.get("/lessons/{module_code}")
async def get_lesson_package(module_code: str):
    """
    Get lesson JSON package for a module.
    
    Returns lesson data in the format:
    {
      "module_name": [
        {
          "id": "sign_id",
          "label": "Sign Label",
          "video": "path/to/video.mp4",
          "recognition_label": "SIGN_LABEL"
        }
      ]
    }
    
    Args:
        module_code: The module code (e.g., "alphabet", "numbers")
        
    Returns:
        Lesson JSON package
    """
    try:
        with get_postgres_session() as db:
            # TODO: Implement lesson package generation
            # 1. Query module by module_code
            # 2. Query lessons in module
            # 3. Query signs in lessons
            # 4. Query media files for signs
            # 5. Format as JSON package
            
            return {
                "module_code": module_code,
                "module_name": "",
                "lessons": [],
                "message": "Lesson package endpoint - to be implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching lesson package: {str(e)}"
        )


@router.get("/minigames/{minigame_id}")
async def get_minigame_package(minigame_id: str):
    """
    Get minigame JSON package.
    
    Returns minigame config in the format:
    {
      "minigame_id": "sign_sprint",
      "game_name": "Sign Sprint",
      "game_type": "camera",
      "module_id": "alphabet",
      "config": {
        "rounds": 5,
        "time_limit": 60
      }
    }
    
    Args:
        minigame_id: The minigame ID
        
    Returns:
        Minigame JSON package
    """
    try:
        with get_postgres_session() as db:
            # TODO: Implement minigame package generation
            # 1. Query minigame by minigame_id
            # 2. Format config as JSON
            
            return {
                "minigame_id": minigame_id,
                "game_name": "",
                "game_type": "",
                "module_id": "",
                "config": {},
                "message": "Minigame package endpoint - to be implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching minigame package: {str(e)}"
        )


@router.get("/modules")
async def get_module_list():
    """
    Get list of all modules with their codes and names.
    
    Returns:
        List of modules
    """
    try:
        with get_postgres_session() as db:
            # TODO: Implement module list retrieval
            return {
                "modules": [],
                "message": "Module list endpoint - to be implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching module list: {str(e)}"
        )
