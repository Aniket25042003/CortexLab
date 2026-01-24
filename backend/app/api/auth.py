"""
Authentication API Routes

Handles Google OAuth authentication using authorization code flow.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from typing import Optional

from app.core.database import get_db
from app.core.security import create_session_token, verify_session_token
from app.config import get_settings
from app.models import User
from app.schemas import GoogleAuthRequest, AuthResponse, UserResponse

router = APIRouter()
settings = get_settings()

# Google OAuth token endpoint
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    request: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth using authorization code flow.
    
    Exchanges the authorization code for access token using client_secret,
    then fetches user info and creates/retrieves user account.
    """
    try:
        # Exchange authorization code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": request.id_token,  # This is actually the auth code
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": "postmessage",  # Special value for popup flow
                    "grant_type": "authorization_code",
                },
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail=f"Failed to exchange code: {token_response.text}"
                )
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=401, detail="No access token received")
            
            # Fetch user info using the access token
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=401, 
                    detail="Failed to fetch user info"
                )
            
            userinfo = userinfo_response.json()
        
        # Extract user info
        google_id = userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name", email.split("@")[0] if email else "User")
        avatar_url = userinfo.get("picture")
        
        if not google_id or not email:
            raise HTTPException(status_code=401, detail="Invalid user info from Google")
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=401, detail=f"Google auth failed: {str(e)}")
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update user info if changed
        user.name = name
        user.avatar_url = avatar_url
        await db.commit()
    
    # Create session token
    session_token = create_session_token(user.id)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400 * 7  # 7 days
    )
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url
        ),
        session_token=session_token
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout the current user.
    
    Clears the session cookie.
    """
    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    session_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current authenticated user.
    
    Returns user info if the session is valid.
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = verify_session_token(session_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url
    )
