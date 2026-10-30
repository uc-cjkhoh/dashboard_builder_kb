#!/usr/bin/env bash
# Kills orphaned headless Chromium left behind by tests/live/cdp.mjs and ad-hoc screenshot scripts.
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

[ "$killed" -gt 0 ] && printf '{"systemMessage":"Removed %d orphaned headless Chrome browser(s)."}\n' "$killed"
exit 0
