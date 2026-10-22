# Webring and path security

This independent text-only host fixture exercises the public build CLI and default
templates together. Parameterized tests select each owner-controlled text mode,
both webring layouts, failure policies, and invalid tag input in a temporary copy.
The external data contains harmless script markers; tests inspect generated HTML
without executing scripts. The template's news-post HTML must remain unaffected
by webring-scoped autoescaping.

Run `python -m pytest tests/test_webring_security.py`. No external endpoint,
credentials, or golden refresh is required. The complete source fixture lives
here; tests modify only their temporary staged copy.
