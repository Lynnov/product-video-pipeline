---
name: kling-api
description: 易纸箱视频流程中默认使用可灵 API 图生视频的执行规范，定义生成前检查、JWT 鉴权、请求字段、任务查询、下载和 manifest 回填规则。
---

# 可灵 API 图生视频执行规范

本文件用于 `product-video-pipeline` 的默认生视频 provider。除非用户明确指定即梦/Dreamina/Seedance/CLI 生视频，否则图生视频按可灵 API 路径执行。

官方文档来源：`https://klingai.com/document-api/apiReference/model/imageToVideo`、`https://klingai.com/document-api/apiReference/commonInfo`。

## 基础信息

- Base URL: `https://api-beijing.klingai.com`
- 创建任务：`POST /v1/videos/image2video`
- 查询单个任务：`GET /v1/videos/image2video/{task_id}`
- 查询任务列表：`GET /v1/videos/image2video?pageNum=1&pageSize=30`
- `Content-Type`: `application/json`
- `Authorization`: `Bearer <token>`

新系统调用域名已从 `https://api.klingai.com` 变更为 `https://api-beijing.klingai.com`。

## 鉴权

实际调用前确认环境变量存在：

- `KLING_ACCESS_KEY`
- `KLING_SECRET_KEY`

每次请求前用 AK/SK 生成 JWT token：

- Header: `{ "alg": "HS256", "typ": "JWT" }`
- Payload:
  - `iss`: `KLING_ACCESS_KEY`
  - `exp`: 当前 Unix 秒级时间戳 + 1800
  - `nbf`: 当前 Unix 秒级时间戳 - 5
- Signature: 使用 `KLING_SECRET_KEY` 按 HS256 签名

Authorization 组装为：`Authorization: Bearer <JWT token>`。

Python 参考：

```python
import time
import jwt

def encode_jwt_token(ak, sk):
    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5,
    }
    return jwt.encode(payload, sk, headers=headers)
```

## 生成前检查

如果密钥缺失、用户未授权调用外部服务、余额不足或接口不可用，停止在素材生成前；保留 `01-analysis.md`、`02-prompts.json`、`asset-manifest.json`、`03-media-commands.md` 和 `jianying-draft-plan.md`。

错误响应仍可能是 HTTP 200 外加业务 `code` 非 0；判断成功时同时检查 HTTP 状态和响应体 `code`。

常见错误：

- `401 / 1000-1004`：鉴权失败、Authorization 为空/非法、token 未生效或已失效。
- `429 / 1101-1102`：账户欠费或资源包用完。
- `403 / 1103`：接口或模型无权限。
- `400 / 1200-1201`：请求参数非法。
- `400 / 1301`：触发内容安全策略。
- `429 / 1302-1303`：请求过快、并发或 QPS 超限。
- `500/503/504`：服务端错误、维护或内部超时。

## 请求输入

每个痛点视频使用 `02-prompts.json` 中同一条记录的：

- `image_file`
- `video_prompt`
- `duration_seconds`
- `video_file`

`video_prompt` 只描述画面运动、人物微动作、环境动态和情绪变化；不要把首帧路径或视频时长写进提示词正文。

## 创建任务 Request Body

易纸箱流程默认使用单图首帧图生视频。将已生成的 `image_file` 转为公网可访问 URL 或 Base64 字符串后传给 `image`。

```json
{
  "model_name": "kling-v2-6",
  "image": "<public_image_url_or_base64>",
  "prompt": "<video_prompt>",
  "negative_prompt": "",
  "duration": "<duration_seconds>",
  "mode": "std",
  "sound": "off",
  "callback_url": "",
  "external_task_id": ""
}
```

字段规则：

- `model_name`，可选，默认 `kling-v1`。官方枚举包含 `kling-v1`、`kling-v1-5`、`kling-v1-6`、`kling-v2-master`、`kling-v2-1`、`kling-v2-1-master`、`kling-v2-5-turbo`、`kling-v2-6`、`kling-v3`。易纸箱默认先用 `kling-v2-6`，如用户指定其他模型则按用户指定。
- `image`，可选但 `image` 和 `image_tail` 至少二选一。支持图片 Base64 或可访问 URL；Base64 不要带 `data:image/png;base64,` 前缀。支持 `.jpg`、`.jpeg`、`.png`，文件不超过 10MB，宽高不小于 300px，宽高比在 `1:2.5` 到 `2.5:1` 之间。
- `image_tail`，可选，尾帧控制；本流程默认不使用。
- `prompt`，可选但单镜头模式不得为空，不超过 2500 字符。
- `negative_prompt`，可选，不超过 2500 字符；官方建议也可在正向提示词中补充负向约束。
- `duration`，string，可选，默认 `5`，单位秒。官方通用枚举为 `3` 到 `15` 的整数字符串，但不同模型版本支持范围不同。本流程使用 `duration_seconds` 转字符串前，需按实际模型能力校验；2026-05-27 实测 `kling-v2-6` 拒绝 `"6"` 并返回 `1201 duration value '6' is invalid`，改用 `"5"` 后通过参数校验但因账户余额不足停止。同日实测 `kling-v3` 搭配 `"6"` 通过参数校验，随后因账户余额不足返回 `1102 Account balance not enough`。
- `mode`，可选，默认 `std`。`std` 输出 720P；`pro` 输出 1080P；`4k` 输出 4K。
- `sound`，可选，默认 `off`；本流程默认 `off`。
- `cfg_scale`，可选，默认 `0.5`，范围 `[0, 1]`；`kling-v2.x` 模型不支持该参数，因此默认不传。
- `watermark_info`，可选，格式 `{ "enabled": boolean }`。
- `callback_url`，可选；不配置时使用轮询查询。
- `external_task_id`，可选；用户自定义任务 ID，单用户下需要唯一，可用于查询任务。

不要在默认请求中加入 `multi_shot`、`image_tail`、`camera_control`、`static_mask`、`dynamic_masks`、`element_list`、`voice_list`，除非用户明确要求对应能力。

## 创建任务示例

```bash
curl --location --request POST 'https://api-beijing.klingai.com/v1/videos/image2video' \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data-raw '{
    "model_name": "kling-v2-6",
    "image": "<public_image_url_or_base64>",
    "prompt": "镜头缓慢推近，人物翻找单据，桌面纸张轻微晃动；不要生成字幕、文字、水印或品牌标志。",
    "negative_prompt": "",
    "duration": "6",
    "mode": "std",
    "sound": "off",
    "callback_url": "",
    "external_task_id": ""
  }'
```

## 创建任务响应

成功提交时响应结构：

```json
{
  "code": 0,
  "message": "string",
  "request_id": "string",
  "data": {
    "task_id": "string",
    "task_info": {
      "external_task_id": "string"
    },
    "task_status": "submitted",
    "created_at": 1722769557708,
    "updated_at": 1722769557708
  }
}
```

`data.task_id` 回填到 `asset-manifest.json` 的 `video_task_id`。

## 查询任务

单任务查询：

```bash
curl --request GET \
  --url 'https://api-beijing.klingai.com/v1/videos/image2video/<task_id>' \
  --header 'Authorization: Bearer <token>'
```

任务状态字段：`data.task_status`，枚举值：

- `submitted`
- `processing`
- `succeed`
- `failed`

失败原因字段：`data.task_status_msg`。

成功时结果字段：

```json
{
  "data": {
    "task_id": "string",
    "task_status": "succeed",
    "task_status_msg": "string",
    "task_result": {
      "videos": [
        {
          "id": "string",
          "url": "string",
          "watermark_url": "string",
          "duration": "string"
        }
      ]
    },
    "final_unit_deduction": "string"
  }
}
```

`data.task_result.videos[0].url` 是无水印生成视频 URL。官方说明生成的视频 URL 会在 30 天后清理，必须及时下载并转存。

列表查询只用于排查或补查：

```bash
curl --request GET \
  --url 'https://api-beijing.klingai.com/v1/videos/image2video?pageNum=1&pageSize=30' \
  --header 'Authorization: Bearer <token>'
```

## 轮询和下载

未配置 `callback_url` 时，提交后轮询 `GET /v1/videos/image2video/{task_id}`：

1. `submitted` / `processing`：继续等待。
2. `succeed`：读取 `data.task_result.videos[0].url`，下载到 `videos/<id>.mp4`。
3. `failed`：停止该任务，记录 `data.task_status_msg`。

建议从 10-15 秒间隔开始轮询；如果多次仍为处理中，逐步放大间隔，避免触发 `429 / 1302-1303` 速率或并发限制。

## 命令/请求清单规则

在 `03-media-commands.md` 中为每个痛点输出一个可灵图生视频请求块，包含：

- 输入首帧：`./outputs/<project>/<image_file>`，并说明需要转成公网 URL 或 Base64 后传入 `image`
- 输出视频：`./outputs/<project>/<video_file>`
- 提示词：`video_prompt`
- 时长：`duration_seconds` 转字符串传给 `duration`
- provider：`kling-api`
- endpoint：`POST https://api-beijing.klingai.com/v1/videos/image2video`
- 查询：`GET https://api-beijing.klingai.com/v1/videos/image2video/<task_id>`

## 回填规则

生成成功后，在 `asset-manifest.json` 回填：

- `video_provider`: `kling-api`
- `video_model`: 实际请求的 `model_name`
- `video_task_id`: 创建任务响应的 `data.task_id`
- `video_original_url`: 查询响应的 `data.task_result.videos[0].url`
- `video_original_file`，如果下载文件名不是计划文件名
- `video_actual_duration_seconds`: 查询响应的 `data.task_result.videos[0].duration` 转为数字；如果缺失则填 `null`

下载后按 `video_file` 重命名，例如 `videos/pain-01.mp4`。后续剪映方案只引用计划文件名，不引用远端 URL 或临时文件名。
