# 01 · 安装 Claude Desktop（Windows）

## 官方安装包是什么

`Claude Desktop Setup.exe`（约 7.5MB）**不是**普通 NSIS 安装器，它是个自解压引导器：

1. 自己 `--elevated` 提权（会弹 UAC，用户点"是"）；
2. 把内嵌的 `Claude-<n>.msix` 释放到 `%TEMP%`；
3. 用 `Add-AppxPackage` 把 MSIX 装到当前用户；
4. 用 `explorer.exe shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude` 拉起应用。

日志在 `%TEMP%\ClaudeSetup.log`，安装完成会写：

```
MSIX package installed successfully
=== Claude Setup completed successfully ===
```

## 装完在哪

| 内容 | 路径 |
| --- | --- |
| 程序本体 | `C:\Program Files\WindowsApps\Claude_<版本>_x64__pzs8sxrjxfjjc\app` |
| 用户数据 / 缓存 | `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude` |
| 日志 | `%LOCALAPPDATA%\Claude\logs`（main.log / mcp.log …） |
| 包版本查询 | `Get-AppxPackage -Name *Claude* \| select PackageFullName,InstallLocation` |

启动命令（快捷方式或用它起进程）：

```powershell
explorer.exe 'shell:AppsFolder\Claude_pzs8sxrjxfjjc!Claude'
```

## 别踩这些

- **`--silent` / `-s` 都不认**：传了会立刻 `ExitCode 2` 退出，什么也不装。
  直接双击/直接运行，让它自己弹 UAC + 进度条最稳。
- **别在装完前抢着起进程**：引导器在"正在完成最后步骤"阶段会 `/f` 掉同名进程，
  提前拉起会被打断，看起来像"装失败"。
- **MSIX 目录是只读的**：要改文件必须提权 + `takeown`，见 [02-shell.md](02-shell.md)。
- 系统区域设成 `zh-CN` 时，外壳会自动用官方 `zh-Hans` 语言表 —— 但官方只写了 893/1310 条，
  剩下的按钮/弹窗会掉回英文，所以还是要补（[02-shell.md](02-shell.md)）。
