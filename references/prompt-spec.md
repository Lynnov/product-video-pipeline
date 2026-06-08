---
name: prompt-spec
description: 易纸箱痛点镜头的中文写实提示词规范，定义 02-prompts.json 字段、首帧命名、素材映射、字幕旁白和按字幕估算时长的方法。
---

# 提示词与素材计划规范

## 核心原则

只为痛点段落生成素材，不提前展示易纸箱如何解决。提示词使用中文，画面为写实风格，避免卡通、科幻、夸张商业海报感。

## 画面风格

- 9:16 竖屏。
- 2K 竖屏目标尺寸为 `1152x2048`：长边按 2048，宽度为 2048 × 9 ÷ 16 = 1152。
- 中国纸箱厂、包装厂、仓库、财务办公室、业务办公室等真实工业/办公场景。
- 如果出现人物，明确写“亚裔男性”或“亚裔女性”。
- 低饱和冷灰或真实办公室光线，纪实感，电影级写实摄影。
- 不出现品牌标志，不出现可读文字。

## 字幕和旁白

`subtitle` 即该镜头旁白文案。字幕来自痛点分析中提取的痛点表达，要求短、准、贴近用户痛感。

不要单独创建 `voiceover` 字段。需要估算时长时，直接使用 `subtitle` 作为旁白文本。

## `02-prompts.json` 字段

每个痛点一项：

```json
[
  {
    "id": "pain-01",
    "pain_point": "痛点名称",
    "pain_summary": "痛点解释",
    "image_file": "images/pain-01.png",
    "video_file": "videos/pain-01.mp4",
    "image_prompt": "9:16 竖屏中文写实生图提示词。",
    "video_prompt": "镜头缓慢推近，人物翻找单据，桌面纸张轻微晃动，情绪从忙乱到焦虑；不要生成字幕、文字、水印或品牌标志。",
    "subtitle": "该镜头字幕/旁白",
    "duration_seconds": 6,
    "duration_basis": "时长估算依据",
    "style": "电影级真实工业摄影/低饱和度冷灰色调/纪实感",
    "aspect_ratio": "9:16",
    "image_size": "1152x2048"
  }
]
```

## 文件命名和首帧关系

- `image_file` 固定为 `images/<id>.png`，替代即梦返回的乱码或 submit_id 文件名。
- `video_file` 固定为 `videos/<id>.mp4`。
- 首帧图片路径属于 CLI 调用参数，不属于视频生成画面提示词。
- 不要在 `video_prompt` 中写“使用 images/<id>.png 作为首帧”或“生成 X 秒视频”，这些要求由 `image_file`、`duration_seconds` 和即梦命令负责表达。

## 视频提示词要求

`video_prompt` 只描述画面如何运动、人物如何微动、环境如何变化、情绪如何推进。

必须加入通用负向约束：不要生成字幕、文字、水印、品牌标志。

好的 `video_prompt` 示例：

```text
镜头从桌面散乱单据缓慢推近到财务人员焦虑的脸部，她快速翻动几张单据，手指在计算器和电脑表格之间来回移动，手机屏幕亮起但文字不可读，背景办公室灯光轻微闪烁，情绪从忙乱到更焦虑；不要生成字幕、文字、水印或品牌标志。
```

不要这样写：

```text
使用 images/pain-01.png 作为首帧，生成 6 秒图生视频。
```

## 时长估算

`duration_seconds` 不固定时长。先写 `subtitle`，再估算视频长度。

估算规则：

- 中文旁白约 4-5 字/秒。
- 英文约 2-3 词/秒。
- 估算后向上取整，并按镜头情绪预留 0.5-1 秒。
- 一般单条控制在 4-8 秒。
- 旁白过长时优先拆成两个痛点镜头，不生成拖沓长镜头。
- 如果即梦模型只支持有限时长档位，选择不短于估算值的最近档位，并在 `duration_basis` 写明。

`duration_basis` 示例：

```text
18 个汉字 ÷ 4.5 字/秒 ≈ 4 秒，预留翻单据和焦虑停顿后取 6 秒。
```

## `asset-manifest.json` 初始结构

生成提示词时同时生成素材映射文件，先写计划文件名，实际生成后回填 provider-aware 的模型、任务 ID、原始 URL 和原始文件名。

```json
[
  {
    "id": "pain-01",
    "image_file": "images/pain-01.png",
    "video_file": "videos/pain-01.mp4",
    "duration_seconds": 6,
    "image_provider": null,
    "image_model": null,
    "image_size": "1152x2048",
    "image_task_id": null,
    "image_original_url": null,
    "image_original_file": null,
    "image_status": "planned",
    "image_attempts": 0,
    "image_error": null,
    "image_last_attempt_at": null,
    "image_fallback_used": false,
    "image_fallback_from": null,
    "image_fallback_reason": null,
    "image_fallback_attempts": 0,
    "probe_mode": null,
    "probe_asset_id": null,
    "probe_provider": null,
    "probe_model": null,
    "probe_size": null,
    "probe_status": null,
    "probe_error": null,
    "probe_checked_at": null,
    "image_approved": false,
    "image_revision_prompt": null,
    "video_provider": null,
    "video_model": null,
    "video_task_id": null,
    "video_original_url": null,
    "video_original_file": null,
    "video_actual_duration_seconds": null
  }
]
```
