#!/usr/bin/env bash
# Reaps what Claude sessions leave behind. Two kinds, both silent when nothing is found:
#  1. Orphaned headless Chromium from tests/live/cdp.mjs and ad-hoc screenshot scripts.
#  2. Orphaned dev servers: `dotnet run` / bin/{Debug,Release} DashboardBuilder started from a Claude
#     shell (CLAUDECODE=1 in its environment) that is now reparented to init and over an hour old.
#     Never the live service (/var/www/...), never a process of another user or without the marker.
# An orphan is a launcher (--remote-debugging-port + a calc-ui-* profile) whose parent is no longer a
# node process, so a browser a running script still owns is never touched. Its whole process group
# goes with it (the helpers share the launcher's group). Silent when nothing is found.
cat >/dev/null 2>&1  # drain the hook's stdin JSON

killed=0
while read -r pid ppid pgid; do
  # node renames its main thread ("MainThread"), so judge the parent by its executable, not its comm
  parent=$(readlink "/proc/$ppid/exe" 2>/dev/null)
  [ "${parent##*/}" = "node" ] && continue
  kill -9 -- "-$pgid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
  killed=$((killed + 1))
done < <(ps -eo pid=,ppid=,pgid=,args= | awk '$4 ~ /(chrome|chrome-headless-shell|headless_shell)$/ && /--remote-debugging-port/ && /user-data-dir=[^ ]*calc-ui-/ && !/--type=/ {print $1, $2, $3}')

# The profile dirs go too: a SIGKILLed launcher (here or from a killed script) never runs its own cleanup.
# Only calc-ui-* dirs no live process references and older than a minute, so a browser a running script owns
# (or is just about to spawn) keeps its profile.
live=$(ps -eo args= | grep -o 'user-data-dir=[^ ]*calc-ui-[^ ]*' | cut -d= -f2-)
while IFS= read -r dir; do
  grep -qxF "$dir" <<<"$live" && continue
  rm -rf -- "$dir"
done < <(find "${TMPDIR:-/tmp}" -maxdepth 1 -type d -name 'calc-ui-*' -user "$(id -un)" -mmin +1 2>/dev/null)

# --- 2. orphaned dev servers ---------------------------------------------------------------------
# Root = owned by us, CLAUDECODE=1, parent is init, >= 1 h old, and a dev-run command line. Its whole
# subtree goes too (the `dotnet run` wrapper, its shell and the app child that holds the port).
MIN_AGE=${REAP_MIN_AGE:-3600}   # override only for testing
me=$(id -u)
descendants() { local c; for c in $(pgrep -P "$1" 2>/dev/null); do descendants "$c"; echo "$c"; done; }
devkilled=0
while read -r pid ppid age args; do
  [ "$ppid" = 1 ] && [ "$age" -ge "$MIN_AGE" ] || continue
  [ "$(stat -c %u "/proc/$pid" 2>/dev/null)" = "$me" ] || continue
  tr '\0' '\n' <"/proc/$pid/environ" 2>/dev/null | grep -qx 'CLAUDECODE=1' || continue
  case "$args" in */var/www/*) continue ;; esac
  victims="$(descendants "$pid") $pid"
  # TERM first so Kestrel releases its port, KILL whatever is left
  kill $victims 2>/dev/null; sleep 1; kill -9 $victims 2>/dev/null
  devkilled=$((devkilled + 1))
done < <(ps -u "$me" -o pid=,ppid=,etimes=,args= | grep -E '(dotnet (run|watch)( |$)|/bin/(Debug|Release)/net[0-9.]+/DashboardBuilder)' | grep -v grep)

msg=""
[ "$killed" -gt 0 ] && msg="Removed $killed orphaned headless Chrome browser(s). "
[ "$devkilled" -gt 0 ] && msg="${msg}Stopped $devkilled orphaned dev server(s)."
[ -n "$msg" ] && printf '{"systemMessage":"%s"}\n' "${msg% }"
exit 0
