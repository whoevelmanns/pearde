# Jira sync

Optional, per board. Mirrors a PRD's `state` onto its Jira issue's status, so
the board and the tracker teammates already watch never disagree about where
work stands.

## Enabling it

Two things, both required, or `jira_sync.py` does nothing:

1. `jira-sync: on` in `prds/settings.md` — an unknown key elsewhere, read
   only here, same as any other board setting.
2. `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` in the environment. Create
   the token at `https://id.atlassian.com/manage-profile/security/api-tokens`.
   Set the three as **user environment variables** (`setx` on Windows, a
   shell profile export elsewhere) — never pasted into a PRD, a commit, or a
   chat transcript. A **new** shell/session is required after `setx`; the one
   that ran it does not see its own write.

Either missing: `sync` prints one line to stderr and exits 0. A board with no
Jira behind it, or a session before the token is exported, is unaffected —
never treat that line as failure.

## The issue key

Read off the PRD directory's own name: a leading `<PROJECT>-<number>`,
case-folded to upper — `ab-621-listen-modernisieren` → `AB-621`,
`hama-1397-ladeeinheiten-versandart-leer` → `HAMA-1397`. A PRD without that
shape (`datumsfilter-bis-naechster-tag`) is skipped, one line, exit 0 — most
boards mix ticketed and non-ticketed PRDs on purpose, and that is not an
error.

## The workflow graph, not a fixed table

Jira workflows differ per site and per project — nothing about status names
or transitions is hardcoded in the script. `jira_sync.py discover
<PROJECT-KEY>` reads the project's real workflow (workflow scheme → workflow
definition → transitions, cross-referenced against
`/project/<KEY>/statuses` for the **display** names a project may have
renamed — the workflow definition itself often still carries the generic
originals, e.g. `Preparing` where the project shows `Vorbereitung`) and
caches it as `prds/.jira-graph-<PROJECT>.json`. `sync` discovers lazily the
first time a project is seen. Re-run `discover` (or delete the cache file)
after editing the workflow in Jira.

`prds/.jira-graph-*.json` is machine-local and regenerable — gitignore it
beside `.plan.json`.

## State → status

| pearde state | Jira action |
|---|---|
| `open` | **only ever un-pauses** — if the issue is at an `… on hold` status, takes the `Resume…` transition back to the active status it paused from. Otherwise **no forced move**, including no move to a nominal "backlog" status: an issue already `Selected` or further was placed there on purpose (by a person, or an earlier sync), and pearde's own `open` firing again — after `refine`, after a question answered — is not grounds to undo that. Silent no-op, no comment. |
| `analyzing` | advance the graph toward "Preparing"'s display name (`Vorbereitung` here) |
| `refine` | pause the current phase if a single `… on hold` transition is available from here (e.g. `Preparing` → `Preparing on hold`); always comments the proposed split |
| `specced` | advance toward "Preparing Done" |
| `claimed` | advance toward "Implementing" |
| `question` / `blocked` | pause the current phase, same as `refine`; always comments the question/blocker text |
| `done` | advance toward "Done"'s display name (`Fertig` here) |
| `failed` | advance toward "Reopened"'s display name (`Erneut geöffnet` here); always comments the failure reason |

"Advance the graph toward X" is a breadth-first search from the issue's
**current** status to the target's display name, executed one live
transition per hop — never a single hardcoded transition id, because the
site's ids are not portable and a workflow edit would silently break a
cached one. Already at the target: no-op. **No path found: nothing is
forced.** Most workflows do not lead backward, and an issue found further
along than pearde expected (worked directly in Jira, or simply ahead of
where pearde's own state machine has caught up) is not this script's call to
walk back — it comments what pearde tried and leaves the status alone.

**Why `open` never targets a fixed status**, unlike every other row: a
Kanban-style workflow's "ready to start" status (`Selected` here) is
typically a dead end coming back the other way — reachable from the true
backlog status, but not reachable again once the issue has moved past it.
Treating pearde's `open` as "put the issue in the backlog status" would
therefore fight a human who deliberately re-selected work, and repeatedly
fail (silently, since **the fail case for `open` is intentionally not a
mismatch worth a comment** — see next paragraph) once anything has moved on.
Un-pausing is the one `open`-triggered move that is always safe, because it
only ever returns the issue to a status it was already at.

## Comments — kept rare on purpose

A plain successful transition is already visible in Jira's own activity log
— a comment repeating "status changed" is noise, not information. A comment
is posted only when the status change alone would not tell the story:

- `refine` / `question` / `blocked` / `failed` — always, carrying the
  reason/question/split text pearde already wrote into the PRD.
- a `note` was passed to `sync` explicitly.
- the graph search found no forward path — flags a real mismatch between
  what pearde expected and where the issue actually is, worth a human's
  look. (The `open` "already past backlog" case is excluded from this: see
  above — that is the expected, common resting state, not a mismatch.)

## Calling it

```sh
python3 <skill>/jira_sync.py sync <prd-dir-name> <state> [note...]
python3 <skill>/jira_sync.py discover <PROJECT-KEY>   # (re)cache the graph
python3 <skill>/jira_sync.py check [PROJECT-KEY]      # env + graph reachability
```

Call `sync` from the orchestrator, after writing the same transition to
`prd.md` — same rule as **Commits**: it rides the transition that produced
it, never a separate pass. `<prd-dir-name>` is the PRD's own directory name
(not its full path) — `sync` derives the board via the same cwd-walk every
other script in this skill uses, so run it from inside the repo.

Never a worker's job — same one-writer rule as `state` and commits. The
orchestrator calls it, once, right after the write it mirrors.

## Rückrichtung: Jira als Quelle

Alles oben ist pearde → Jira. Zwei zusätzliche, rein lesende Reports gehen
die andere Richtung: Jira wird beim Scan (Loop-Schritt 1) als weitere Quelle
befragt, nicht nur als Ziel beschrieben. Beide sind report-only — keiner
schreibt einen State, keiner erzwingt einen Übergang. Der Mensch (oder der
Orchestrator, in seinem Namen) bleibt in der Schleife für alles mit echten
Konsequenzen.

### Drift-Erkennung (`jira_sync.py drift`)

Für jede PRD mit ableitbarem Jira-Key (`issue_key()`, wie oben) und einem
`state`, dessen `STATE_TARGET`-Eintrag ein festes Ziel ist — `analyzing`,
`specced`, `claimed`, `done`, `failed` — wird der aktuelle Jira-Status via
`current_status()` abgefragt und mit dem erwarteten verglichen. Abweichung →
eine Zeile:

```
jira_sync: drift <rel> (<KEY>): state <state> expects "<target>", Jira has "<live>"
```

Kein Fund → keine Ausgabe (silent-when-clean, wie `memos.py check`). Nie ein
automatischer PRD-State-Wechsel: viele Jira-Status (Reviewing, Testing,
Deploying) haben keine pearde-Entsprechung, und ein Jira-Status wie "Fertig"
ist für sich kein ausreichender Verify-Nachweis — pearde verlangt für `done`
einen echten Beleg (**Never take a worker's word for a transition**), kein
reines Statusflag von außen.

`open`, `refine`, `question`, `blocked` sind explizit von der Prüfung
ausgenommen — nicht weil `STATE_TARGET` für alle vier `None` trägt (`open`
hat dort tatsächlich einen Eintrag, der aber nur von `sync()`s
Sonderbehandlung nie als hartes Ziel benutzt wird, siehe **Warum `open`
nie ein festes Ziel anpeilt** oben), sondern weil keiner der vier einen
einzelnen erwarteten Status hat: `open` pausiert/entpausiert nur, und
`refine`/`question`/`blocked` landen auf irgendeinem `… on hold`, nicht auf
einem festen Namen. Ein Vergleich dagegen wäre geraten, kein echter Fund.

PRDs ohne ableitbaren Jira-Key: still übersprungen, wie überall sonst in
diesem Skript.

`drift(board)` liest nur das eigene Board (`view/plan.py`'s `scan(board)`,
kein Members-Fan-out) — genau wie `sync()` heute schon nur dort wirkt, wo es
aufgerufen wird.

### Ticket-Import (`jira_sync.py import-new`)

Findet neue "bereit, mir zugewiesen"-Tickets in Jira, die noch keine PRD auf
dem Board haben — und meldet sie, **legt aber selbst keine Dateien unter
`prds/` an.** Titel- und Body-Text aus einer Jira-Beschreibung sinnvoll zu
formulieren ist Content-Arbeit, kein deterministischer API-Call; das Anlegen
bleibt Sache des Orchestrators, exakt wie beim bestehenden "Refine"-Schritt —
hält den One-Writer-Grundsatz für `prds/`-Dateien intakt.

**Projekt-Scope** (`configured_projects(board)`): die Vereinigung aus jedem
`<PROJECT>`-Präfix, der unter einem existierenden PRD-Ordnernamen auftaucht
— rekursiv über das ganze Board, nicht nur `prds/*` flach — plus dem
optionalen, additiven Settings-Key `jira-projects` (Liste oder
Komma-Scalar). Letzterer deckt das Henne-Ei-Problem ab: ein komplett neues
Projekt importieren, bevor überhaupt eine PRD mit dessen Präfix existiert.

**"Bereit, nicht begonnen"** (`selected_status_name(board)`): exakter
Namensabgleich gegen `fields.status.name`, Default `"Selected"`,
konfigurierbar über `jira-selected-status`. **Nicht** `statusCategory` — bei
diesem Jira-Setup (live gegen `/rest/api/3/project/{AB,HAMA}/statuses`
geprüft) trägt `statusCategory: new` neben `Selected` auch `Offen`
(Backlog), jedes `… on hold` und jedes `… done`-Zwischenstand
(`Preparing Done`, `Testing done`, …) sowie `Erneut geöffnet` —
`statusCategory` unterscheidet in diesem Workflow nicht zuverlässig
"bereit, nicht begonnen" von anderen new-artigen Zuständen.

**Zuordnung Ticket → bestehende PRD** (`has_existing_prd`/`_prd_for_key`):
primär derselbe `<PROJECT>-<number>`-Präfix-Abgleich wie `issue_key()`, nur
umgekehrt (existierende PRD-Ordnernamen als Index); Fallback: der Key
(wortgrenzen-genau, case-insensitive) kommt im Body irgendeiner
existierenden PRD vor — fängt eine PRD ohne Präfix im Ordnernamen ab, die
ihren eigenen Key aber im Body nennt. **Bekannte, dokumentierte Lücke**: eine
PRD ohne Präfix im Ordnernamen UND ohne Erwähnung ihres eigenen Keys im Body
(Beispiel zur Speczeit: `ab-621-listen-modernisieren/
sortierung-erhalten-am-absteigend/` für AB-625) wird von keinem der beiden
Signale gefangen — der Import würde sie fälschlich als "ohne PRD" melden.
Ohne ein drittes Signal (z. B. ein Jira-seitiger Remote-Link auf den
PRD-Pfad, den es heute nicht gibt) ist das aus PRD-Board-Daten allein nicht
schließbar. Abgefedert am Review-Punkt statt in der Zuordnungslogik selbst:
siehe Parent-Gruppierung unten — ein Treffer mit Parent zeigt auch dessen
bestehende Geschwister, sodass die Naheliegenheit eines Duplikats vor dem
Anlegen sichtbar wird.

**Parent-Gruppierung**: für jedes Ticket ohne bestehende PRD wird
`fields.parent.key` (falls vorhanden) gegen dieselbe Zuordnungslogik
geprüft. Auflösbar → dessen relativer PRD-Pfad **und** die bereits
existierenden Kinder dieses Pfads werden mitgemeldet — das liefert dem
Orchestrator, was er braucht, um das neue Ticket gruppiert unter dem Parent
statt flach anzulegen (analog zur bestehenden, manuell angelegten Struktur
`prds/ab-621-…/{ab-628-…, ab-630-…}/`), und macht einen möglichen
Nahe-Duplikat-Fall sichtbar. Kein Parent, oder nicht auflösbar:
`parent: none -> flat` — flacher Fallback unter `prds/`, keine Kette von
Vermutungen über mehrere Ebenen.

**Paginierung**: `/rest/api/3/search/jql` paginiert mit `nextPageToken`
(String) + `isLast` (Bool) — nicht das klassische `startAt`/`total`-Paar des
älteren `/search`-Endpunkts. Live gegen `nicando.atlassian.net` verifiziert:
auch die letzte Seite trägt noch einen (dann veralteten) `nextPageToken`,
daher stoppt die Schleife auf `isLast`, nie auf bloßer Token-Abwesenheit.

**Ausgabeformat**, ein Block pro gefundenem Ticket ohne PRD:

```
jira_sync: new <KEY> "<summary>"
  parent: <PARENT-KEY> -> existing PRD <rel-parent-dir> (siblings: <name1>, <name2>, ...)
  description: <Text aus der ADF-Beschreibung, auf ~300 Zeichen gekürzt, oder "(none)">
```

bzw. `  parent: none -> flat`. Am Ende, nur wenn mindestens ein Ticket
gefunden wurde: `jira_sync: import-new: <n> ticket(s) without an existing
PRD`. Kein Treffer: keine Ausgabe.

### Beides im Loop

`jira-sync: on` genügt nicht allein — beide brauchen dieselben drei
Umgebungsvariablen wie `sync`; fehlen sie, eine Zeile auf stderr, Exit 0,
kein Traceback. Beide laufen in Loop-Schritt 1 (Scan), vor dem eigentlichen
Board-Scan oder direkt danach: `drift`s Zeilen fließen in den Rundenbericht,
`import-new`s Blöcke werden vom Orchestrator in neue `prds/`-Verzeichnisse
umgesetzt (README, **The loop**, Schritt 1).
