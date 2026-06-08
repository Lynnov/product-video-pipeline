# Product Video Pipeline Skill

`product-video-pipeline` 是一个面向「易纸箱」产品宣传视频的 Claude Code Skill。它把产品脚本、卖点文案或旁白稿，整理成一套可执行的视频生产资料：痛点分析、AI 生图提示词、AI 图生视频提示词、媒体生成命令/请求清单、素材映射表、图片确认流程和剪映草稿输入或拼接方案。

这个 Skill 不是通用短视频生成器。它专门服务易纸箱宣传片，重点处理纸箱厂老板、业务、财务、仓库等真实经营场景中的痛点素材。

## 适合什么场景

适合以下需求：

- 把易纸箱产品介绍改成竖屏宣传视频生产资料。
- 从脚本里提炼痛点段落，并生成对应镜头提示词。
- 为每个痛点镜头生成首帧图片提示词和图生视频提示词。
- 生成可复制执行的媒体生成命令或 API 请求清单。
- 生成剪映草稿输入或拼接方案，方便后期照着剪。
- 默认使用 `gpt-image-2` 生图、`dreamina-cli` 生视频，也支持用户明确指定即梦 CLI 或可灵 API。

不适合以下需求：

- 非易纸箱品牌的通用短视频脚本。
- 在未验证本地剪映草稿工具时，声称已经创建可打开的完整剪映工程文件。
- 自动剪辑成片并发布。
- 不提供脚本、旁白或产品卖点时直接凭空生成完整项目。

## 能输出什么

默认输出到：

```text
outputs/<project>/
├── 01-analysis.md
├── 02-prompts.json
├── 03-media-commands.md
├── asset-manifest.json
├── images/
├── videos/
├── subtitles/
├── jianying-draft/
└── jianying-draft-plan.md
```

各文件用途：

| 文件 | 用途 |
| --- | --- |
| `01-analysis.md` | 从脚本中提炼痛点，并规划剪辑节奏。 |
| `02-prompts.json` | 每个痛点镜头的生图提示词、图生视频提示词、字幕、时长和素材命名。 |
| `03-media-commands.md` | 按 provider 生成可复制的生图命令、图生视频请求或 CLI 命令。 |
| `asset-manifest.json` | 素材映射表，记录计划文件名、provider、模型、任务 ID、远端 URL、图片确认状态和实际时长。 |
| `images/` | 首帧图片输出目录；默认先全部生成并等待确认。 |
| `videos/` | 图生视频输出目录；全部图片确认后才生成。 |
| `subtitles/` | 剪映草稿输入需要的字幕文件，例如 `draft.srt`。 |
| `jianying-draft/` | 剪映草稿输入目录；无原生草稿工具时至少写入 `timeline.json`。 |
| `jianying-draft-plan.md` | 剪映拼接方案，包含素材顺序、字幕、旁白、转场和音效建议。 |

## 安装方式

### 方式一：作为独立仓库使用

```bash
git clone https://github.com/Lynnov/product-video-pipeline.git
cd product-video-pipeline
```

然后把这个目录放到 Claude Code 可以读取的 skills 目录中，或在 Claude Code 里直接引用本目录的 `SKILL.md`。

### 方式二：放入 Claude Code skills 目录

如果你的 Claude Code skills 目录类似：

```text
~/.claude/skills/
```

可以将仓库克隆到：

```bash
cd ~/.claude/skills
git clone https://github.com/Lynnov/product-video-pipeline.git
```

安装后，Claude Code 在相关任务中会根据 `SKILL.md` 的描述自动触发这个 Skill。

## 环境变量配置

复制示例文件：

```bash
cp .env.example .env
```

按需填写：

```bash
KFCV50_API_KEY=your-kfcv50-api-key
KLING_ACCESS_KEY=your-kling-access-key
KLING_SECRET_KEY=your-kling-secret-key
```

说明：

| 变量 | 是否必需 | 用途 |
| --- | --- | --- |
| `KFCV50_API_KEY` | 使用 `gpt-image-2` 生图时必需 | 调用 KFC V50 中转的 `gpt-image-2` 图片生成接口。 |
| `KLING_ACCESS_KEY` | 使用可灵 API 生视频时必需 | 可灵 API Access Key。 |
| `KLING_SECRET_KEY` | 使用可灵 API 生视频时必需 | 可灵 API Secret Key，用于生成 JWT。 |

`.env` 已被 `.gitignore` 排除，不要提交真实密钥。

## Provider 选择规则

默认 provider：

- 生图默认 `gpt-image-2`。
- 生视频默认 `dreamina-cli`。
- 用户明确指定时才切换到其他 provider。

### 生图 provider

| Provider | 用途 | 说明 |
| --- | --- | --- |
| `gpt-image-2` | 默认 API 生图路径 | 使用 KFC V50 中转接口，目标尺寸为 `1152x2048`。 |
| `dreamina-cli` | 用户明确指定即梦、Dreamina 或 CLI 生图时使用 | 使用 `dreamina text2image --ratio=9:16 --resolution_type=2k`。 |

### 生视频 provider

| Provider | 用途 | 说明 |
| --- | --- | --- |
| `dreamina-cli` | 默认图生视频路径 | 使用 `dreamina image2video`，默认 `seedance2.0fast`、720p。 |
| `kling-api` | 用户明确指定可灵、Kling 或 API 生视频时使用 | 使用可灵 API 图生视频接口。 |

## 图片确认与重生成规则

完整流程必须先生成全部首帧图片，然后暂停等待用户确认。

用户逐张确认图片时：

- 满意：在 `asset-manifest.json` 中标记 `image_approved: true`。
- 不满意且无修改意见：使用原 `image_prompt` 重新生成该图片。
- 不满意且有修改意见：把修改意见合并进原提示词，写入 `image_revision_prompt` 后重新生成该图片。

只有全部图片确认后，才继续生成视频。

## 图片尺寸规则

所有痛点素材默认是竖屏 9:16。

2K 竖屏图片尺寸统一为：

```text
1152x2048
```

计算方式：

```text
长边 = 2048
宽度 = 2048 × 9 ÷ 16 = 1152
```

因此 `02-prompts.json` 每条都应包含：

```json
{
  "aspect_ratio": "9:16",
  "image_size": "1152x2048"
}
```

## 最常用的使用方式

### 只生成完整生产资料，不实际调用 API

给 Claude Code：

```text
请使用 product-video-pipeline skill，基于 视频脚本/客户管理.md 生成完整视频生产资料。
生图默认用 gpt-image-2，生视频默认用 dreamina-cli。
先不要实际调用外部生成接口。
```

Claude 应输出：

```text
outputs/客户管理/
├── 01-analysis.md
├── 02-prompts.json
├── 03-media-commands.md
├── asset-manifest.json
└── jianying-draft-plan.md
```

### 实际生成首帧图片

给 Claude Code：

```text
使用 product-video-pipeline，基于 outputs/客户管理/02-prompts.json，
用 gpt-image-2 生成所有首帧图片，并回填 asset-manifest.json。
```

生成后应得到：

```text
outputs/客户管理/images/pain-01.png
outputs/客户管理/images/pain-02.png
...
```

并在 `asset-manifest.json` 中回填：

```json
{
  "image_provider": "gpt-image-2",
  "image_model": "gpt-image-2",
  "image_size": "1152x2048",
  "image_original_url": "https://..."
}
```

### 默认用即梦 CLI 生成视频

全部图片确认后，默认用 `dreamina-cli` 生成视频：

```text
用 product-video-pipeline，基于 outputs/客户管理 已确认的首帧图片生成视频。
```

对应命令形态：

```bash
dreamina image2video \
  --image ./outputs/客户管理/images/pain-01.png \
  --prompt="<video_prompt>" \
  --duration=<duration_seconds> \
  --model_version=seedance2.0fast \
  --video_resolution=720p \
  --poll=30
```

生成完成后查询并下载：

```bash
download_dir=$(mktemp -d ./outputs/客户管理/videos/pain-01.download.XXXXXX)
dreamina query_result --submit_id=<video_task_id> --download_dir="$download_dir"
original_file=$(ls -t "$download_dir" | head -1)
test -n "$original_file"
mv "$download_dir/$original_file" ./outputs/客户管理/videos/pain-01.mp4
rmdir "$download_dir"
```

并回填：

```json
{
  "video_provider": "dreamina-cli",
  "video_model": "seedance2.0fast",
  "video_task_id": "...",
  "video_original_file": "...",
  "video_actual_duration_seconds": 6.0
}
```

### 明确指定可灵 API 生成视频

如果用户明确指定可灵、Kling 或 API 生视频：

```text
用 product-video-pipeline 的 kling-api 路径，基于 outputs/客户管理/images/pain-01.png 生成第一个视频。
```

可灵 API 会用：

```text
POST https://api-beijing.klingai.com/v1/videos/image2video
```

成功后应下载到：

```text
outputs/客户管理/videos/pain-01.mp4
```

并回填：

```json
{
  "video_provider": "kling-api",
  "video_model": "kling-v3",
  "video_task_id": "...",
  "video_original_url": "https://...",
  "video_actual_duration_seconds": 6.0
}
```

## 示例脚本

仓库中带了两个示例脚本：

```text
视频脚本/客户管理.md
视频脚本/库存管理.md
```

可以直接让 Claude Code 用它们测试：

```text
请使用 product-video-pipeline，基于 视频脚本/客户管理.md 生成完整视频生产资料。
生图默认用 gpt-image-2，生视频默认用 dreamina-cli。
```

## 重要约束

生成资料时需要遵守：

- 只为痛点段落生成素材，不提前展示解决方案。
- 提示词使用中文写实风格。
- 人物必须明确写“亚裔男性”或“亚裔女性”。
- `video_prompt` 只描述画面运动、人物微动作、环境动态和情绪变化。
- `video_prompt` 不写首帧路径，也不写视频时长。
- `video_prompt` 必须包含“不要生成字幕、文字、水印或品牌标志”。
- 不创建 `voiceover` 字段，旁白统一使用 `subtitle`。
- `duration_seconds` 按 `subtitle` 估算，不固定写 5 秒。
- 实际生成素材后必须回填 `asset-manifest.json`。

## 目录说明

```text
product-video-pipeline/
├── SKILL.md
├── README.md
├── .env.example
├── references/
│   ├── analysis-editing.md
│   ├── prompt-spec.md
│   ├── gpt-image-api.md
│   ├── dreamina-cli.md
│   ├── kling-api.md
│   ├── seedance-cli.md
│   ├── jianying-draft-builder.md
│   └── jianying-plan.md
├── scripts/
│   ├── create_jianying_draft.py
│   └── test_create_jianying_draft.py
├── templates/
│   ├── prompts.schema.json
│   ├── asset-manifest.schema.json
│   └── media-commands.md
├── evals/
│   └── evals.json
└── 视频脚本/
    ├── 客户管理.md
    └── 库存管理.md
```

## 各参考文件什么时候看

| 文件 | 何时使用 |
| --- | --- |
| `SKILL.md` | 主流程、触发条件、provider 路由和完成前自检。 |
| `references/analysis-editing.md` | 生成 `01-analysis.md` 时读取。 |
| `references/prompt-spec.md` | 生成 `02-prompts.json` 和初始 `asset-manifest.json` 时读取。 |
| `references/gpt-image-api.md` | 使用默认 `gpt-image-2` 生图时读取。 |
| `references/dreamina-cli.md` | 使用默认 `dreamina-cli` 生视频，或用户指定即梦 CLI 生图/生视频时读取。 |
| `references/kling-api.md` | 用户明确指定可灵、Kling 或 API 生视频时读取。 |
| `references/jianying-draft-builder.md` | 生成剪映草稿输入或调用已验证草稿工具时读取。 |
| `references/jianying-plan.md` | 生成剪映拼接方案时读取。 |
| `scripts/create_jianying_draft.py` | 从已确认素材 manifest 生成 `draft.srt` 和 fallback `timeline.json`。 |
| `templates/media-commands.md` | 生成 `03-media-commands.md` 时参考。 |

## 常见问题

### 没有选择 provider，会用什么默认值？

生图默认使用 `gpt-image-2`，生视频默认使用 `dreamina-cli`。只有用户明确指定即梦 CLI 生图，或明确指定可灵、Kling、API 生视频时，才切换到对应 provider。

### 为什么生成完图片后要暂停？

完整流程必须先生成全部首帧图片并等待用户确认。用户不满意且无修改意见时，用原提示词重新生成；用户给出修改意见时，把修改意见合并进 `image_revision_prompt` 后重新生成。全部图片确认后才生成视频。

### 为什么 `gpt-image-2` 用 `1152x2048`？

因为项目默认生产 9:16 竖屏 2K 首帧。长边按 2048 计算，宽度为 1152。

### 可灵提示余额不足怎么办？

可灵常见错误 `1102` 表示账户欠费或资源包用完。需要充值、购买资源包，或改用即梦 CLI 生成视频。

### 即梦任务显示失败但本地有视频怎么办？

先用 `ffprobe` 或播放器检查本地 MP4 是否有效。如果视频可播放，可以保留文件，并在 `asset-manifest.json` 中记录 `video_task_id` 和实际时长。

### 为什么不直接声称生成了可打开的剪映草稿？

当前脚本会生成剪映草稿输入：`subtitles/draft.srt` 和 `jianying-draft/timeline.json`。只有本地实测 `cut_cli`、`pyJianYingDraft` 或可信 JianYing MCP 可用后，才可以声称创建了可打开的原生剪映草稿；否则只输出草稿输入或人工拼接方案。

## 推荐工作流

1. 准备一段易纸箱产品脚本。
2. 让 Claude Code 从第 1 步开始执行完整流程。
3. 默认用 `gpt-image-2` 生成全部首帧图片。
4. 检查每张图片。
5. 不满意且无修改意见时，直接重新生成该图片。
6. 不满意且有修改意见时，把修改意见合并进原提示词后重新生成该图片。
7. 全部图片确认后，再默认用 `dreamina-cli` 生成视频。
8. 生成剪映草稿输入；草稿工具不可用时，生成 `jianying-draft-plan.md`。

## 安全提醒

- 不要提交 `.env`。
- 不要把 API Key 写进 README、脚本或聊天记录。
- 外部生成接口会消耗额度，实际调用前先确认 provider 和素材数量。
- 生成的视频或图片远端 URL 可能会过期，拿到后尽快下载到本地。
