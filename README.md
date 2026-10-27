# CA GitHub Build Guild

Static community site hosted on GitHub Pages.

## Automatically updated dev community section

The Pages workflow refreshes the six newest matching articles on each push to
`main`, on manual runs, and daily at 14:23 UTC (GitHub schedules can be delayed).
Merge these changes into `main` to enable it; the repository must already use
GitHub Actions as its Pages publishing source. No mailbox access, API keys,
database, or additional Python packages are needed.

Sources:
- [Microsoft for Developers](https://devblogs.microsoft.com/feed/)
- [The GitHub Blog](https://github.blog/feed/)
- [Microsoft Foundry Blog](https://devblogs.microsoft.com/foundry/feed/)

`scripts\update_community.py` matches titles and categories for GitHub Copilot,
developer agents, VS Code, developer tooling, and Microsoft Foundry (including
the Azure AI Foundry name). The dedicated Foundry feed also supplies
Foundry ecosystem articles. Generic "Copilot" is not a match. Microsoft
365/M365/Office 365 articles are excluded unless the metadata explicitly names
GitHub Copilot or Foundry; generic agent mentions are not enough.
This is a topic-filtered blog feed, not a reproduction of Microsoft.Source's
editorial selections.

The generator deduplicates canonical article links, sorts by publication date,
and replaces only the marked community region in `index.html`. Cards contain
linked titles, topics, publishers, and dates, not copied article bodies. Feed
content is escaped and article URLs are restricted to official HTTPS blog hosts.
The browser receives static HTML, so the section works without JavaScript or
cross-origin RSS requests.

The workflow generates the page in its deployment artifact, without committing
daily changes. If a feed cannot be fetched or parsed, or no articles match, the
job fails before deploying and the last successfully deployed site stays live.
The section shows the last successful refresh time; check the **Deploy GitHub
Pages** Actions run for failures. The checked-in page is a starter snapshot,
not a record of daily deployments. Only `index.html` and `assets` are published.

To refresh the local snapshot and run the offline tests:

```powershell
python scripts\update_community.py
python -m unittest discover -s tests
```

Preview with `python -m http.server 8000`, then open `http://localhost:8000`.
To adjust sources or topic matching, edit `FEEDS` or `topics_for` in the
generator and update the regression cases in `tests\test_community.py`.