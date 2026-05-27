---
name: seedance-cli
description: 即梦 CLI / Seedance CLI 的底层命令参考，记录安装登录、文生图、图生视频、查询下载和任务列表等通用命令。
---

# 即梦 CLI / Seedance CLI 命令参考

本参考来自 `CLI/Seedance_CLI/即梦 CLI 体验指南.pdf` 的命令示例。使用前先确认本机已安装 `dreamina` CLI 并已登录。

## 安装与登录

```bash
curl -fsSL https://jimeng.jianying.com/cli | bash
dreamina login
dreamina login --debug
dreamina user_credit
```

## 通用参数

- `--poll=30`：每 30 秒轮询任务状态。指南建议使用 `--poll` 等待生成结果。
- 如果命令只返回 `submit_id`，使用 `query_result` 查询并下载结果。

## 文生图

```bash
dreamina text2image \
  --prompt="<生图提示词>" \
  --ratio=9:16 \
  --resolution_type=2k \
  --poll=30
```

指南示例中 `--ratio` 使用 `1:1`，本技能用于竖屏短视频，默认改为 `9:16`。

## 文生视频

```bash
dreamina text2video \
  --prompt="<生视频提示词>" \
  --duration=5 \
  --ratio=9:16 \
  --video_resolution=720P \
  --poll=30
```

指南示例中 `--ratio` 使用 `16:9`，本技能用于竖屏短视频，默认改为 `9:16`。

## 图生图

```bash
dreamina image2image \
  --images ./input.png \
  --prompt="<图生图提示词>" \
  --resolution_type=2k \
  --poll=30
```

## 图生视频

```bash
dreamina image2video \
  --image ./first_frame.png \
  --prompt="<图生视频提示词>" \
  --duration=5 \
  --poll=30
```

## 查询和下载结果

```bash
dreamina query_result --submit_id=<submit_id>
dreamina query_result --submit_id=<submit_id> --download_dir=./downloads
```

## 列出任务

```bash
dreamina list_task
dreamina list_task --gen_status=success
dreamina list_task --submit_id=<submit_id>
```

## 维护命令

```bash
dreamina relogin
dreamina logout
```

配置和任务信息通常位于：

```text
~/.dreamina_cli/config.toml
~/.dreamina_cli/credential.json
~/.dreamina_cli/tasks.db
~/.dreamina_cli/logs/
```
