
"""
Users Router for MINI-RAG Backend

Provides endpoints for user management, including listing users, updating profiles, and filtering by role or status.
All user data is stored and queried from Supabase.
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional
from uuid import uuid4

from models import UserUpdate
from database import get_supabase, SUPABASE_URL
from routers.auth import get_current_user
from core.rbac import require_roles, require_self_or_roles

router = APIRouter()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024


# ---------------------------------------------------------------------------
# List users
# ---------------------------------------------------------------------------

@router.get("/", response_model=list)
async def get_all_users(
    role: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "teacher")),
):
    try:
        sb = get_supabase()
        q = sb.table("users").select("id, name, institution_id, email, role, avatar, profile_image_url, status, created_at")
        if role:
            q = q.eq("role", role)
        if status:
            q = q.eq("status", status)
        resp = q.order("created_at", desc=True).execute()
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students")
async def get_students(current_user: dict = Depends(require_roles("admin", "teacher", "student"))):
    try:
        sb = get_supabase()
        resp = sb.table("users").select("id, name, institution_id, email, avatar, profile_image_url, status").eq("role", "student").execute()
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teachers")
async def get_teachers(current_user: dict = Depends(require_roles("admin", "teacher", "student"))):
    try:
        sb = get_supabase()
        resp = sb.table("users").select("id, name, institution_id, email, avatar, profile_image_url, status").eq("role", "teacher").execute()
        return resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_user_stats(current_user: dict = Depends(require_roles("admin"))):
    try:
        sb = get_supabase()
        all_users = sb.table("users").select("id, role, status").execute().data or []
        total = len(all_users)
        students = sum(1 for u in all_users if u["role"] == "student")
        teachers = sum(1 for u in all_users if u["role"] == "teacher")
        admins = sum(1 for u in all_users if u["role"] == "admin")
        active = sum(1 for u in all_users if u.get("status") == "active")
        return {
            "total_users": total,
            "students": students,
            "teachers": teachers,
            "admins": admins,
            "active_users": active,
            "inactive_users": total - active,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------

@router.get("/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/{user_id}/profile-image")
async def upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    require_self_or_roles("admin")(current_user, user_id)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type. Use JPG, PNG, or WEBP.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > MAX_PROFILE_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image size must be 5MB or less")

    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL is not configured")

    try:
        sb = get_supabase()

        try:
            sb.storage.get_bucket("avatars")
        except Exception:
            sb.storage.create_bucket("avatars", {"public": True})

        extension = ALLOWED_IMAGE_TYPES[file.content_type]
        storage_path = f"users/{user_id}/{uuid4().hex}.{extension}"
        sb.storage.from_("avatars").upload(
            storage_path,
            file=content,
            file_options={"content-type": file.content_type},
        )

        public_url = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/public/avatars/{storage_path}"
        updated = sb.table("users").update({"profile_image_url": public_url}).eq("id", user_id).execute()
        if not updated.data:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "message": "Profile image uploaded successfully",
            "profile_image_url": public_url,
            "user": updated.data[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Single user
# ---------------------------------------------------------------------------

@router.get("/{user_id}")
async def get_user(user_id: int, current_user: dict = Depends(require_roles("admin", "teacher", "student"))):
    try:
        sb = get_supabase()
        resp = sb.table("users").select("id, name, institution_id, email, role, avatar, profile_image_url, status, created_at").eq("id", user_id).limit(1).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="User not found")
        return resp.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Update user
# ---------------------------------------------------------------------------

@router.patch("/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    require_self_or_roles("admin")(current_user, user_id)
    is_admin = current_user.get("role") == "admin"
    if user_update.role and not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can change roles")
    try:
        sb = get_supabase()
        update_data = {k: (v.value if hasattr(v, "value") else v) for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Nothing to update")
        resp = sb.table("users").update(update_data).eq("id", user_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User updated successfully", "user": resp.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}/role")
async def change_user_role(user_id: int, role_data: dict, current_user: dict = Depends(require_roles("admin"))):
    new_role = role_data.get("role")
    if new_role not in ["student", "teacher", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    try:
        sb = get_supabase()
        resp = sb.table("users").update({"role": new_role}).eq("id", user_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="User not found")
        u = resp.data[0]
        return {"message": f"Role changed to {new_role}", "user": {"id": u["id"], "name": u["name"], "role": u["role"]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Delete user
# ---------------------------------------------------------------------------

@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_roles("admin"))):
    if current_user.get("id") == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    try:
        sb = get_supabase()
        resp = sb.table("users").delete().eq("id", user_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
