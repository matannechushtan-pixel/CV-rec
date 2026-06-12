"""
Reads unread job alert emails from Gmail and returns parsed jobs.
Marks emails as read after processing to avoid duplicates.
"""
import base64
import logging
from core.gmail_auth import get_gmail_service
from agents.email_job_parser import extract_jobs_from_email

logger = logging.getLogger(__name__)


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(part: dict) -> tuple[str, str]:
    """Returns (html_body, text_body) from a message part."""
    html, text = "", ""
    mime = part.get("mimeType", "")
    data = part.get("body", {}).get("data", "")

    if data:
        decoded = base64.urlsafe_b64decode(data + "==").decode(
            "utf-8", errors="replace")
        if mime == "text/html":
            html = decoded
        elif mime == "text/plain":
            text = decoded

    # Recurse into multipart
    for sub in part.get("parts", []):
        h2, t2 = _decode_body(sub)
        html = html or h2
        text = text or t2

    return html, text


async def fetch_and_parse_job_emails(
    max_emails: int = 50,
) -> list[dict]:
    """
    Fetch unread job alert emails from Gmail.
    Parse each one with Claude and return all extracted jobs.
    Marks processed emails as read.
    """
    try:
        service = get_gmail_service()
    except FileNotFoundError as e:
        logger.error("Gmail not configured: %s", e)
        return []

    # Search for unread emails likely to be job alerts
    # Broad query catches all job boards
    query = (
        "is:unread ("
        "subject:משרה OR subject:עבודה OR subject:job OR "
        "subject:jobs OR subject:vacancy OR subject:hiring OR "
        "subject:career OR subject:איתור OR subject:משרות"
        ")"
    )

    try:
        result = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_emails,
        ).execute()
    except Exception as e:
        logger.error("Gmail list error: %s", e)
        return []

    messages = result.get("messages", [])
    logger.info("Found %d unread job emails", len(messages))

    all_jobs  = []
    read_ids  = []   # emails to mark as read after processing

    for msg_ref in messages:
        try:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full",
            ).execute()

            headers  = msg["payload"].get("headers", [])
            sender   = _get_header(headers, "From")
            subject  = _get_header(headers, "Subject")
            html, text = _decode_body(msg["payload"])

            if not html and not text:
                continue

            jobs = await extract_jobs_from_email(
                sender=sender,
                subject=subject,
                body_html=html,
                body_text=text,
            )

            all_jobs.extend(jobs)
            read_ids.append(msg_ref["id"])

        except Exception as e:
            logger.warning("Error processing email %s: %s",
                           msg_ref["id"], e)
            continue

    # Mark all processed emails as read
    if read_ids:
        try:
            service.users().messages().batchModify(
                userId="me",
                body={
                    "ids":            read_ids,
                    "removeLabelIds": ["UNREAD"],
                },
            ).execute()
            logger.info("Marked %d emails as read", len(read_ids))
        except Exception as e:
            logger.warning("Failed to mark emails as read: %s", e)

    return all_jobs
