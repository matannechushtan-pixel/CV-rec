from supabase import create_client, Client

from core.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

CV_FILES_BUCKET = "cv-files"

_bucket_ready = False


def _ensure_bucket() -> None:
    global _bucket_ready
    if _bucket_ready:
        return
    try:
        buckets = supabase.storage.list_buckets()
        names = {b.name for b in buckets}
        if CV_FILES_BUCKET not in names:
            supabase.storage.create_bucket(CV_FILES_BUCKET, options={"public": True})
    except Exception:
        pass
    _bucket_ready = True


def upload_cv_pdf(path: str, content: bytes) -> str:
    """Upload a generated CV PDF to Supabase storage and return its public URL."""
    _ensure_bucket()
    supabase.storage.from_(CV_FILES_BUCKET).upload(
        path,
        content,
        {"content-type": "application/pdf", "upsert": "true"},
    )
    return supabase.storage.from_(CV_FILES_BUCKET).get_public_url(path)
