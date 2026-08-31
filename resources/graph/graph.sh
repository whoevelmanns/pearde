#!/bin/bash
# pearde graph — graphify rounds over any folder, Obsidian vault out.
#
#   graph.sh extract [folder] [--force]   full extraction, clusters + Obsidian vault
#   graph.sh update [folder]              re-extract changed files only (AST, no LLM)
#   graph.sh query [folder] "question"    BFS over graph.json, capped budget
#   graph.sh path [folder] "A" "B"        shortest path between two nodes
#   graph.sh explain [folder] "X"         one node and its neighbors, plain language
#   graph.sh god-nodes [folder]           most connected nodes
#   graph.sh open [folder]                open graphify-out/obsidian as a vault
#
# Defaults come from here; PEARDE_GRAPH_MODEL / PEARDE_GRAPH_FOLDER override.
set -uo pipefail

BACKEND=ollama
MODEL="${PEARDE_GRAPH_MODEL:-glm-5.3-flash:cloud}"

cmd="${1:-help}"; [ $# -gt 0 ] && shift

case "$cmd" in
  extract|update|query|path|explain|god-nodes|open)
    : ;;
  help|-h|--help|"")
    awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
  *)
    echo "unknown command: $cmd (extract | update | query | path | explain | god-nodes | open)" >&2
    exit 2 ;;
esac

# First positional arg that is a directory is the folder; the rest are args.
FOLDER="${PEARDE_GRAPH_FOLDER:-.}"
ARGS=()
for a in "$@"; do
  if [ -d "$a" ] && [ "${#ARGS[@]}" -eq 0 ]; then FOLDER="$a"; else ARGS+=("$a"); fi
done

cd "$FOLDER" || exit 1

case "$cmd" in
  extract)
    graphify extract . --backend "$BACKEND" --model "$MODEL" --max-concurrency 1 ${ARGS[@]:-}
    ;;
  update)
    graphify update .
    ;;
  query)
    graphify query "${ARGS[0]}" ${ARGS[@]:1}
    ;;
  path)
    graphify path "${ARGS[0]}" "${ARGS[1]}"
    ;;
  explain)
    graphify explain "${ARGS[0]}"
    ;;
  god-nodes)
    graphify god-nodes
    ;;
  open)
    open "obsidian://open?path=$(python3 -c "import os,urllib.parse;print(urllib.parse.quote(os.path.abspath('graphify-out/obsidian')))")"
    ;;
esac