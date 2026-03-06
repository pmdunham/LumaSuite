#!/usr/bin/env python3
import requests
import argparse
import os

def upload_firmware(ip, filepath):
    if not os.path.isfile(filepath):
        print(f"[ERR] File not found: {filepath}")
        return

    url = f"http://{ip}/upload"
    fname = os.path.basename(filepath)

    print(f"[CS31] Uploading to {url}")
    print(f"[CS31] Field name: FIREWARE_FILE")
    print(f"[CS31] Sending Chrome-style multipart/form-data")

    with open(filepath, "rb") as f:
        # EXACTLY like Chrome sends it
        files = {
            "FIREWARE_FILE": (
                fname,
                f,
                "application/x-gzip"
            )
        }

        try:
            resp = requests.post(url, files=files, timeout=600)
        except requests.exceptions.ConnectionError as e:
            # Device drops TCP mid-flash — this is normal
            print("[CS31] Device closed connection during write (expected).")
            print("[CS31] Flash is in progress. Wait 60–90 seconds.")
            return
        except requests.exceptions.ReadTimeout:
            print("[CS31] Timeout but upload was accepted. Device is flashing.")
            return

    print(f"[CS31] HTTP Status: {resp.status_code}")
    print(f"[CS31] Response text: {resp.text}")
    print("[CS31] If no ‘error’ shown, device is flashing now.")

def main():
    parser = argparse.ArgumentParser(description="CS31 Firmware Uploader")
    parser.add_argument("--ip", required=True, help="CS31 IP address")
    parser.add_argument("--file", required=True, help="Firmware .tar.gz path")
    args = parser.parse_args()
    upload_firmware(args.ip, args.file)

if __name__ == "__main__":
    main()
