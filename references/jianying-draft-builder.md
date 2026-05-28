---
name: jianying-draft-builder
description: 剪映草稿生成器规范，定义从 asset-manifest.json、视频、音频和字幕生成剪映时间线输入，或通过已验证工具生成原生草稿的输入、输出和限制。
---

# 剪映草稿生成器规范

## 目标

在全部图片确认并生成视频后，读取 `asset-manifest.json`，把每条素材按顺序放入剪映草稿时间线。

## 输入

默认输入目录为 `outputs/<project>/`：

```text
outputs/<project>/
├── asset-manifest.json
├── videos/
├── audio/
└── subtitles/
```

每条 manifest 记录至少需要：

- `id`
- `video_file`
- `duration_seconds`
- `subtitle`
- `image_approved: true`

可选字段：

- `audio_file`：该镜头旁白音频。
- `subtitle_file`：该镜头字幕文件。
- `video_actual_duration_seconds`：优先用于剪映片段时长。
- `jianying_clip_start_seconds`：生成草稿时回填。
- `jianying_clip_duration_seconds`：生成草稿时回填。

## 输出

```text
outputs/<project>/jianying-draft/
├── timeline.json
├── draft_content.json 或工具生成的等价草稿文件（仅真实草稿工具可用时）
├── draft_meta_info.json 或工具生成的等价草稿文件（仅真实草稿工具可用时）
└── materials/（仅真实草稿工具可用时）
```

## 生成规则

- 视频轨：按 manifest 顺序拼接 `video_file`。
- 音频轨：存在 `audio_file` 时按同一开始时间放入旁白音频。
- 字幕轨：优先使用 `subtitle` 生成字幕；存在 `subtitle_file` 时可直接导入。
- 时长：优先使用 `video_actual_duration_seconds`，否则使用 `duration_seconds`。
- 图片未全部确认时不得生成视频或剪映草稿。

## 工具选择

优先顺序：

1. 本地实测可用的 `cut_cli`。
2. 本地实测可用的 `pyJianYingDraft`。
3. 第三方 JianYing MCP。
4. 仅生成 `jianying-draft-plan.md`。

使用第三方 MCP 或 CLI 前，必须确认工具来源、写入目录和是否会上传素材。
