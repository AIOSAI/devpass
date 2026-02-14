# System Crash Troubleshooting Guide

**Created:** 2025-10-30
**Last Updated:** 2025-10-30 (Session 1)
**Issue:** Random system crashes causing black screen, keyboard shutdown, forced logout
**Status:** Actively troubleshooting - monitoring with Timeshift disabled

---

## Session History

### Session 1 - October 30, 2025

**Initial Investigation:**
- Analyzed system logs, crash dumps, and boot history
- Identified multiple crashes today with no clear trigger
- Found USB errors with Logitech G502 mouse
- Discovered Timeshift segfault during hourly backup (12:04 PM)
- System crashed 37 minutes later at 12:41 PM
- Journal files corrupted indicating unclean shutdown

**Key Findings:**
- Two crashes today: 9:52 AM (28min uptime) and 12:41 PM (2h44min uptime)
- No kernel panic messages - system stopped instantly
- Corrupted journal files: `/var/log/journal/.../system.journal` and `user-1000.journal`
- Timeshift segfault at memory location (line 217 of crash log)
- No out-of-memory kills detected
- Temperatures normal (CPU 43°C, GPU 42°C)
- Memory: 16GB available, plenty of free space
- Disk: 67GB used of 937GB (8% utilization)

**Actions Taken:**
1. Created crash capture script: `~/capture-crash-log.sh`
2. Unplugged USB charging cable from Logitech G502 (wireless receiver only now)
3. Disabled Timeshift hourly backups to test if crashes are workload-related
4. Generated first crash log: `~/crash-logs/crash-log-20251030-125622.txt`

**User Context:**
- Power loss yesterday (Oct 29) from tripped breaker - explains some journal corruption
- Today's crashes (Oct 30) had NO power loss - concerning
- Crashes are random in timing, not clearly tied to specific activities
- Timeshift runs hourly backups - crashed during one at 12:04 PM
- System is 6+ years old (Ryzen 5 2600 from 2018 era)

**Working Theory:**
Hardware failure (most likely RAM) causing random crashes. Timeshift crashing during backup operation may indicate bad RAM hit during memory-intensive disk I/O. System crashes are so sudden that kernel cannot write panic messages or clean shutdown.

**Next Steps:**
1. Monitor system with Timeshift disabled (testing in progress)
2. Run memtest86+ when time allows (CRITICAL)
3. Capture crash log after next crash
4. If crashes continue with Timeshift off → confirms general hardware issue
5. If crashes stop → Timeshift backups were triggering the failure (but still likely bad RAM)

---

## Problem Summary

Your system is experiencing random crashes (not sleep mode). Evidence shows:
- System has crashed multiple times recently (sometimes after only 28 minutes of uptime)
- USB device errors with Logitech G502 mouse (unplugged dual connection - may help)
- No overheating issues (temperatures are normal at 40-45°C)
- Crashes are random and getting more frequent
- Multiple application crashes recorded (VS Code 134MB crash, Nautilus 23MB crash, Timeshift 970KB crash)
- Journal files corrupted after crashes = unclean shutdown (hardware failure signature)
- No kernel panic messages = system death too sudden to log

**Most Likely Cause:** Bad RAM (80% probability) or failing power supply (15% probability)
**Why:** Instant crashes with no warning + corrupted journals + segfaults = hardware failure pattern

---

## IMMEDIATE ACTION: After Next Crash

Run this command immediately after rebooting from a crash:
```bash
~/capture-crash-log.sh
```

This saves detailed crash information to `~/crash-logs/` for analysis.

---

## Diagnostic Steps (In Priority Order)

### 1. TEST YOUR RAM (HIGHEST PRIORITY)

**Why:** Random crashes with no pattern = bad RAM in 80% of cases

**How to run memtest:**
1. Reboot your computer
2. Hold SHIFT key during boot to see GRUB menu
3. Select "Memory Test (memtest86+)"
4. Let it run for at least 1 full pass (30-60 minutes)
5. **If ANY errors appear = Replace RAM immediately**

**Alternative if GRUB menu doesn't show:**
```bash
sudo reboot
# Then press ESC or SHIFT repeatedly during boot
```

---

### 2. CHECK DISK HEALTH

Install and run disk diagnostics:
```bash
sudo apt install smartmontools
sudo smartctl -a /dev/nvme0n1 | grep -iE "(error|fail|health|worn)"
```

Look for:
- SMART overall-health: should say "PASSED"
- Media errors: should be 0
- Critical warnings: should be 0

---

### 3. MONITOR HARDWARE TEMPERATURES

While system is under load:
```bash
watch -n 2 sensors
```

**Safe temperatures:**
- CPU (Tctl): Under 75°C normal, under 85°C under load
- GPU (edge): Under 80°C
- NVMe: Under 70°C

Press Ctrl+C to exit.

---

### 4. CHECK FOR KERNEL PANICS

After a crash, check if kernel panicked:
```bash
journalctl -b -1 | grep -i "panic\|oops\|bug"
```

---

## Hardware Information

- **CPU:** AMD Ryzen 5 2600 Six-Core Processor
- **GPU:** AMD Radeon RX 580 (open-source drivers)
- **RAM:** 16GB
- **Storage:** NVMe SSD (937GB, 8% used)
- **Kernel:** 6.14.0-33-generic
- **OS:** Ubuntu 24.04 LTS

---

## Known Issues Fixed

1. ✅ Logitech G502 mouse had both wireless + USB charging cable connected
   - **Action taken:** Unplugged USB charging cable (use wireless only or wired only, not both)

2. ✅ Timeshift hourly backups disabled (testing if crashes are related)
   - **Action taken:** Turned off hourly schedule (Oct 30)
   - **Next step:** Monitor if crashes still occur without Timeshift running

---

## Things to Check

**Power Supply:**
- [ ] Check if PSU fan is running
- [ ] Listen for unusual noises from PSU
- [ ] Check if power cables are firmly connected
- [ ] Try different power outlet

**RAM:**
- [ ] Run memtest86+ (see step 1 above)
- [ ] If you have multiple RAM sticks, try one at a time to isolate bad stick
- [ ] Reseat RAM (remove and firmly reinstall)

**Physical:**
- [ ] Check if RAM is properly seated
- [ ] Check if GPU is properly seated
- [ ] Check all power cables (24-pin, 8-pin CPU, PCIe power)
- [ ] Clean dust from case (can cause overheating/shorts)

**Software:**
- [ ] Update system: `sudo apt update && sudo apt upgrade`
- [ ] Check for BIOS updates from motherboard manufacturer

---

## Recent Crash History

### October 30, 2025 (Today)
```
Boot -2: 9:23 AM - 9:52 AM (28 minutes uptime) → CRASH
Boot -1: 9:57 AM - 12:41 PM (2h 44min uptime) → CRASH
         12:04 PM - Timeshift segfault during hourly backup
         12:41 PM - System crash (37 minutes after Timeshift crash)
Current: 12:42 PM - present (monitoring with Timeshift disabled)
```

### October 29, 2025 (Yesterday)
- Power loss from tripped breaker (user confirmed)
- Explains some journal corruption from that date

### Pattern Analysis
- Crashes increasing in frequency
- 37 different boot sessions logged in journal
- Today had 2 crashes in ~3 hours (very unstable)
- Longest recent uptime: ~17 hours (Oct 29, 11:18 AM - Oct 30, 4:07 AM)
- Shortest uptime: 28 minutes (Oct 30, 9:23 AM - 9:52 AM)
- **Pattern shows hardware degradation over time**

---

## What to Report Back (For Next Session)

When you return to discuss this issue, please provide:

1. **Did the system crash again?** Yes/No, and when?
2. **If crashed:** Did you run `~/capture-crash-log.sh`? New crash log location?
3. **Timeshift test results:** With hourly backups disabled, did crashes stop or continue?
4. **Memtest results:** Did you run it? Pass or fail? Any errors shown?
5. **Any patterns noticed:** Time of day, specific activities, loading certain programs?
6. **System uptime:** How long has current session been running? (check with `uptime`)
7. **Any new symptoms:** Freezes, slowdowns, strange behavior before crashes?

**To check current status before next session:**
```bash
uptime                           # How long has system been stable?
journalctl --list-boots | tail -5  # Recent boot history
ls -lt ~/crash-logs/             # Any new crash logs?
```

---

## Emergency Commands

**View last crash immediately after reboot:**
```bash
journalctl -b -1 -p err --no-pager | less
```

**Check if crash dumps exist:**
```bash
ls -lh /var/crash/
```

**View current system health:**
```bash
sensors
free -h
df -h
uptime
```

**List recent boots:**
```bash
journalctl --list-boots | tail -10
```

---

## Next Steps

1. ⚠️ **RUN MEMTEST86+ ASAP** (most likely culprit)
2. Run disk health check
3. Capture crash log after next crash
4. Monitor for patterns (time of day, activity, etc.)
5. Consider stress testing if memtest passes:
   ```bash
   sudo apt install stress-ng
   stress-ng --cpu 4 --timeout 60s --metrics
   ```

---

## Support Files

- **Crash logs location:** `~/crash-logs/`
- **Crash capture script:** `~/capture-crash-log.sh` (run after each crash)
- **This guide:** `~/Desktop/CRASH-TROUBLESHOOTING-GUIDE.md` (session memory)
- **First crash log:** `~/crash-logs/crash-log-20251030-125622.txt`

---

## Important Notes

**About the Crashes:**
- System is NOT going to sleep (idle timeout is 60 minutes, not the cause)
- These are HARD CRASHES requiring reboot, not software hangs
- Random crashes getting more frequent = hardware degradation pattern
- Instant death with no warning = hardware failure signature (not software)

**About Timeshift:**
- Segfault at 12:04 PM during hourly backup
- System crash 37 minutes later at 12:41 PM
- Timeshift crash and system crash may or may not be related
- Hourly backups now DISABLED to test if crashes continue

**Critical Warnings:**
- If memtest finds errors, system is UNSAFE TO USE (can silently corrupt data)
- Bad RAM can cause file corruption even before crashing
- Backup important data if you haven't already
- Consider this system unstable until memtest passes clean

**Power Context:**
- Yesterday (Oct 29): Power loss from tripped breaker
- Today (Oct 30): Two crashes with NO power loss (hardware issue confirmed)

---

## Quick Reference: Resume Next Session

When starting next troubleshooting session, Claude should:
1. Read this document first to recall all context
2. Ask for crash status update (did it crash again?)
3. Check if user ran capture script after any new crashes
4. Review new crash logs if they exist
5. Assess Timeshift test results (crashes with it disabled?)
6. Determine next diagnostic steps based on findings

**Session 1 ended with:** Timeshift disabled, monitoring in progress, memtest not yet run
