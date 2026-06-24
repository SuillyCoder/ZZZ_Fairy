# Device Control

Fairy's awareness of the machine she's running on — performance monitoring, proactive battery warnings, cache cleanup, basic security checks, and visualized performance snapshots.

## System info — `system_info.py`

- `get_system_performance()` — spoken summary of CPU, RAM (used/total via a custom byte-readable formatter), and disk usage, plus battery percentage and charging status if a battery is present
- `check_battery_threshold()` — a tiered warning system (30%, 20%, 10%, 5%) that fires once per discharge cycle per tier, resets when the device is plugged back in or recovers above 30%, so Fairy doesn't repeat the same warning every poll
- `start_battery_monitor()` — runs the threshold check on a background daemon thread at a configurable interval, calling Fairy's speak function directly when a tier fires — this is what lets Fairy proactively warn about low battery without being asked
- `preview_cache_clear()` / `clear_cache()` — scans the OS temp directory, reports how much space could be freed, and only actually deletes after confirmation; handles both files and subdirectories, skips anything locked/permission-denied rather than crashing
- `open_task_manager_performance()` — opens Windows Task Manager directly to the Performance tab via `subprocess`

**Tools/libraries:** `psutil`, `tempfile`, `shutil`, `threading`, `subprocess`

## Security audit — `security_audit.py`

`run_security_audit()` runs three local, read-only checks and reports a pass/fail summary:

- **Firewall** — queries Windows Firewall profile status via `netsh`
- **Defender** — queries real-time protection status via PowerShell's `Get-MpComputerStatus`
- **Open ports** — checks local listening ports via `psutil` against a watchlist of commonly-risky ports (FTP, Telnet, RPC, NetBIOS, SMB, RDP)

This is local introspection only — no remote scanning, no pinging other hosts, no network traffic generated.

**Tools/libraries:** `psutil`, `subprocess` (netsh, PowerShell)

## Performance plotting — `performance_plot.py`

`plot_performance_metrics()` samples CPU%, RAM%, and network upload/download throughput once per second over a short window, then renders a two-panel `matplotlib` chart (CPU/RAM usage on top, network throughput on bottom), annotated with current battery status if available. Saved to `plots/` and returned with a short spoken summary of the averages.

**Tools/libraries:** `psutil`, `matplotlib` (TkAgg backend)

## Current scope

| Capability | Status |
|---|---|
| CPU/RAM/disk/battery status on demand | ✅ |
| Proactive tiered battery warnings | ✅ |
| Temp cache scanning + confirmed clearing | ✅ |
| Firewall / Defender / open-port audit | ✅ |
| Performance snapshot plotting (CPU, RAM, network) | ✅ |
| Task Manager shortcut | ✅ |
| Cross-platform support (currently Windows-specific commands) | 🔲 Not yet |
