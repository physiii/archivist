"""GitHub API integration for Archivist.

Provides journal activity, focus data, integration health checks,
and content fetching for vector-store indexing.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ── Configuration ────────────────────────────────────────────────────────

GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
GITHUB_API_BASE = "https://api.github.com"

_GITHUB_CACHE_DIR = Path(os.getenv(
    "ARCHIVIST_GITHUB_CACHE_DIR",
    "~/.config/archivist/github-cache",
)).expanduser()

_REQUEST_TIMEOUT = 20  # seconds per API call

log = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ── Cache helpers ────────────────────────────────────────────────────────

def _cache_key(name: str) -> Path:
    _GITHUB_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = hashlib.sha256(name.encode()).hexdigest()[:16]
    return _GITHUB_CACHE_DIR / f"{slug}.json"


def _cache_get(name: str, max_age_s: float) -> object | None:
    path = _cache_key(name)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data.get("_ts", 0) < max_age_s:
            return data.get("payload")
    except Exception:
        pass
    return None


def _cache_put(name: str, payload: object) -> None:
    path = _cache_key(name)
    try:
        path.write_text(json.dumps({"_ts": time.time(), "payload": payload}), encoding="utf-8")
    except Exception:
        pass


# ── Display timezone (reuse Archivist's setting) ─────────────────────────

def _display_tz():
    """Return the configured display timezone, falling back to UTC."""
    tz_name = os.getenv("ARCHIVIST_DISPLAY_TIMEZONE", "").strip()
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(tz_name)
        except Exception:
            pass
    return timezone.utc


# ── Token health check ──────────────────────────────────────────────────

def check_github_token() -> dict:
    """Verify the GitHub token and return connection status."""
    if not GITHUB_TOKEN:
        return {"connected": False, "error": "GITHUB_TOKEN not set"}

    cached = _cache_get("token_check", max_age_s=300)
    if cached is not None:
        return cached

    try:
        resp = requests.get(f"{GITHUB_API_BASE}/user", headers=_headers(), timeout=_REQUEST_TIMEOUT)
        if resp.status_code == 401:
            result = {"connected": False, "error": "Token expired or invalid"}
            _cache_put("token_check", result)
            return result
        resp.raise_for_status()
        user = resp.json()
        result = {
            "connected": True,
            "login": user.get("login", ""),
            "name": user.get("name", ""),
            "avatar_url": user.get("avatar_url", ""),
            "expires_at": resp.headers.get("github-authentication-token-expiration", ""),
            "scopes": resp.headers.get("x-oauth-scopes", ""),
            "rate_limit": int(resp.headers.get("x-ratelimit-limit", 0)),
            "rate_remaining": int(resp.headers.get("x-ratelimit-remaining", 0)),
            "error": None,
        }
        # Auto-detect username if not configured
        global GITHUB_USERNAME
        if not GITHUB_USERNAME and result["login"]:
            GITHUB_USERNAME = result["login"]
        _cache_put("token_check", result)
        return result
    except requests.RequestException as exc:
        result = {"connected": False, "error": str(exc)[:200]}
        _cache_put("token_check", result)
        return result


# ── Ensure username is available ─────────────────────────────────────────

def _ensure_username() -> str:
    """Return the GitHub username, auto-detecting if needed."""
    global GITHUB_USERNAME
    if GITHUB_USERNAME:
        return GITHUB_USERNAME
    status = check_github_token()
    return status.get("login", "") or GITHUB_USERNAME


# ── Events API (activity feed) ──────────────────────────────────────────

def fetch_github_events(username: str | None = None, max_pages: int = 10) -> list[dict]:
    """Fetch recent public+private events for the authenticated user."""
    if not GITHUB_TOKEN:
        return []
    username = username or _ensure_username()
    if not username:
        return []

    cache_name = f"events:{username}"
    cached = _cache_get(cache_name, max_age_s=1800)
    if cached is not None:
        return cached

    all_events: list[dict] = []
    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/users/{username}/events",
                headers=_headers(),
                params={"per_page": 100, "page": page},
                timeout=_REQUEST_TIMEOUT,
            )
            if resp.status_code != 200:
                break
            events = resp.json()
            if not events:
                break
            all_events.extend(events)
        except requests.RequestException:
            break

    _cache_put(cache_name, all_events)
    return all_events


# ── Journal: activity bucketed by day ────────────────────────────────────

_EVENT_TYPE_MAP = {
    "PushEvent": "push",
    "PullRequestEvent": "pr",
    "PullRequestReviewEvent": "review",
    "PullRequestReviewCommentEvent": "review",
    "IssuesEvent": "issue",
    "IssueCommentEvent": "issue",
    "CreateEvent": "create",
    "DeleteEvent": "delete",
    "ReleaseEvent": "release",
    "ForkEvent": "fork",
    "WatchEvent": "star",
}


def _parse_event(event: dict) -> dict | None:
    """Normalize a GitHub event into a journal activity record."""
    etype = event.get("type", "")
    mapped = _EVENT_TYPE_MAP.get(etype)
    if not mapped:
        return None

    repo_name = (event.get("repo") or {}).get("name", "")
    created_at = event.get("created_at", "")
    payload = event.get("payload") or {}

    title = ""
    number = None
    action = payload.get("action", "")
    url = ""

    if mapped == "push":
        commits = payload.get("commits") or []
        title = commits[0].get("message", "").split("\n", 1)[0] if commits else "Push"
        count = payload.get("size", len(commits))
        if count > 1:
            title = f"{count} commits: {title}"
    elif mapped == "pr":
        pr = payload.get("pull_request") or {}
        title = pr.get("title", "")
        number = pr.get("number")
        url = pr.get("html_url", "")
    elif mapped == "review":
        pr = payload.get("pull_request") or {}
        title = f"Review on: {pr.get('title', '')}"
        number = pr.get("number")
        url = pr.get("html_url", "")
    elif mapped == "issue":
        issue = payload.get("issue") or {}
        title = issue.get("title", "")
        number = issue.get("number")
        url = issue.get("html_url", "")
    elif mapped == "release":
        release = payload.get("release") or {}
        title = release.get("name") or release.get("tag_name", "")
        url = release.get("html_url", "")
    elif mapped == "create":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref", "")
        title = f"Created {ref_type}: {ref}" if ref else f"Created {ref_type}"
    elif mapped == "fork":
        forkee = payload.get("forkee") or {}
        title = f"Forked to {forkee.get('full_name', '')}"

    return {
        "type": mapped,
        "repo": repo_name,
        "title": title.strip(),
        "number": number,
        "action": action,
        "url": url,
        "created_at": created_at,
    }


def collect_github_activity_for_days(since_days: int = 0) -> dict[str, list[dict]]:
    """Collect GitHub activity bucketed by day for the journal.

    When *since_days* is 0 (default) fetch all available history —
    the Events API covers the last ~90 days, and the Search API
    supplements with complete PR/issue history back to account creation.

    Returns ``{day_iso: [activity_record, ...]}``.
    """
    if not GITHUB_TOKEN:
        return {}

    cache_name = f"journal_activity:{since_days}"
    cached = _cache_get(cache_name, max_age_s=1800)
    if cached is not None:
        return cached

    cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)) if since_days else None
    tz = _display_tz()
    events = fetch_github_events()

    activity: dict[str, list[dict]] = {}
    seen: set[str] = set()  # deduplicate

    for event in events:
        created = event.get("created_at", "")
        if not created:
            continue
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            continue
        if cutoff and dt < cutoff:
            continue

        record = _parse_event(event)
        if not record:
            continue

        # Deduplicate by (type, repo, number/title, day)
        day = dt.astimezone(tz).date().isoformat()
        dedup_key = f"{record['type']}:{record['repo']}:{record.get('number') or record['title']}:{day}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        activity.setdefault(day, []).append(record)

    # Supplement with historical PR/issue data from the Search API
    # (Events API only covers last ~90 days).
    try:
        _merge_search_history(activity, seen, tz, cutoff)
    except Exception:
        log.exception("Failed to supplement journal with GitHub search history")

    _cache_put(cache_name, activity)
    return activity


def _merge_search_history(
    activity: dict[str, list[dict]],
    seen: set[str],
    tz,
    cutoff: datetime | None,
) -> None:
    """Fetch historical PRs/issues via the Search API and merge into activity."""
    username = _ensure_username()
    if not username:
        return

    def _search_items(query: str, max_pages: int = 10) -> list[dict]:
        items: list[dict] = []
        for page in range(1, max_pages + 1):
            try:
                resp = requests.get(
                    f"{GITHUB_API_BASE}/search/issues",
                    headers=_headers(),
                    params={"q": query, "per_page": 100, "sort": "updated", "order": "desc", "page": page},
                    timeout=_REQUEST_TIMEOUT,
                )
                if resp.status_code == 403:
                    # Rate limited
                    log.warning("GitHub search rate limited at page %d", page)
                    break
                if resp.status_code != 200:
                    break
                page_items = resp.json().get("items", [])
                if not page_items:
                    break
                items.extend(page_items)
            except requests.RequestException:
                break
        return items

    # Fetch PRs authored by user
    for item in _search_items(f"author:{username} type:pr"):
        _add_search_item(item, "pr", activity, seen, tz, cutoff)

    # Fetch issues authored by user
    for item in _search_items(f"author:{username} type:issue"):
        _add_search_item(item, "issue", activity, seen, tz, cutoff)

    # Fetch PRs where user was requested as reviewer
    for item in _search_items(f"reviewed-by:{username} type:pr", max_pages=5):
        _add_search_item(item, "review", activity, seen, tz, cutoff)


def _add_search_item(
    item: dict,
    item_type: str,
    activity: dict[str, list[dict]],
    seen: set[str],
    tz,
    cutoff: datetime | None,
) -> None:
    """Parse a Search API item and add to activity if not already seen."""
    created = item.get("created_at", "")
    if not created:
        return
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except Exception:
        return
    if cutoff and dt < cutoff:
        return

    repo_url = item.get("repository_url") or ""
    repo = repo_url.rsplit("/repos/", 1)[-1] if "/repos/" in repo_url else ""
    number = item.get("number")
    title = item.get("title", "").strip()
    url = item.get("html_url", "")

    day = dt.astimezone(tz).date().isoformat()
    dedup_key = f"{item_type}:{repo}:{number or title}:{day}"
    if dedup_key in seen:
        return
    seen.add(dedup_key)

    record = {
        "type": item_type,
        "repo": repo,
        "title": f"Review on: {title}" if item_type == "review" else title,
        "number": number,
        "action": item.get("state", ""),
        "url": url,
        "created_at": created,
    }
    activity.setdefault(day, []).append(record)


# ── Focus: current open work ─────────────────────────────────────────────

def get_github_focus_data(username: str | None = None) -> dict:
    """Fetch open PRs, review requests, and assigned issues for Focus page."""
    if not GITHUB_TOKEN:
        return {"open_prs": [], "review_requests": [], "assigned_issues": []}

    username = username or _ensure_username()
    if not username:
        return {"open_prs": [], "review_requests": [], "assigned_issues": []}

    cache_name = f"focus:{username}"
    cached = _cache_get(cache_name, max_age_s=300)
    if cached is not None:
        return cached

    result: dict[str, list] = {"open_prs": [], "review_requests": [], "assigned_issues": []}

    def _search(query: str) -> list[dict]:
        items = []
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/search/issues",
                headers=_headers(),
                params={"q": query, "per_page": 30, "sort": "updated", "order": "desc"},
                timeout=_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    items.append({
                        "number": item.get("number"),
                        "title": item.get("title", ""),
                        "repo": (item.get("repository_url") or "").rsplit("/repos/", 1)[-1] if item.get("repository_url") else "",
                        "state": item.get("state", ""),
                        "url": item.get("html_url", ""),
                        "updated_at": item.get("updated_at", ""),
                        "labels": [l.get("name", "") for l in (item.get("labels") or [])],
                    })
        except requests.RequestException as exc:
            log.warning("GitHub search failed for %r: %s", query, exc)
        return items

    result["open_prs"] = _search(f"author:{username} type:pr is:open")
    result["review_requests"] = _search(f"review-requested:{username} type:pr is:open")
    result["assigned_issues"] = _search(f"assignee:{username} is:open")

    _cache_put(cache_name, result)
    return result


# ── Vector store: full content for indexing ───────────────────────────────

def fetch_github_content_for_indexing(
    username: str | None = None,
    since_days: int = 90,
    max_repos: int = 50,
) -> list[dict]:
    """Fetch issue/PR bodies and comments for vector-store indexing.

    Returns a list of content records ready for chunking and embedding.
    """
    if not GITHUB_TOKEN:
        return []

    username = username or _ensure_username()
    if not username:
        return []

    cache_name = f"indexing_content:{username}:{since_days}"
    cached = _cache_get(cache_name, max_age_s=7200)
    if cached is not None:
        return cached

    since_date = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    content: list[dict] = []

    # Get repos the user contributes to (owned + org member)
    repos: list[str] = []
    for affiliation in ("owner", "organization_member"):
        page = 1
        while page <= 5 and len(repos) < max_repos:
            try:
                resp = requests.get(
                    f"{GITHUB_API_BASE}/user/repos",
                    headers=_headers(),
                    params={"affiliation": affiliation, "sort": "pushed", "per_page": 30, "page": page},
                    timeout=_REQUEST_TIMEOUT,
                )
                if resp.status_code != 200:
                    break
                page_repos = resp.json()
                if not page_repos:
                    break
                for r in page_repos:
                    pushed = r.get("pushed_at", "")
                    if pushed and pushed >= since_date:
                        repos.append(r.get("full_name", ""))
                page += 1
            except requests.RequestException:
                break

    seen_ids: set[str] = set()

    for repo_full in repos[:max_repos]:
        # Fetch issues (includes PRs on GitHub API)
        try:
            resp = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_full}/issues",
                headers=_headers(),
                params={"state": "all", "since": since_date, "per_page": 30, "sort": "updated"},
                timeout=_REQUEST_TIMEOUT,
            )
            if resp.status_code != 200:
                continue
            for item in resp.json():
                is_pr = bool(item.get("pull_request"))
                source_id = f"{repo_full}#{item['number']}"
                if source_id in seen_ids:
                    continue
                seen_ids.add(source_id)

                body = str(item.get("body") or "").strip()
                title = str(item.get("title") or "").strip()

                # Fetch top comments (up to 10)
                comments: list[str] = []
                comments_url = item.get("comments_url", "")
                if comments_url and item.get("comments", 0) > 0:
                    try:
                        cresp = requests.get(
                            comments_url,
                            headers=_headers(),
                            params={"per_page": 10},
                            timeout=_REQUEST_TIMEOUT,
                        )
                        if cresp.status_code == 200:
                            for c in cresp.json():
                                cbody = str(c.get("body") or "").strip()
                                if cbody:
                                    cauthor = (c.get("user") or {}).get("login", "")
                                    comments.append(f"[{cauthor}]: {cbody}")
                    except requests.RequestException:
                        pass

                content.append({
                    "source_type": "github",
                    "doc_type": "github_pr" if is_pr else "github_issue",
                    "source_id": source_id,
                    "title": title,
                    "body": body,
                    "comments": comments,
                    "url": item.get("html_url", ""),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                    "repo": repo_full,
                    "author": (item.get("user") or {}).get("login", ""),
                    "labels": [l.get("name", "") for l in (item.get("labels") or [])],
                    "state": item.get("state", ""),
                })
        except requests.RequestException:
            continue

    _cache_put(cache_name, content)
    log.info("Fetched %d GitHub content items for indexing across %d repos", len(content), len(repos))
    return content
