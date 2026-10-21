# 版本下载站（site/）

一个零依赖的小站点：**版本选择 + 下载**。纯静态页面 + 一个 Python 标准库服务器，
所以既能本机/校园网跑，也能原样丢到任何静态托管（GitHub Pages、Cloudflare Pages、学校空间）。

```
site/
  index.html          页面（深色，和程序同一套视觉语言）
  versions.json       版本清单（版本号/大小/sha256/更新说明）
  releases/*.zip      安装包（由 add_release.py 生成）
  serve.py            本机服务器（静态 + /api/versions + /download/* + 下载计数）
  add_release.py      打包新版本并更新清单
  启动下载站.bat       双击启动（会顺手打开浏览器）
  downloads.log       下载记录（自动生成，不进版本库）
```

## 一、启动（本机 / 校园网）

双击 **`启动下载站.bat`**，或：

```bash
cd site
..\.venv\Scripts\python.exe serve.py        # 默认 80 端口 => 地址不用带端口号
..\.venv\Scripts\python.exe serve.py --port 8080   # 想换端口时
```

**默认监听 80**，所以别人打开 `http://<你的IP>/` 就行，**不需要写 `:8000`**。
如果 80 被别的软件占用，会自动退到 8000 并在窗口里提示。

启动后窗口里会打印可访问地址，例如：

```
本机            http://127.0.0.1:8000
局域网/校园网    http://172.20.10.3:8000
```

把 **局域网/校园网那一行** 发给同学即可；页面右侧还有**二维码**，手机扫一下就进来，连地址都不用打。首次运行 Windows 会弹防火墙提示，
勾选「专用网络」并允许，否则别人连不上。

### 关于「校园网内访问」的现实限制

- 只有**和你在同一网段、且学校没有开启客户端隔离**时，别人才能访问你的电脑。
  很多高校的无线网会隔离终端（AP isolation），这种情况下同学打不开，需要换下面第 3 条的做法。
- 手机热点（`172.20.10.x`）是另一个网段：**连同一个热点**的设备能访问，校园网里的同学不能。
- 换网络后 IP 会变，重新启动一次看新地址即可（页面里的地址不用改）。

## 二、发布新版本

```bash
cd site
..\.venv\Scripts\python.exe add_release.py --version v1.1.0
```

它会：改 `souti.py` 的 `__version__` → 打出 `releases/fhcmd-v1.1.0.zip`
（含 souti.py / README / CHANGELOG / 启动 bat / config.example / icon）→ 算 sha256 →
更新 `versions.json` → 同步进 `index.html` 的内联数据。

更新说明默认从 `CHANGELOG.md` 对应版本那一节抓，也可以 `--notes "一句话"` 手动给。

> 页面每 0 次刷新都会重新读清单，**发布后不用重启服务器**，刷新页面就能看到新版本。

## 三、想放到公网/学校空间（推荐，同学不受隔离影响）

因为页面是纯静态的，直接把这几个文件传上去就能用：

```
index.html  versions.json  releases/
```

- **GitHub Pages**：把仓库推到 GitHub → Settings → Pages → 选分支，得到 `https://<用户名>.github.io/<仓库>/`。
  注意页面里下载链接会自动退化成 `releases/xxx.zip`（没有 `/download/` 计数接口），仍然能下。
- **Cloudflare Pages / Vercel / 任意静态空间**：拖上去即可。
- 需要下载计数的话，只有 `serve.py` 这种带后端的模式才有。

## 四、接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 首页 |
| GET | `/api/versions` | 版本清单 JSON（含每个包的下载次数） |
| GET | `/download/<文件名>` | 下载安装包，并记一次到 `downloads.log` |
| GET | `/qr.png` | 当前访问地址的二维码（按请求的 Host 动态生成） |

## 五、安全

- 服务器**只以 `site/` 为根目录**，程序本体、`.venv`、`config.json`、`error.log` 都不会被暴露。
- `serve.py` / `add_release.py` / `downloads.log` 与隐藏文件一律 404。
- 站点不含任何 API Key；安装包里也只有 `config.example.json`（空 key）。
- 只想自己看：`serve.py --host 127.0.0.1`（局域网访问会被拒）。
