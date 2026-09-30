#!/usr/bin/env python3
import os, re, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
from html import escape

import firebase_admin
from firebase_admin import credentials, firestore

ROOT = Path(__file__).resolve().parents[2]
JOBS = ROOT / "jobs"
SITEMAPS = ROOT / "sitemaps"
MANIFEST = ROOT / ".seo-job-manifest.json"

BASE = "https://saifanw.github.io/india-jobs-portal"


def slug(v):
    return (
        re.sub(r"[^a-z0-9]+", "-", str(v or "job").lower())
        .strip("-")[:70]
        or "job"
    )


def path(jid, j):
    return f"jobs/{slug(j.get('title'))}-{slug(j.get('company'))}-{jid}/"


def date(v):
    if not v:
        return None

    if hasattr(v, "to_datetime"):
        try:
            return v.to_datetime()
        except Exception:
            pass

    if isinstance(v, datetime):
        return v

    for f in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(
                str(v).strip(), f
            ).replace(tzinfo=timezone.utc)
        except Exception:
            pass

    return None


def iso(v):
    d = date(v)
    return d.date().isoformat() if d else None


def clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def make_page(j, url):
    title = clean(j.get("title")) or "Job Vacancy"
    company = clean(j.get("company")) or "Employer"
    loc = clean(j.get("location")) or "India"
    salary = clean(j.get("salary")) or "Not specified"
    exp = clean(j.get("experience")) or "Any Experience"
    typ = clean(j.get("type") or j.get("jobType")) or "Full Time"
    qual = clean(j.get("qualification")) or "Not specified"

    description = (
        clean(j.get("description"))
        or "Job details are available on this page."
    )

    notes = clean(j.get("notes"))
    apply = clean(j.get("apply") or j.get("applyLink"))

    posted = (
        iso(j.get("createdAt") or j.get("datePosted"))
        or datetime.now(timezone.utc).date().isoformat()
    )

    deadline = iso(j.get("deadline") or j.get("lastDate"))

    schema = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": title,
        "description": description,
        "datePosted": posted,
        "hiringOrganization": {
            "@type": "Organization",
            "name": company
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": loc,
                "addressCountry": "IN"
            }
        },
        "employmentType": typ.upper().replace(" ", "_"),
        "url": url
    }

    if deadline:
        schema["validThrough"] = deadline

    if re.match(r"^https?://", apply, re.I):
        apply_html = (
            '<a class="btn" href="'
            + escape(apply, quote=True)
            + '" target="_blank" rel="noopener noreferrer nofollow">'
            "Apply Now ↗</a>"
        )
    else:
        apply_html = (
            "<p><b>Official application link is not available. "
            "Verify the vacancy notice before applying.</b></p>"
        )

    notes_html = ""

    if notes:
        notes_html = (
            "<section><h2>Additional Information</h2>"
            "<p>"
            + escape(notes).replace("\n", "<br>")
            + "</p></section>"
        )

    deadline_html = ""

    if deadline:
        deadline_html = (
            '<span>📅 Deadline: '
            + escape(deadline)
            + "</span>"
        )

    meta = escape(
        (
            title
            + " | "
            + company
            + " | "
            + loc
            + " | "
            + exp
            + " | "
            + salary
        )[:300],
        quote=True
    )

    css = (
        "body{margin:0;font-family:Arial,sans-serif;"
        "background:#f5f7fb;color:#182536}"
        ".wrap{width:min(900px,92%);margin:auto}"
        ".top{background:#102a43;color:#fff;padding:16px 0}"
        ".card{background:#fff;margin:35px 0;padding:28px;"
        "border-radius:18px;border:1px solid #dfe7ef;"
        "box-shadow:0 10px 30px #102a430d}"
        "h1{color:#102a43}"
        ".company{color:#64748b;font-weight:700}"
        ".meta{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}"
        ".meta span{border:1px solid #dfe7ef;padding:8px 10px;"
        "border-radius:8px;font-size:13px}"
        ".btn{display:inline-block;background:#1769e8;color:#fff;"
        "padding:12px 18px;border-radius:9px;text-decoration:none;"
        "font-weight:800}"
        "section{border-top:1px solid #e5ebf1;margin-top:24px;"
        "padding-top:20px}"
        ".note{font-size:12px;color:#64748b}"
        "a{color:#1769e8}"
    )

    html = """<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>TITLE | COMPANY | India Jobs Portal</title>

<meta name="description" content="META">
<meta name="robots" content="index,follow,max-image-preview:large">

<link rel="canonical" href="URL">

<meta property="og:title" content="TITLE | COMPANY">
<meta property="og:description" content="META">
<meta property="og:url" content="URL">

<script type="application/ld+json">
SCHEMA
</script>

<style>CSS</style>
</head>

<body>

<div class="top">
<div class="wrap">
<b>India Jobs Portal</b> • Job Details
</div>
</div>

<main class="wrap">

<article class="card">

<h1>TITLE</h1>

<div class="company">
COMPANY • 📍 LOC
</div>

<div class="meta">
<span>💼 TYPE</span>
<span>👤 EXP</span>
<span>💰 SALARY</span>
<span>🎓 QUAL</span>
DEADLINE
</div>

APPLY

<section>
<h2>Job Description</h2>
<p>DESCRIPTION</p>
</section>

NOTES

<section>
<h2>Job Preparation</h2>
<p>
Prepare relevant skills, aptitude and interview questions
before applying.
</p>

<a href="BASE/career-prep-center.html">
Test &amp; Preparation →
</a>

</section>

<p class="note">
Verify vacancy details and application instructions on the
employer's official source before applying.
</p>

<p>
<a href="BASE/jobs.html">← Browse all jobs</a>
</p>

</article>

</main>

</body>
</html>"""

    vals = {
        "TITLE": escape(title),
        "COMPANY": escape(company),
        "LOC": escape(loc),
        "TYPE": escape(typ),
        "EXP": escape(exp),
        "SALARY": escape(salary),
        "QUAL": escape(qual),
        "DEADLINE": deadline_html,
        "APPLY": apply_html,
        "DESCRIPTION": escape(description).replace("\n", "<br>"),
        "NOTES": notes_html,
        "META": meta,
        "URL": escape(url, quote=True),
        "SCHEMA": json.dumps(schema, ensure_ascii=False),
        "CSS": css,
        "BASE": BASE
    }

    for k, v in vals.items():
        html = html.replace(k, v)

    return html


def main():

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not raw:
        raise SystemExit(
            "Missing GOOGLE_SERVICE_ACCOUNT_JSON secret"
        )

    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(
            credentials.Certificate(json.loads(raw))
        )

    db = firestore.client()

    active = []
    today = datetime.now(timezone.utc).date()

    for d in db.collection("jobs").where(
        "status", "==", "approved"
    ).stream():

        j = d.to_dict()

        dl = date(
            j.get("deadline")
            or j.get("lastDate")
        )

        if dl and dl.date() < today:
            continue

        active.append((d.id, j))

    if JOBS.exists():
        for c in JOBS.iterdir():
            if c.is_dir():
                shutil.rmtree(c)

    JOBS.mkdir(parents=True, exist_ok=True)

    (JOBS / "README.md").write_text(
        "Generated automatically. Do not edit manually.\n"
    )

    manifest = {}
    urls = []

    for jid, j in active:

        rel = path(jid, j)
        url = BASE + "/" + rel

        out = ROOT / rel / "index.html"

        out.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        out.write_text(
            make_page(j, url),
            encoding="utf-8"
        )

        sig = hashlib.sha256(
            json.dumps(
                j,
                default=str,
                sort_keys=True
            ).encode()
        ).hexdigest()

        manifest[jid] = {
            "url": url,
            "hash": sig
        }

        urls.append(
            (
                url,
                j.get("updatedAt")
                or j.get("createdAt")
            )
        )

    static = [
        BASE + "/",
        BASE + "/jobs.html",
        BASE + "/government-jobs.html",
        BASE + "/job-seeker.html",
        BASE + "/post-a-job.html",
        BASE + "/resume-builder.html",
        BASE + "/career-prep-center.html"
    ]

    allu = [(x, None) for x in static] + urls

    if SITEMAPS.exists():
        shutil.rmtree(SITEMAPS)

    SITEMAPS.mkdir(parents=True, exist_ok=True)

    chunks = [
        allu[i:i + 50000]
        for i in range(0, len(allu), 50000)
    ]

    names = []

    for i, ch in enumerate(chunks, 1):

        name = f"sitemap-{i}.xml"
        names.append(name)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for u, last in ch:

            lastmod = iso(last)

            lines.append(
                "  <url><loc>"
                + escape(u)
                + "</loc>"
                + (
                    "<lastmod>"
                    + lastmod
                    + "</lastmod>"
                    if lastmod
                    else ""
                )
                + "</url>"
            )

        lines.append("</urlset>")

        (
            SITEMAPS / name
        ).write_text(
            "\n".join(lines) + "\n"
        )

    if len(names) == 1:

        (
            ROOT / "sitemap.xml"
        ).write_text(
            (SITEMAPS / names[0]).read_text()
        )

    else:

        (
            ROOT / "sitemap.xml"
        ).write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(
                f"<sitemap><loc>{BASE}/sitemaps/{n}</loc></sitemap>"
                for n in names
            )
            + "\n</sitemapindex>\n"
        )

    old = (
        json.loads(MANIFEST.read_text())
        if MANIFEST.exists()
        else {}
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True
        )
    )

    changed = [
        v["url"]
        for jid, v in manifest.items()
        if old.get(jid, {}).get("hash") != v["hash"]
    ]

    removed = [
        v["url"]
        for jid, v in old.items()
        if jid not in manifest
    ]

    (
        ROOT / ".seo-changes.json"
    ).write_text(
        json.dumps(
            {
                "changed": changed[:200],
                "removed": removed[:200],
                "active_count": len(active)
            },
            indent=2
        )
    )

    print(
        "Generated",
        len(active),
        "job pages"
    )


if __name__ == "__main__":
    main()
