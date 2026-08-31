---
state: question
origin: requested
priority: 65
complexity: 15
blast-radius: mid
---

# asking — one PRD waiting on a person

This is the waiting-on-you band. The round below is in the shape the view
parses, so the page renders it as picks.

## Questions

### Q1: Where does the cache live?

The lookup is called on every request and the answer rarely changes. A cache
in memory is fastest and gone on restart; a cache on disk survives a restart
and costs a read. Which one?

1. **In memory** — a dict per process, cleared on restart; the first request after a start pays the lookup once (recommended)
2. **On disk** — a JSON file beside the settings, read once at start and rewritten on every change
3. **No cache** — the lookup is cheap enough to run every time, and a cache is a second source of truth
