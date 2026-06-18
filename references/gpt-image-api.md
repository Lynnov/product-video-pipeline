---
name: gpt-image-api
description: RightCode Draw 第三方 gpt-image-2 生图接口参考，供易纸箱视频流程在需要替代或补充即梦文生图时使用。
---

# GPT Image API 接入参考

本文档记录 RightCode Draw 中转的 `gpt-image-2` 生图接口。该接口历史实测尺寸为 `1024x1024`；当前易纸箱目标默认尺寸为 `1152x2048`，批量使用前仍需小样本验证。

## 基础信息

- Provider: RightCode Draw
- 主通道名称：`kfcv50-primary`
- 备用通道名称：`kfcv50-fallback`
- Base URL: `https://www.right.codes/draw`
- Endpoint: `POST /v1/images/generations`
- Full URL: `https://www.right.codes/draw/v1/images/generations`
- 主 API 环境变量：`KFCV50_API_KEY`、`KFCV50_BASE_URL`、`KFCV50_IMAGE_MODEL`
- 备用 API 环境变量：`KFCV50_FALLBACK_ENABLED`、`KFCV50_FALLBACK_API_KEY`、`KFCV50_FALLBACK_BASE_URL`、`KFCV50_FALLBACK_IMAGE_MODEL`
- 鉴权头：`Authorization: Bearer $KFCV50_API_KEY`
- Content-Type: `application/json`

## 推荐用途

在 `product-video-pipeline` 中，本接口只用于“文生图/参考图生图”阶段，可替代即梦 `text2image` 生成视频首帧图片。后续图生视频默认使用 `dreamina-cli`；只有用户明确指定可灵、Kling 或 API 生视频时才使用 `kling-api`。

## Request Body

```json
{
  "model": "gpt-image-2",
  "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
  "image": [],
  "size": "1152x2048",
  "response_format": "url"
}
```

字段说明：

- `model`，string，必填。固定使用已实测可用的 `gpt-image-2`。
- `prompt`，string，必填。图片生成提示词。
- `image`，array，可选。纯文生图时传空数组；参考图生图能力尚未实测。
- `size`，string，必填。易纸箱竖屏 2K 首帧默认传 `1152x2048`，计算方式为长边 2048、宽度 2048 × 9 ÷ 16 = 1152。历史实测 `1024x1024` 可用；`1152x2048` 首次批量调用前建议先做小样本验证。
- `response_format`，string，可选。固定传 `url`，便于下载图片并回填素材清单。

## Skill 默认参数

易纸箱竖屏宣传视频首帧生图，默认先使用：

```json
{
  "model": "gpt-image-2",
  "image": [],
  "size": "1152x2048",
  "response_format": "url"
}
```

`prompt` 使用 `02-prompts.json` 中每条素材的 `image_prompt`；`size` 使用 `02-prompts.json` 的 `image_size`，默认应为 `1152x2048`。首次批量调用前，不额外生成测试图，使用第一张正式图片兼做当前通道出图探测。

## 运行时策略

### 零成本配置检查

正式请求前只检查配置，不消耗额度：

- `.env` 或系统环境变量中存在 `KFCV50_API_KEY`。
- `KFCV50_BASE_URL` 为空时使用 `https://www.right.codes/draw`。
- `KFCV50_IMAGE_MODEL` 为空时使用 `gpt-image-2`。
- `KFCV50_FALLBACK_ENABLED=true` 时，`KFCV50_FALLBACK_API_KEY`、`KFCV50_FALLBACK_BASE_URL`、`KFCV50_FALLBACK_IMAGE_MODEL` 必须同时非空。

### 首张正式图探测

1. 读取 `02-prompts.json` 第一条素材。
2. 用该素材的正式 `image_prompt`、`image_size` 和计划 `image_file` 请求主 API。
3. 主 API 成功时，立即下载并回填 manifest，再启动后续队列。
4. 主 API 失败时，按单张重试策略处理。
5. 主 API 最终失败且备用 API 已启用并完整配置时，自动用备用 API 处理第一张。
6. 主 API 和备用 API 都失败时，停止后续队列并反馈失败原因。

探测结果应写入第一张正式素材对应的 manifest 项：`probe_mode: first_formal_image`、`probe_asset_id`、`probe_provider`、`probe_model`、`probe_size`、`probe_status`、`probe_error`、`probe_checked_at`。

### 小并发队列

首张探测成功后，剩余素材按 `02-prompts.json` 顺序进入队列：

- 默认并发上限为 `2`。
- 每个请求只生成 1 张图片。
- 哪张先完成，就先下载到对应 `images/<id>.png` 并回填对应 manifest 项。
- 回填必须按素材 ID 定位，不依赖请求完成顺序。

### 单张重试和错误分类

临时错误默认最多尝试 10 次，等待节奏为 10 秒、20 秒、30 秒、45 秒、60 秒，之后每次 60 秒。适用错误包括网络超时、5xx、临时限流和下载 URL 短暂不可用。

以下错误不应继续重试同一主 API：鉴权失败、余额不足、模型不存在、尺寸不支持、明确的 prompt 安全拒绝。若备用 API 已启用且配置完整，直接切换备用 API；否则停止当前图片处理并提示用户修正配置或提示词。

### 备用 API fallback

自动 fallback 只支持同调用格式的 RightCode Draw 备用 API。切换到备用 API 不需要再次提示用户，因为 `.env` 已显式启用同格式备用通道。

`dreamina-cli` 属于不同 provider，不得自动 fallback。需要使用 `dreamina-cli` 重新生成失败项时，必须先暂停并取得用户确认。

## Curl 示例

```bash
curl "https://www.right.codes/draw/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KFCV50_API_KEY" \
  -d '{
    "model": "gpt-image-2",
    "prompt": "一名亚裔男性仓库主管站在凌乱的纸箱堆前，表情焦虑，写实摄影风格，竖屏构图，不要生成字幕、文字、水印或品牌标志",
    "image": [],
    "size": "1152x2048",
    "response_format": "url"
  }'
```

## 历史 `1024x1024` 已实测成功响应

以下响应来自历史 `1024x1024` 调用，不代表 `1152x2048` 已稳定验证。

```json
{
  "data": [
    {
      "url": "https://image-videofile.oss-accelerate.aliyuncs.com/codex/48bc5a69-bf40-4baf-b094-570abd338e15.png"
    }
  ],
  "created": 1779787463,
  "usage": {
    "input_tokens": 187,
    "output_tokens": 7024,
    "total_tokens": 7211,
    "input_tokens_details": {
      "text_tokens": 187,
      "image_tokens": 0
    },
    "output_tokens_details": {
      "text_tokens": 0,
      "image_tokens": 7024
    }
  }
}
```

图片 URL 字段路径：`data[0].url`。

## 下载与回填规则

生成成功后：

1. 读取 `data[0].url`。
2. 下载图片到 `images/<id>.png`，其中 `<id>` 来自 `02-prompts.json` 的痛点素材 ID。
3. 在 `asset-manifest.json` 回填：
   - `image_status`: `generated`
   - `image_attempts`: 主 API 实际尝试次数
   - `image_provider`: `kfcv50-primary` 或 `kfcv50-fallback`
   - `image_model`: 实际使用的模型
   - `image_size`: `1152x2048`
   - `image_task_id`，如果响应中提供任务 ID；没有则填 `null`
   - `image_original_url`: `data[0].url`
   - `image_original_file`，如果实际下载文件名不是计划文件名
   - `image_fallback_used`: 是否使用备用 API
   - `image_fallback_from`: 使用备用 API 时填 `kfcv50-primary`
   - `image_fallback_reason`: 使用备用 API 时填主 API 失败摘要
   - `image_fallback_attempts`: 备用 API 实际尝试次数；未使用时为 `0`
   - `image_approved`: `false`

最终失败时不要静默跳过，在对应素材中回填：

- `image_status`: `failed`
- `image_attempts`: 主 API 实际尝试次数
- `image_error`: 最终错误摘要
- `image_last_attempt_at`: 最后一次尝试时间
- `image_provider`: 最后使用的 provider
- `image_model`: 最后使用的模型
- `image_size`: `1152x2048`
- `image_fallback_used`: 是否已尝试备用 API
- `image_fallback_attempts`: 备用 API 实际尝试次数；未启用时为 `0`
- `image_approved`: `false`

## 使用前检查

实际调用前先确认：

- 用户授权使用 RightCode Draw 三方服务并消耗额度。
- 已完成零成本配置检查。
- `image_prompt` 已包含“不要生成字幕、文字、水印或品牌标志”。
- `image_size` 为 `1152x2048`。
- 输出文件名遵守 `images/<id>.png`，不要依赖远端 URL 文件名。
- 自动 fallback 只会切到同格式 RightCode Draw 备用 API，不会切到 `dreamina-cli`。

## 待实测清单

- 确认 `1152x2048` 在当前通道的稳定性和费用。
- 参考图生图时 `image` 字段接受 URL、base64 还是文件上传结果。
- 失败响应格式，例如余额不足、模型不可用、prompt 违规。
- 图片 URL 的有效期。
