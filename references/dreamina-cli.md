---
name: dreamina-cli
description: 易纸箱视频流程中用户选择或指定即梦 CLI 时的执行规范，定义 text2image、image2video、seedance2.0fast 参数和 manifest 回填规则。
---

# 即梦 CLI 执行规范

本文件在用户选择 `dreamina-cli` 生图，或未指定/明确指定使用即梦、Dreamina、Seedance、CLI 生视频时读取。默认生视频 provider 是 `dreamina-cli`。

底层命令参考见 `references/seedance-cli.md`。命令清单格式使用 `templates/media-commands.md`，本文件只写执行规则，不重复展开完整模板。

## 生成前检查

需要实际生成素材时先运行：

```bash
dreamina --help
dreamina user_credit
```

如果 CLI 不可用、未登录、额度不足或用户没有授权执行外部生成命令，停止在素材生成前；保留 `01-analysis.md`、`02-prompts.json`、`asset-manifest.json`、`03-media-commands.md` 和 `jianying-draft-plan.md`。

## 命令清单生成规则

生成 `03-media-commands.md` 时，按 `templates/media-commands.md` 的结构为每个痛点填入：

- `id`
- `pain_point`
- `image_file`
- `video_file`
- `image_prompt`
- `video_prompt`
- `duration_seconds`

只有当对应 provider 被选中时，才在 `03-media-commands.md` 输出 Dreamina 的文生图块或图生视频块。命令清单按痛点分组；Dreamina 文生图块包含文生图、下载重命名首帧，Dreamina 图生视频块包含图生视频、下载重命名视频。

如果提示词包含双引号或换行，改写为单行并转义，确保用户可以直接复制执行。

## 文生图执行规则

用户选择 `dreamina-cli` 生图时，对 `02-prompts.json` 中每个 `image_prompt` 调用 `dreamina text2image`：

- `--ratio=9:16`
- `--resolution_type=2k`
- `--poll=30`

生成成功后下载到 `images/`。如果 CLI 返回任务 ID 但未自动下载，使用 `dreamina query_result --download_dir` 下载，并将该任务 ID 回填为 `image_task_id`。

即梦下载文件名可能是任务 ID 或乱码，不要让后续流程依赖它。下载后按 `02-prompts.json` 的 `image_file` 重命名，例如 `pain-01.png`。在 `asset-manifest.json` 回填：

- `image_provider`: `dreamina-cli`
- `image_model`: `dreamina-text2image-2k`，如果 CLI 未返回模型名
- `image_size`: `1152x2048`
- `image_task_id`
- `image_original_file`

如果实际扩展名不是 `.png`，按真实扩展名更新 `image_file`、`asset-manifest.json` 和命令清单；不要改写 `video_prompt` 来承载首帧路径。

## 图生视频执行规则

只有用户指定 `dreamina-cli` 视频 provider 时，对每张已生成图片，结合对应的 `video_prompt` 和 `duration_seconds` 调用 `dreamina image2video`。

`--image` 必须使用重命名后的 `image_file`，不要使用即梦返回的原始文件名。

Dreamina 视频 provider 下图生视频优先速度，使用：

```bash
--model_version=seedance2.0fast
--video_resolution=720p
```

生成成功后下载到 `videos/`，并按 `video_file` 重命名，例如 `pain-01.mp4`。在 `asset-manifest.json` 回填：

- `video_provider`: `dreamina-cli`
- `video_model`: `seedance2.0fast`
- `video_task_id`
- `video_original_file`
- `video_actual_duration_seconds`，如果 CLI 返回实际时长
