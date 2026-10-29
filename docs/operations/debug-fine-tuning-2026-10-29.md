# Debug log — fine-tuning run 2026-10-29

Warnings, errors, bugs, permission denials and anything that stopped development during the fine-tuning run. Append-only.

- **ft-connection** (2026-10-29) — setPill/PILL in Core/ui.js are now unused dead code (out of scope: Core); left in place. Task 6: server returns the entered (trimmed) host, so the only host loss found was the blank form after a reload/change; fixed via formFromView, recent stored from the entered host. No other errors.
