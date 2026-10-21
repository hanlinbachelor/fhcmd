# -*- coding: utf-8 -*-
"""GitHub 设备码登录（等价于 gh auth login --web，但可脚本化）

流程：
  1. 向 GitHub 要一个一次性代码（形如 XXXX-XXXX）
  2. 用户在浏览器打开 https://github.com/login/device 输入代码并授权
  3. 本脚本轮询拿到 token，写进 gh 的凭据里
"""
import json
import subprocess
import sys
import time

import requests

CLIENT_ID = "178c6fc778ccc68e1d6a"          # GitHub CLI 的公开 client id
SCOPE = "repo read:user workflow"
GH = r"C:\Program Files\GitHub CLI\gh.exe"


def post(url, **data):
    return requests.post(url, data=data,
                         headers={"Accept": "application/json"},
                         timeout=30).json()


def main():
    d = post("https://github.com/login/device/code", client_id=CLIENT_ID, scope=SCOPE)
    if "device_code" not in d:
        sys.exit(f"申请设备码失败：{d}")
    code = d["user_code"]
    url = d["verification_uri"]
    interval = d.get("interval", 5)
    print(f"CODE={code}")
    print(f"URL={url}")
    print("等待授权…", flush=True)

    deadline = time.time() + d.get("expires_in", 900)
    while time.time() < deadline:
        time.sleep(interval)
        r = post("https://github.com/login/oauth/access_token",
                 client_id=CLIENT_ID, device_code=d["device_code"],
                 grant_type="urn:ietf:params:oauth:grant-type:device_code")
        err = r.get("error")
        if err == "authorization_pending":
            print("… 还没点授权", flush=True)
            continue
        if err == "slow_down":
            interval += 5
            continue
        if err:
            sys.exit(f"授权失败：{err} {r.get('error_description', '')}")
        token = r.get("access_token")
        if not token:
            sys.exit(f"没拿到 token：{r}")
        print("TOKEN_OK", flush=True)

        # 交给 gh 保存（之后 git push 也用它）
        p = subprocess.run([GH, "auth", "login", "--hostname", "github.com", "--with-token"],
                           input=token, text=True, capture_output=True)
        print("gh 写入凭据:", p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip())
        p2 = subprocess.run([GH, "auth", "status"], text=True, capture_output=True)
        print(p2.stdout.strip() or p2.stderr.strip())
        return
    sys.exit("超时，未完成授权")


if __name__ == "__main__":
    main()
