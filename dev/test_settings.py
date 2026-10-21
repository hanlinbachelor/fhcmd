# -*- coding: utf-8 -*-
"""验证设置窗：能改配置、能存盘、key 能被正确读出"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QDialog

app = QApplication(sys.argv)
import souti

cfg = souti.load_config()
old_key = cfg.get("api_key", "")

# 1) 窗口能建出来，字段有默认值
dlg = souti.SettingsDialog(None, cfg)
print("默认 api_base =", dlg.ed_base.text())
print("默认 model    =", dlg.ed_model.text())
print("key 输入框是否密码模式 =", dlg.ed_key.echoMode() == dlg.ed_key.EchoMode.Password)

# 2) 填值 + 保存，确认写进 config.json
dlg.ed_base.setText("https://example.com/v1")
dlg.ed_model.setText("some-vision-model")
dlg.ed_key.setText("sk-test-123456")
dlg.save()
print("对话框结果 =", "Accepted" if dlg.result() == QDialog.Accepted else dlg.result())

on_disk = json.loads(open(souti.CONFIG_PATH, encoding="utf-8").read())
assert on_disk["api_base"] == "https://example.com/v1", on_disk["api_base"]
assert on_disk["model"] == "some-vision-model", on_disk["model"]
assert on_disk["api_key"] == "sk-test-123456", "key 没写进配置"
print("✅ 三项都已写入 config.json")

key, src = souti.resolve_api_key(on_disk)
assert key == "sk-test-123456", (key, src)
print("✅ 读回来的 key 正确，来源 =", src)

# 3) 还原成测试前的状态，别弄脏真实配置
cfg["api_base"] = "https://api.deepseek.com"
cfg["model"] = "deepseek-v4-flash-vision-exp"
cfg["api_key"] = old_key
souti.save_config(cfg)
print("✅ 已还原原有配置")
