---
name: product-video-pipeline
description: Use when 用户要把易纸箱产品宣传脚本、产品介绍、卖点文案或旁白内容制作成竖屏宣传视频，尤其提到易纸箱宣传视频、产品宣传脚本、痛点提炼、生图、生视频、即梦 CLI、剪映草稿或剪映拼接方案时。
---

# 易纸箱宣传视频生产流程

## 核心原则

把用户提供的易纸箱产品宣传脚本、产品介绍或旁白文本，转换为可执行的视频生产资料：痛点分析、剪辑思路、AI 生图提示词、AI 图生视频提示词、媒体生成命令/请求清单、素材映射和剪映草稿拼接方案。

保持“易纸箱产品宣传视频”这个专用场景，不扩展成通用短视频生成器。

## 先判断输入

用户至少要提供产品宣传脚本、产品介绍、卖点文本或旁白内容。

如果用户只说“做一个易纸箱宣传视频”之类的模糊目标，先索要脚本、旁白稿、卖点列表，或询问是否需要先起草脚本。不要凭空生成完整项目。

## Skill 文件结构

```text
product-video-pipeline/
├── SKILL.md                                  # 技能入口：触发场景、标准执行流程、provider 路由、硬约束和自检
├── references/
│   ├── analysis-editing.md                 # 痛点分析和剪辑思路参考：生成 01-analysis.md
│   ├── prompt-spec.md                       # 提示词规范：中文写实风格、JSON 字段、image_size、首帧命名和时长估算
│   ├── gpt-image-api.md                     # KFC V50 三方 gpt-image-2 生图接口参考：首帧文生图、尺寸、下载和 manifest 回填
│   ├── dreamina-cli.md                      # 即梦执行规范：可选文生图、用户指定时的图生视频和 manifest 回填
│   ├── kling-api.md                         # 可灵图生视频 API 执行规范：默认视频 provider、任务查询和 manifest 回填
│   ├── jianying-plan.md                     # 剪映方案规范：素材顺序、字幕旁白、待生成标记和首帧图片列
│   └── seedance-cli.md                      # 即梦 CLI 底层参考：安装登录、查询下载和图生视频命令
├── templates/
│   ├── prompts.schema.json                  # 02-prompts.json 结构校验模板（纯 JSON）
│   ├── asset-manifest.schema.json           # asset-manifest.json 结构校验模板（纯 JSON）
│   └── media-commands.md                    # 03-media-commands.md 命令/请求清单模板
└── evals/
    └── evals.json                           # 技能评测用例：输入不足、提示词、provider 路由、命令、时长和生成约束
```

Markdown 参考文件和 Markdown 模板文件应在文件开头写 `name` 与 `description` frontmatter。JSON 文件必须保持合法 JSON，不写 frontmatter。

## 输出文件

默认输出到 `outputs/<project>/`：

```text
outputs/<project>/
├── 01-analysis.md
├── 02-prompts.json
├── 03-media-commands.md
├── asset-manifest.json
├── images/
├── videos/
└── jianying-draft-plan.md
```

所选生图 provider 或生视频 provider 不可用时，仍生成除实际媒体以外的文档，并说明卡在“素材生成”。

## Provider 选择规则

生图 provider 必须由用户选择：`gpt-image-2` 使用 KFC V50 的 gpt-image-2 API，默认目标尺寸 `1152x2048`；`dreamina-cli` 使用即梦 CLI text2image，参数为 `--ratio=9:16` 和 `--resolution_type=2k`。

如果用户要求生成命令清单或实际生成素材，但没有指定生图 provider，先询问用户选择 `gpt-image-2` 还是 `dreamina-cli`，不要默认选择。

生视频 provider 默认 `kling-api`；只有用户明确指定即梦、Dreamina、Seedance 或 CLI 生视频时，才使用 `dreamina-cli`。

## 标准执行流程

按下面顺序执行。用户只要求其中一部分时，可以从对应步骤开始或在对应步骤停止；但不要跳过该步骤要求读取的参考文件。

| 步骤 | 动作 | 必读文件 | 输出 |
| --- | --- | --- | --- |
| 第 1 步 | 判断输入是否足够；缺少脚本或产品文本时先向用户索要 | 本文件“先判断输入” | 是否继续执行的决定 |
| 第 2 步 | 提炼痛点，规划剪辑思路 | `references/analysis-editing.md` | `01-analysis.md` |
| 第 3 步 | 生成中文写实生图/图生视频提示词，估算每条视频时长，规划素材命名 | `references/prompt-spec.md` | `02-prompts.json`、`asset-manifest.json` |
| 第 4 步 | 生成媒体命令/请求清单：按生图 provider 条件读取 `references/gpt-image-api.md` 或 `references/dreamina-cli.md`，按生视频 provider 条件读取 `references/kling-api.md` 或 `references/dreamina-cli.md` | 对应 provider 参考文件、`templates/media-commands.md` | `03-media-commands.md` |
| 第 5 步 | 用户要求实际生成素材时，按 provider 路由生成首帧图片和视频；否则跳过 | 对应 provider 参考文件 | `images/`、`videos/`，并回填 `asset-manifest.json` |
| 第 6 步 | 生成剪映草稿拼接方案 | `references/jianying-plan.md` | `jianying-draft-plan.md` |
| 第 7 步 | 按完成前自检逐项检查 | 本文件“完成前自检” | 最终回复 |

## 按需执行规则

- 用户只要痛点分析：执行第 1-2 步。
- 用户只要提示词：执行第 1-3 步。
- 用户要可复制的媒体生成命令/请求：执行第 1-4 步。
- 用户要实际生成图片或视频：执行第 1-5 步。
- 用户要剪映方案或完整资料：执行第 1-6 步。

结构校验可参考：

- `templates/prompts.schema.json`
- `templates/asset-manifest.schema.json`

## 硬约束

- 提示词必须使用中文写实风格。
- 只生成痛点段落素材，不提前展示解决方案。
- 人物必须写明亚裔男性或亚裔女性。
- `image_file` 按痛点 ID 命名为 `images/<id>.png`，不要依赖 provider 返回的原始文件名。
- `02-prompts.json` 每条素材必须包含 `aspect_ratio: "9:16"` 和 `image_size: "1152x2048"`。
- `video_prompt` 只描述画面运动、人物微动作、环境动态和情绪变化，不写首帧路径或视频时长。
- `video_prompt` 必须包含“不要生成字幕、文字、水印或品牌标志”。
- `subtitle` 即该镜头旁白，用于估算 `duration_seconds`；不要单独创建 `voiceover` 字段。
- `duration_seconds` 按 `subtitle` 语速估算，不固定为 5 秒。
- 实际生成素材时必须维护 `asset-manifest.json`，回填 image/video provider、model、task ID、远端 URL 或原始文件名。
- 即梦图生视频只有用户指定 `dreamina-cli` 视频 provider 时使用；该路径必须包含 `--model_version=seedance2.0fast` 和 `--video_resolution=720p`。
- 没有剪映 MCP 时，只输出剪映草稿拼接方案，不声称已经创建草稿。

## 完成前自检

交付前检查：

- 是否使用了用户提供的脚本或产品文本，而不是凭空生成项目。
- `01-analysis.md` 的痛点是否和 `02-prompts.json` 一一对应。
- `02-prompts.json` 是否是合法 JSON，且每条都是 9:16 竖屏痛点素材并包含 `image_size`。
- 每条 `video_prompt` 是否只描述画面，不包含首帧路径或视频时长。
- 每条 `video_prompt` 是否包含“不要生成字幕、文字、水印或品牌标志”。
- 是否没有生成 `voiceover` 字段。
- 每条 `duration_seconds` 是否按 `subtitle` 估算，并写明 `duration_basis`。
- `asset-manifest.json` 是否记录计划文件名；实际生成后是否补充 provider、model、task ID、远端 URL 或原始文件名。
- `03-media-commands.md` 的生图命令/请求、`--image` 或图片引用、`--duration` 或时长参数是否与 JSON 一致。
- 生图 provider 是否由用户选择；未选择时是否先询问。
- 生视频 provider 是否默认 `kling-api`，或在用户明确指定即梦、Dreamina、Seedance、CLI 生视频时才使用 `dreamina-cli`。
- 即梦参数 `--model_version=seedance2.0fast` 和 `--video_resolution=720p` 是否只在 `dreamina-cli` 视频 provider 下检查。
- 剪映方案是否区分“已生成文件”和“待生成文件”，并保留首帧图片对应关系。
