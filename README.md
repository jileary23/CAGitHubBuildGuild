# CA Build Guild

A public, single-page site for the **California State Government GitHub Copilot Build Guild** — a monthly community of practice where CA state teams learn, share, and build with GitHub Copilot.

Modeled after the [Ohio Build Guild](https://aka.ms/ohiobuildguild) site, and restyled to match the official **CA GitHub Build Guild Monthly Series** deck's dark, aurora-themed GitHub Copilot brand look.

🔗 Live: **aka.ms/CAGitHubBuildGuild** _(short URL redirect to be configured by the Microsoft short-link admin — see below)_

## What's on the site

- **Hero** — mission tagline, "Learn. Share. Build.", featured speakers, register CTA.
- **Why teams join** — four value props (Statewide Community, Real-World Impact, Peer Learning, Microsoft & GitHub Support).
- **Sessions & notes** — the full session roadmap (Sept 2026 – June 2027) with a filterable/searchable grid (All / Past / Upcoming), plus a "suggest a topic" card. The Sept 16 launch session includes full AI-generated meeting notes and a link to the recap PDF.
- **Featured team** — Kenedy Thorne, Jill Ranasinghe, and Jason Cook.
- **Light/dark theme toggle** — dark aurora theme is the default; choice persists via `localStorage`.

## Structure

```
index.html          # entire site (HTML + CSS + JS, no build step)
assets/             # speaker photos, session recap PDF, brand/theme graphics
```

No build tooling, frameworks, or dependencies — it's a static HTML file you can open directly or host anywhere (GitHub Pages, Azure Static Web Apps, etc.).

## Updating content

- **New session**: duplicate a `.session-card` block in the `#sessions` grid in `index.html`, update date/title/description/status (`data-status="past"` or `"upcoming"`).
- **Session notes**: add a new `<section class="notes-panel">` (see the Sept 16 example) and link it from the session card.
- **Team member**: add a card to the `#team` grid and (optionally) the hero speaker row.
- **Photos/logos**: drop files into `assets/` and reference with a relative path.

## Publishing via GitHub Pages

1. Push this repo to GitHub (public).
2. Repo **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` / `(root)`.
3. Site will publish at `https://<org-or-user>.github.io/<repo>/`.
4. Request an `aka.ms/CAGitHubBuildGuild` short-link redirect to that Pages URL from your Microsoft short-link admin (self-service at https://aka.ms if you have access, otherwise via the internal aka.ms admin request process).

## Notes

- The original `.pptx` source decks are excluded from the repo via `.gitignore` (large binaries); the Sept 16 recap is published instead as `assets/agent-quality-token-optimization.pdf`.
- Session dates assume a Sept 2026 launch; adjust freely if your actual schedule differs.
