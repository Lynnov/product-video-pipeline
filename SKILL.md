---
name: product-video-pipeline
description: Use when 用户要把易纸箱产品宣传脚本、产品介绍、卖点文案或旁白内容制作成竖屏宣传视频，尤其提到易纸箱宣传视频、痛点提炼、gpt-image 生图、fallback、即梦 CLI、生视频、剪映草稿或剪映拼接方案时。
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
│   ├── gpt-image-api.md                     # RightCode Draw 三方 gpt-image-2 生图接口参考：首帧文生图、尺寸、下载和 manifest 回填
│   ├── dreamina-cli.md                      # 即梦执行规范：可选文生图、默认图生视频和 manifest 回填
│   ├── kling-api.md                         # 可灵图生视频 API 执行规范：用户指定 API 生视频时的任务查询和 manifest 回填
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

## gpt-image 生图运行时优化

当生图 provider 为 `gpt-image-2` 时，按 `references/gpt-image-api.md` 执行运行时策略：

1. 正式生图前只做零成本配置检查，不额外生成测试图。
2. 使用第一张正式图片兼做供应商出图探测；首张主 API 和备用 API 都失败时，停止后续队列。
3. 首张成功后，后续图片按素材 ID 排队小并发生成；默认并发上限为 2。
4. 每张图片成功后立即下载到计划路径，并按素材 ID 回填 `asset-manifest.json`，不等全部完成后统一回填。
5. 单张失败按参考文件中的重试和不可重试错误分类处理；最终失败必须在 manifest 写入失败状态。
6. 只有 `.env` 显式启用且完整配置同格式 RightCode Draw 备用 API 时，才自动 fallback 到备用 API。
7. `dreamina-cli` 不作为自动 fallback；切换到 `dreamina-cli` 前必须暂停并取得用户确认。
8. 全部图片处理完后统一暂停：全部成功则等待逐张确认；部分失败则汇总失败项并等待用户选择下一步。

## Provider 选择规则

生图 provider 默认使用 `gpt-image-2`。只有用户明确指定即梦、Dreamina 或 CLI 生图时，才使用 `dreamina-cli`。

生视频 provider 默认使用 `dreamina-cli`。只有用户明确指定可灵、Kling 或 API 生视频时，才使用 `kling-api`。

默认完整流程必须先生成全部首帧图片，并在图片确认环节暂停。用户确认全部图片可用后，才继续生成视频。

## 图片确认与重生成规则

实际生成图片时，必须先生成全部计划图片，然后暂停等待用户确认。

用户逐张确认图片时：

- 用户确认满意：在 `asset-manifest.json` 中标记该图片 `image_approved: true`。
- 用户不满意但没有给修改意见：使用原 `image_prompt` 重新生成同一张图片，并回填新的任务 ID、远端 URL 或原始文件名。
- 用户不满意且给了修改意见：将修改意见合并进原 `image_prompt`，生成 `image_revision_prompt`，再重新生成同一张图片，并回填新的任务 ID、远端 URL 或原始文件名。

所有图片的 `image_approved` 都为 `true` 后，才允许进入生视频步骤。

## 标准执行流程

按下面顺序执行。用户只要求其中一部分时，可以从对应步骤开始或在对应步骤停止；但不要跳过该步骤要求读取的参考文件。

| 步骤 | 动作 | 必读文件 | 输出 |
| --- | --- | --- | --- |
| 第 1 步 | 判断输入是否足够；缺少脚本或产品文本时先向用户索要 | 本文件“先判断输入” | 是否继续执行的决定 |
| 第 2 步 | 提炼痛点，规划剪辑思路 | `references/analysis-editing.md` | `01-analysis.md` |
| 第 3 步 | 生成中文写实生图/图生视频提示词，估算每条视频时长，规划素材命名 | `references/prompt-spec.md` | `02-prompts.json`、`asset-manifest.json` |
| 第 4 步 | 生成媒体命令/请求清单：按生图 provider 条件读取 `references/gpt-image-api.md` 或 `references/dreamina-cli.md`，按生视频 provider 条件读取 `references/kling-api.md` 或 `references/dreamina-cli.md` | 对应 provider 参考文件、`templates/media-commands.md` | `03-media-commands.md` |
| 第 5 步 | 生成首帧图片并回填 manifest；`gpt-image-2` 必须执行“gpt-image 生图运行时优化”后暂停确认 | 对应 provider 参考文件、本文件“gpt-image 生图运行时优化” | `images/`、`asset-manifest.json` |
| 第 6 步 | 图片确认与重生成：不满意无意见则原提示词重生成，有意见则合并修改意见后重生成；失败项按运行时状态选择重试、改提示词、授权切换 provider、跳过或停止 | 本文件“图片确认与重生成规则”、“gpt-image 生图运行时优化” | 已批准或已决策的 `asset-manifest.json` |
| 第 7 步 | 全部图片确认后生成视频；默认使用 `dreamina-cli` | `references/dreamina-cli.md` 或用户指定 provider 参考文件 | `videos/`、回填 `asset-manifest.json` |
| 第 8 步 | 生成剪映草稿；无可用草稿工具时生成剪映拼接方案 | `references/jianying-draft-builder.md`、`references/jianying-plan.md` | `jianying-draft/` 或 `jianying-draft-plan.md` |
| 第 9 步 | 按完成前自检逐项检查 | 本文件“完成前自检” | 最终回复 |

## 按需执行规则

- 用户只要痛点分析：执行第 1-2 步。
- 用户只要提示词：执行第 1-3 步。
- 用户要可复制的媒体生成命令/请求：执行第 1-4 步。
- 用户要实际生成图片：执行第 1-6 步。
- 用户要实际生成视频：执行第 1-7 步。
- 用户要剪映草稿、剪映方案或完整资料：执行第 1-8 步。

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
- 实际生成素材时必须维护 `asset-manifest.json`，回填 image/video provider、model、task ID、远端 URL 或原始文件名；失败时也必须回填状态、尝试次数、错误摘要和 fallback 信息。
- `gpt-image-2` 生图必须先做零成本配置检查，并用第一张正式图兼做出图探测。
- `gpt-image-2` 批量生图必须小并发执行，默认并发上限为 2，且每张成功后立即下载并按素材 ID 回填 manifest。
- `gpt-image-2` 单张失败必须按 `references/gpt-image-api.md` 的重试和不可重试错误分类处理。
- 只有同格式 RightCode Draw 备用 API 已显式启用且配置完整时，才允许自动 fallback；`dreamina-cli` 不得作为自动 fallback。
- 未指定 provider 时，生图默认使用 `gpt-image-2`。
- 未指定 provider 时，生视频默认使用 `dreamina-cli`。
- 必须先生成全部图片并等待用户确认，不要直接继续生成视频。
- 用户不满意图片且未给修改意见时，必须使用原提示词重生成。
- 用户不满意图片且给了修改意见时，必须将修改意见合并进提示词后重生成。
- 只在全部图片确认后才生成视频。
- 使用 `dreamina-cli` 视频 provider 时，即梦图生视频路径必须包含 `--model_version=seedance2.0fast-vip` 和 `--video_resolution=720p`。
- 没有剪映 MCP 时，只输出剪映草稿拼接方案，不声称已经创建草稿。
- 草稿工具不可用时，不要声称已经创建剪映草稿。

## 完成前自检

交付前检查：

- 是否使用了用户提供的脚本或产品文本，而不是凭空生成项目。
- `01-analysis.md` 的痛点是否和 `02-prompts.json` 一一对应。
- `02-prompts.json` 是否是合法 JSON，且每条都是 9:16 竖屏痛点素材并包含 `image_size`。
- 每条 `video_prompt` 是否只描述画面，不包含首帧路径或视频时长。
- 每条 `video_prompt` 是否包含“不要生成字幕、文字、水印或品牌标志”。
- 是否没有生成 `voiceover` 字段。
- 每条 `duration_seconds` 是否按 `subtitle` 估算，并写明 `duration_basis`。
- `asset-manifest.json` 是否记录计划文件名；实际生成后是否补充 provider、model、task ID、远端 URL 或原始文件名；失败时是否补充状态、尝试次数、错误摘要和 fallback 信息。
- `gpt-image-2` 生图是否区分零成本配置检查和首张正式图出图探测。
- `gpt-image-2` 生图是否按小并发队列执行，并在每张成功后立即下载和回填 manifest。
- `gpt-image-2` 生图是否记录不可重试错误，不对鉴权失败、余额不足、模型不存在、尺寸不支持或明确安全拒绝盲目重试。
- 同格式 RightCode Draw fallback 是否只在显式启用且配置完整时自动执行。
- 是否没有在未获用户确认时自动 fallback 到 `dreamina-cli`。
- `03-media-commands.md` 的生图命令/请求、`--image` 或图片引用、`--duration` 或时长参数是否与 JSON 一致。
- 未指定 provider 时，生图是否默认 `gpt-image-2`。
- 未指定 provider 时，生视频是否默认 `dreamina-cli`。
- 是否先生成全部图片并等待用户确认，而不是直接继续生成视频。
- 用户不满意图片且未给修改意见时，是否使用原提示词重生成。
- 用户不满意图片且给了修改意见时，是否将修改意见合并进提示词后重生成。
- 是否只在全部图片确认后才生成视频。
- 即梦参数 `--model_version=seedance2.0fast-vip` 和 `--video_resolution=720p` 是否只在 `dreamina-cli` 视频 provider 下检查。
- 剪映方案是否区分“已生成文件”和“待生成文件”，并保留首帧图片对应关系。
- 是否没有在草稿工具不可用时声称已经创建剪映草稿。
