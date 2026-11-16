三层汉化全流程，Windows 实测（Claude Desktop 5.11492.5.0 MSIX + Claude Code 2.1.284 native）。

## 这一版做了什么

| 层 | 位置 | 处理 | 结果 |
| --- | --- | --- | --- |
| 桌面外壳 | `app.asar` → `resources/i18n/zh-Hans.json` | 补齐官方缺的 417 条，重打包 asar | 1310/1310 全中文 |
| Code 标签页（界面本体） | `ion-dist.asar` → JS 里的 `defaultMessage` | 用社区词库替换字符串字面量 | 56,908 处 / 1,417 个 js |
| Code 标签页语言表 | `ion-dist.asar` → `i18n/en-US.json` | 仅作备用（改它不生效，见 docs/03） | 词库命中 43,442 / 44,218 |
| Claude Code CLI | `claude.exe` | 第三方插件（UTF-16LE 写入字节码常量池） | 1,427 条，`--help` 全中文 |

## 关键发现

1. Electron 的 `EnableEmbeddedAsarIntegrityValidation` 会让改过的 asar 直接 `FATAL: Integrity check failed`，必须用 `@electron/fuses` 关掉。
2. `WindowsApps` 目录要 `takeown` + `icacls` 才写得进，而且必须提权（UAC）。
3. **改 `i18n/en-US.json` 改了等于没改**：en-US 是默认语言，应用直接渲染 JS 里的 `defaultMessage`，压根不加载语言表。这也是现成汉化项目在英文环境下失效的原因。

## 包含内容

- `docs/01~07`：安装、外壳、Code 界面、CLI、GitHub 方案对比、还原、10 条踩坑记录
- `scripts/hanhua.py`：`check` / `shell-build` / `shell-install` / `ion-build` / `ion-install` / `restore`
- `scripts/fuses.js`：读写 Electron fuse
- `data/zh_1~3.json`：自写的 417 条外壳译文

## 用法

```powershell
git clone https://github.com/huajikano/claude-desktop-cn.git
cd claude-desktop-cn
python scripts/hanhua.py check
python scripts/hanhua.py shell-build
python scripts/hanhua.py shell-install          # 管理员
# 词库：https://raw.githubusercontent.com/sheen945/claude-hanhua/master/zh.json.gz → dict/zh.json.gz
python scripts/hanhua.py ion-build
python scripts/hanhua.py ion-install            # 管理员
```

## 还原

```powershell
python scripts/hanhua.py restore                # 管理员
```

## 致谢

- 词库：[sheen945/claude-hanhua](https://github.com/sheen945/claude-hanhua)（MIT，44,199 条，本仓库不分发，只提供下载命令）
- CLI：[taekchef/claude-code-zh-cn](https://github.com/taekchef/claude-code-zh-cn)（MIT）

非官方汉化，改的是本机安装文件；升级或"修复/重置"会覆盖补丁，重跑脚本即可。
