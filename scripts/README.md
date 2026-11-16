# scripts

## hanhua.py —— 一体化工具

前置：Node.js 18+（内部用 `npx @electron/asar`、`node fuses.js`）、Python 3.8+。

| 子命令 | 权限 | 作用 |
| --- | --- | --- |
| `check` | 普通 | 列出安装目录、asar 体积、语言表条数与中文占比、fuse 状态 |
| `shell-build` | 普通 | 解包 `app.asar` → 合并 `data/*.json` 的 417 条增补 → 重打包到 `work/app-new.asar` |
| `shell-install` | **管理员** | 备份 → `takeown` → 覆盖 `app.asar` → 关 asar 完整性 fuse |
| `ion-build` | 普通 | 解包 `ion-dist.asar` → 替换 JS 里的 `defaultMessage` → 重打包到 `work/ion-dist.new.asar` |
| `ion-install` | **管理员** | 备份 → `takeown` → 覆盖 `ion-dist.asar` |
| `restore` | **管理员** | 从 `backup/` 还原 `app.asar` / `ion-dist.asar` / `claude.exe` |

通用参数 `--pkg <dir>`：手动指定安装目录（默认用 `Get-AppxPackage` 自动找最新的
`Claude_*` 包，找不到再退到 `%LOCALAPPDATA%\AnthropicClaude\app-*`）。

### 典型用法

```powershell
python scripts/hanhua.py check

python scripts/hanhua.py shell-build --work work
python scripts/hanhua.py shell-install --work work --backup backup

python scripts/hanhua.py ion-build --work work --dict dict/zh.json.gz
python scripts/hanhua.py ion-install --work work --backup backup

python scripts/hanhua.py restore --backup backup
```

## fuses.js

读写 Electron 的 fuse wire，只做一件事：把 `EnableEmbeddedAsarIntegrityValidation` 关掉，
让改过的 asar 能被加载。

```powershell
node scripts/fuses.js "<pkg>\claude.exe" show
node scripts/fuses.js "<pkg>\claude.exe" disable-asar
```

输出 `49` = 开启（校验），`48` = 关闭。

## 关于提权

`*-install` / `restore` 会检查当前进程是否管理员，不是就直接退出并提示。
以管理员身份打开 PowerShell 再跑，或者：

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-NoExit','-Command','cd "D:\path\to\repo"; python scripts/hanhua.py shell-install'
```
