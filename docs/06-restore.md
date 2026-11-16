# 06 · 还原 与 升级后重打

## 备份长什么样

第一次执行 `*-install` 时自动创建：

```
backup\app.asar        88,812,777 字节   官方外壳
backup\ion-dist.asar   208,001,845 字节  官方 Web 前端
backup\claude.exe      249,955,664 字节  官方 exe（fuse 还是原始状态）
```

## 一键还原

```powershell
python scripts/hanhua.py restore --backup backup    # 需要管理员
```

它会 `takeown` 后把三个文件逐个拷回，重启 Claude 即恢复英文原版。

只想还原某一层，就把对应备份文件手动拷回目标位置（记得先 `takeown` + `icacls`）。

## Claude 升级之后

Claude 更新会装到**新的版本目录**（`Claude_<新版本>_x64__pzs8sxrjxfjjc`），
`app.asar` / `ion-dist.asar` / `claude.exe` 全是官方原版，补丁自然失效。

重打流程（脚本会按 `Get-AppxPackage` 自动找新目录，不用改版本号）：

```powershell
# 1. 外壳
python scripts/hanhua.py shell-build
python scripts/hanhua.py shell-install      # 管理员

# 2. Code 界面（词库不用重下）
python scripts/hanhua.py ion-build
python scripts/hanhua.py ion-install        # 管理员
```

注意：

- 新版本如果改了 key，命中率会下降（不会崩，未命中的保留英文）；
  想提高命中率就去 `sheen945/claude-hanhua` 拿最新 `zh.json.gz` 覆盖 `dict\zh.json.gz`。
- 新版如果连 asar 结构都变了（比如又改回散文件），`ion-build` 会报
  `ion-dist 里没有 i18n/en-US.json`，那就需要跟着新结构改脚本。
- 备份别删：`backup\` 里永远是最初那份官方文件，重打时不会被覆盖。

## 想彻底回到原厂

```powershell
Get-AppxPackage -Name *Claude* | Remove-AppxPackage
# 然后重新跑一次官方的 Claude Desktop Setup.exe
```

因为拿过 `WindowsApps` 里文件的所有权，个别情况下卸载会报权限错误，
这时先 `Stop-Process -Name claude -Force` 再卸载。
