#!/usr/bin/env python
import argparse
import os
import shutil
import subprocess
from time import sleep
import tempfile
import urllib.request
from pathlib import Path

from serial.tools.list_ports import comports
import requests

PROBE_SLEEP_S = 0.5

NANOPATH = Path("/run/media/dbadrian/NICENANO")

DEVICES = {
    "left": "149013CC62CD27DE",
    "right": "AB656F058A03AC08",
}

FILES = {
    "left": "corne_left-nice_nano_v2-zmk.uf2",
    "right": "corne_right-nice_nano_v2-zmk.uf2"
}


def mount_disk_by_label(label):
    if not label:
        raise ValueError("Disk label must be specified.")

    try:
        # Use /dev/disk/by-label to find the device
        device_path = f"/dev/disk/by-label/{label}"

        if not os.path.exists(device_path):
            raise RuntimeError(f"No device found with label '{label}'.")

        # Mount the device to the mount point
        subprocess.run(["udisksctl", "mount", "-b", device_path], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute command: {e}. Ensure you have sufficient privileges.")

    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")
    
def flash(firmware_path):
    if not firmware_path.joinpath(FILES["left"]).exists():
        raise FileNotFoundError("Left firmware not found. Something went wrong...")
        
    if not firmware_path.joinpath(FILES["right"]).exists():
        raise FileNotFoundError("Right firmware not found. Something went wrong...")

    print("Please connect the left side now and PUSH RESET TWICE. Probing now", end='', flush=True)
    while True:
        print(".", end='', flush=True)
        sleep(PROBE_SLEEP_S)
        
        devs = [d.serial_number for d in comports()]
        if DEVICES["left"] not in devs:
            continue
        
        # mount the device
        try:
            mount_disk_by_label("NICENANO")
        except:
            continue

        if NANOPATH.joinpath("CURRENT.UF2").exists():
            print("\n\tFound <left>... copying firmware....")
            shutil.copyfile(firmware_path.joinpath(FILES['left']), NANOPATH.joinpath(FILES['left']))
            
            print("Waiting for controller to reboot..please wait.")
            while DEVICES["left"] in [d.serial_number for d in comports()]:
                print("x", end='', flush=True)
                sleep(PROBE_SLEEP_S)
            break
            
    print("\nPlease connect the right side now and PUSH RESET TWICE. Probing now", end='', flush=True)
    while True:
        print(".", end='', flush=True)
        sleep(PROBE_SLEEP_S)
        
        devs = [d.serial_number for d in comports()]
        if DEVICES["right"] not in devs:
            continue
        
        # mount the device
        try:
            mount_disk_by_label("NICENANO")
        except:
            continue

        if NANOPATH.joinpath("CURRENT.UF2").exists():
            print("\n\tFound <right>... copying firmware....")
            shutil.copyfile(firmware_path.joinpath(FILES['right']), NANOPATH.joinpath(FILES['right']))
            
            print("Waiting for controller to reboot..please wait.")
            while DEVICES["right"] in [d.serial_number for d in comports()]:
                print("x", end='', flush=True)
                sleep(PROBE_SLEEP_S)
            break
        
    
    print("PRINT: DONE CODE AWAY!!!")


if __name__ == "__main__":
    print("CORNEv3 ZMK flasher")
    
    # download firmware to a temporary folder
    r = requests.get('https://api.github.com/repos/dbadrian/zmk-config/releases/latest')
    release_details = r.json()
    print(release_details)
    exit()
    
    files = {a['name']: a['browser_download_url'] for a in release_details['assets']}
    
    # download and unzip into a temporary folder
    with tempfile.TemporaryDirectory() as tdir:
        basepath = Path(tdir)
        for name, url in files.items():
            print(f"Downloading {name}...")
            urllib.request.urlretrieve(url, basepath.joinpath(name))

        # start the flashing process
        flash(basepath)
