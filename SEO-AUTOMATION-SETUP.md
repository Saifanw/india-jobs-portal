# Automatic Job SEO Setup

Excel → Bulk Upload remains unchanged. Approved, non-expired Firebase jobs are automatically generated as crawlable static pages under /jobs/ and included in the sitemap.

One-time setup:
1. Create a Google service-account JSON key for the india-jobs-portal Firebase project with read access to the jobs collection.
2. GitHub → Settings → Secrets and variables → Actions → New repository secret.
3. Name: GOOGLE_SERVICE_ACCOUNT_JSON. Paste the full JSON. Never put it in website files.
4. Enable Google Indexing API if you want automatic URL notifications and grant the service account the required Search Console access.
5. Keep GitHub Pages publishing from the branch containing these generated files.

After setup, use Excel → Bulk Private Job Import as before. The workflow runs hourly and can also be started manually from Actions → Generate SEO Job Pages.

Each approved job gets a permanent URL, SEO title/description, canonical URL, JobPosting JSON-LD, sitemap entry and internal link. Expired jobs are removed from the generated active set. Google indexing is not guaranteed; this makes the technical SEO signals scalable.
