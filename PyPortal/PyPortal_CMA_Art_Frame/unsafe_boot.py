# SPDX-FileCopyrightText: 2020 Dan Cogliano for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import storage

print("**************** WARNING ******************")
print("Using the filesystem as a write-able cache!")
print("This is risky behavior, backup your files!")
print("**************** WARNING ******************")

storage.remount("/", disable_concurrent_write_protection=True)
time.sleep(5)
