---
name: media-commands-template
description: 03-media-commands.md 的 Markdown 模板，按 provider 输出首帧生图请求、图生视频请求、下载重命名和 manifest 回填说明。
---

# 媒体生成命令/请求清单

## Provider 选择

- 生图 provider：`<image_provider>`，可选 `gpt-image-2` 或 `dreamina-cli`
- 生视频 provider：`<video_provider>`，可选 `kling-api` 或 `dreamina-cli`
- 目标画幅：`9:16`
- 目标图片尺寸：`1152x2048`

最终生成 `03-media-commands.md` 时，只保留用户选择的生图 provider 区块和当前生视频 provider 区块；不要同时输出未选中的 provider 区块。

## 执行前检查

### dreamina-cli provider

仅当生图 provider 或生视频 provider 选择 `dreamina-cli` 时执行：

```bash
dreamina --help
dreamina user_credit
```

### gpt-image-2 provider

仅当生图 provider 选择 `gpt-image-2` 时确认：

```bash
test -n "$KFCV50_API_KEY"
```

### kling-api provider

仅当生视频 provider 选择 `kling-api` 时确认：

```bash
test -n "$KLING_ACCESS_KEY"
test -n "$KLING_SECRET_KEY"
```

## <id>：<pain_point>

- 计划图片：`images/<id>.png`
- 计划视频：`videos/<id>.mp4`
- 图片尺寸：`1152x2048`
- 参考时长：`<duration_seconds>s`

### 首帧生图：gpt-image-2

```bash
curl -X POST "https://kfcv50.link/v1/images/generations" \
  -H "Authorization: Bearer $KFCV50_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "<image_prompt>",
    "image": [],
    "size": "1152x2048",
    "response_format": "url"
  }'
```

下载响应中的 `data[0].url` 到 `./outputs/<project>/images/<id>.png`。

### 首帧生图：dreamina-cli

```bash
dreamina text2image \
  --prompt="<image_prompt>" \
  --ratio=9:16 \
  --resolution_type=2k \
  --poll=30
```

```bash
dreamina query_result --submit_id=<image_task_id> --download_dir=./outputs/<project>/images
# 将任务结果下载并重命名为：./outputs/<project>/images/<id>.png
```

### 图生视频：kling-api

```text
provider: kling-api
request:
  input_image: ./outputs/<project>/images/<id>.png
  prompt: <video_prompt>
  duration_seconds: <duration_seconds>
  output_video: ./outputs/<project>/videos/<id>.mp4
```

如果环境没有可灵 API 调用脚本或 SDK，不要编造 endpoint 或命令；只记录以上请求字段，交由可用脚本或 SDK 执行，并将结果保存为 `./outputs/<project>/videos/<id>.mp4`。

### 图生视频：dreamina-cli

```bash
dreamina image2video \
  --image ./outputs/<project>/images/<id>.png \
  --prompt="<video_prompt>" \
  --duration=<duration_seconds> \
  --model_version=seedance2.0fast \
  --video_resolution=720p \
  --poll=30
```

```bash
dreamina query_result --submit_id=<video_task_id> --download_dir=./outputs/<project>/videos
# 将任务结果下载并重命名为：./outputs/<project>/videos/<id>.mp4
```

## Manifest 回填

生成或下载素材后，按痛点 ID 将首帧图片、视频路径和所选 provider 的生成信息回填到 `asset-manifest.json`。确保图片路径为 `./outputs/<project>/images/<id>.png`，视频路径为 `./outputs/<project>/videos/<id>.mp4`。

按选中的生图 provider 回填：`image_provider`、`image_model`、`image_size`、`image_task_id`、`image_original_url`、`image_original_file`。

- `gpt-image-2`：回填 `image_provider: gpt-image-2`、`image_model: gpt-image-2`、`image_size: 1152x2048`、`image_original_url: data[0].url`。如接口响应没有任务 ID，则 `image_task_id` 填 `null`；下载后的规范图片路径仍写入图片路径字段。
- `dreamina-cli` 生图：CLI 查询里的 `--submit_id=<image_task_id>` 只是 CLI 参数占位，manifest 仍写 `image_task_id`。回填 `image_provider: dreamina-cli`、实际使用的 `image_model`、`image_size`、`image_original_file`；如没有原始 URL，则 `image_original_url` 填 `null`。

按选中的生视频 provider 回填：`video_provider`、`video_model`、`video_task_id`、`video_original_url`、`video_original_file`、`video_actual_duration_seconds`。

- `kling-api`：只有实际请求或接口响应中有明确模型名时才回填 `video_model`；没有则填 `null`，不要伪造模型名或 endpoint。按接口响应回填 `video_task_id`、`video_original_url`、`video_original_file` 和 `video_actual_duration_seconds`；缺失字段填 `null`。
- `dreamina-cli` 视频：CLI 查询里的 `--submit_id=<video_task_id>` 只是 CLI 参数占位，manifest 仍写 `video_task_id`。回填 `video_provider: dreamina-cli`、`video_model: seedance2.0fast`、`video_original_file` 和 `video_actual_duration_seconds`；如没有原始 URL，则 `video_original_url` 填 `null`。
