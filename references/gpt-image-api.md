---
name: gpt-image-api
description: KFC V50 第三方 gpt-image-2 生图接口参考，供易纸箱视频流程在需要替代或补充即梦文生图时使用。
---

# GPT Image API 接入参考

本文档记录 KFC V50 中转的 `gpt-image-2` 生图接口。该接口历史实测尺寸为 `1024x1024`；当前易纸箱目标默认尺寸为 `1152x2048`，批量使用前仍需小样本验证。

## 基础信息

- Provider: KFC V50
- Base URL: `https://kfcv50.link`
- Endpoint: `POST /v1/images/generations`
- Full URL: `https://kfcv50.link/v1/images/generations`
- 环境变量：`KFCV50_API_KEY`
- 鉴权头：`Authorization: Bearer $KFCV50_API_KEY`
- Content-Type: `application/json`

## 推荐用途

在 `product-video-pipeline` 中，本接口只用于“文生图/参考图生图”阶段，可替代即梦 `text2image` 生成视频首帧图片。后续图生视频默认使用 `kling-api`；只有用户明确指定即梦/Dreamina/Seedance/CLI 生视频时才使用 Dreamina/Seedance。

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

`prompt` 使用 `02-prompts.json` 中每条素材的 `image_prompt`；`size` 使用 `02-prompts.json` 的 `image_size`，默认应为 `1152x2048`。首次批量调用前，先用小样本验证当前通道对该尺寸的稳定性和费用。

## Curl 示例

```bash
curl "https://kfcv50.link/v1/images/generations" \
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
   - `image_provider`: `gpt-image-2`
   - `image_model`: `gpt-image-2`
   - `image_size`: `1152x2048`
   - `image_task_id`，如果响应中提供任务 ID
   - `image_original_url`: `data[0].url`
   - `image_original_file`，如果实际下载文件名不是计划文件名

## 使用前检查

实际调用前先确认：

- 用户授权使用 KFC V50 三方服务并消耗额度。
- `.env` 或系统环境变量中存在 `KFCV50_API_KEY`。
- `image_prompt` 已包含“不要生成字幕、文字、水印或品牌标志”。
- `image_size` 为 `1152x2048`。
- 输出文件名遵守 `images/<id>.png`，不要依赖远端 URL 文件名。

## 待实测清单

- 确认 `1152x2048` 在当前通道的稳定性和费用。
- 参考图生图时 `image` 字段接受 URL、base64 还是文件上传结果。
- 失败响应格式，例如余额不足、模型不可用、prompt 违规。
- 图片 URL 的有效期。
