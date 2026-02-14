sudo cp ~/SANDBOX_SETUP.md /mnt/sandbox/
# Sandbox Environment Setup Guide

  **Created:** 2025-10-30
  **Location:** /mnt/sandbox
  **Type:** Partition-based chroot isolation sandbox

  ---

  ## What This Is

  A 49GB isolated partition that acts like a Docker-style container but native to Linux.
  When you enter this sandbox via chroot, it becomes your entire world - nothing from the
  parent system exists unless you explicitly copy it in.

  **Key Concept:** TRUE isolation - which python3 returns nothing because Python doesn't 
  exist here unless installed.

  ---

  ## Setup Commands Used

  ```bash
  # 1. Create partition
  sudo dd if=/dev/zero of=/home/aipass/sandbox.img bs=1G count=50

  # 2. Format it
  sudo mkfs.ext4 /home/aipass/sandbox.img

  # 3. Mount it
  sudo mkdir -p /mnt/sandbox
  sudo mount -o loop /home/aipass/sandbox.img /mnt/sandbox

  # 4. Create structure
  sudo mkdir -p /mnt/sandbox/home/aipass/aipass_core
  sudo chown -R aipass:aipass /mnt/sandbox/home/aipass

  # 5. Setup chroot
  sudo mkdir -p /mnt/sandbox/bin
  sudo cp /bin/bash /mnt/sandbox/bin/
  sudo mkdir -p /mnt/sandbox/lib64 /mnt/sandbox/lib/x86_64-linux-gnu
  sudo cp /lib64/ld-linux-x86-64.so.2 /mnt/sandbox/lib64/
  sudo cp /lib/x86_64-linux-gnu/libtinfo.so.6 /mnt/sandbox/lib/x86_64-linux-gnu/
  sudo cp /lib/x86_64-linux-gnu/libc.so.6 /mnt/sandbox/lib/x86_64-linux-gnu/

  How to Use

  Enter sandbox:
  sudo chroot /mnt/sandbox /bin/bash

  Exit sandbox:
  exit

  Status

  - Location: /mnt/sandbox (49GB partition)
  - Contains: bash shell + minimal libraries
  - Python: NOT installed (clean slate)
  - Commands: Only bash (ls, cp, etc. not available yet)

  Next Steps

  Add more tools as needed, install Python, test packages in isolation.
  ENDOFFILE
sudo cp ~/SANDBOX_SETUP.md /mnt/sandbox/
EOF
