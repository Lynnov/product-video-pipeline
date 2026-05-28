---
name: gpt-image-runtime-optimization-spec
description: 记录 product-video-pipeline 后续优化 gpt-image-2 生图探测、逐张回填、重试和 fallback 的规格草案。
---

# GPT Image 生图运行时优化 Spec

## 背景

当前 `product-video-pipeline` 已能生成 `gpt-image-2` 生图请求清单，但运行时策略还不够明确：

- `03-media-commands.md` 中的前置检查只确认 `KFCV50_API_KEY` 是否存在，不代表 API、模型、额度和尺寸都可用。
- `gpt-image-2` 生图看起来是同步请求，当前文档没有定义批量执行时的节奏、失败处理和回填时机。
- `asset-manifest.json` 规定了成功后的回填字段，但没有规定失败时如何记录状态。
- provider 不可用时当前只要求说明卡在“素材生成”，没有定义重试次数、间隔或是否切换到 `dreamina-cli`。

## 目标

后续优化应让生图阶段更可控、可恢复、可追踪：

1. 任务开始前做零成本配置检查，并用第一张正式图片兼做供应商出图探测。
2. 生图按素材顺序入队，以小并发队列执行，而不是等全部完成后统一处理。
3. 每张图片成功后立即下载并回填 `asset-manifest.json`。
4. 单张失败时执行明确的重试策略。
5. 多次失败后记录失败状态，并按配置自动尝试同格式备用 KFC V50 API。
6. 备用 API 与主 API 调用格式一致时，无需再次提示用户确认。

## 非目标

本 spec 不要求立即实现以下能力：

- 不引入新的生图 provider。
- 不自动生成视频。
- 不自动创建剪映草稿。
- 不在没有配置备用 API 的情况下猜测或临时切换到其他 provider。
- 不把 `gpt-image-2` 生图改造成异步轮询模型，除非后续接口实测证明它是异步任务接口。

## 推荐流程

### 1. 首张正式图兼做供应商出图探测

任务开始前不额外生成测试图片，避免重复消耗额度。正式生图前只做零成本配置检查：

- `.env` 是否存在主 API 配置。
- `KFCV50_API_KEY` 是否非空。
- `KFCV50_BASE_URL` 是否非空；未配置时默认使用 `https://kfcv50.link`。
- `KFCV50_IMAGE_MODEL` 是否非空；未配置时默认使用 `gpt-image-2`。
- 如果启用备用 API，检查 `KFCV50_FALLBACK_API_KEY`、`KFCV50_FALLBACK_BASE_URL`、`KFCV50_FALLBACK_IMAGE_MODEL` 是否完整。

真正要探测的是供应商当前是否能出图，因此使用第一张正式图片作为实际探测请求：

1. 取 `02-prompts.json` 中第一条素材。
2. 使用该素材的正式 `image_prompt`、`image_size` 和计划 `image_file` 请求主 API。
3. 第一张主 API 成功时，立即下载并回填 manifest，然后启动后续小并发队列。
4. 第一张主 API 失败时，按单张重试策略处理。
5. 第一张主 API 重试后仍失败且备用 API 已启用时，自动切换备用 API 处理第一张。
6. 第一张主 API 和备用 API 都失败时，停止批量生图并反馈失败原因，避免后续素材一起失败。

需要记录的探测结果：

- `probe_mode`: `first_formal_image`
- `probe_asset_id`: 第一张正式素材 ID
- `probe_provider`: 实际成功或最终失败的 provider，例如 `kfcv50-primary` 或 `kfcv50-fallback`
- `probe_model`: 实际使用的模型，例如 `gpt-image-2`
- `probe_size`: `1152x2048`
- `probe_status`: `success` 或 `failed`
- `probe_error`: 失败时记录错误摘要
- `probe_checked_at`: 检查时间

### 2. 小并发队列生成与逐张回填

批量生图按 `02-prompts.json` 的素材顺序进入请求队列。默认推荐使用小并发队列，而不是固定分配每路处理几张：

- 默认并发上限建议为 `2`，即同一时间最多只有 2 个生图请求在运行。
- 每个请求仍然只生成 1 张图片，不使用单请求多图。
- 哪个请求先完成，就先下载该图片并回填 `asset-manifest.json`。
- 某一路空出来后，立即从队列取下一张继续请求。
- 全程不允许超过当前配置的并发上限。

执行顺序示例：

1. 同时发起 `pain-02` 和 `pain-03`。
2. 如果 `pain-03` 先成功，则先下载 `pain-03` 并回填 manifest。
3. 空出的并发槽继续发起 `pain-04`。
4. 如果 `pain-02` 随后成功，则下载 `pain-02` 并回填 manifest。
5. 空出的并发槽继续发起 `pain-05`。

每个素材的单次处理步骤：

1. 读取当前素材的 `id`、`image_prompt`、`image_file`、`image_size`。
2. 调用 `gpt-image-2` 生图 API。
3. 如果返回 `data[0].url`，立即下载到计划路径，例如 `images/pain-01.png`。
4. 下载成功后立即回填 `asset-manifest.json`。
5. 释放当前并发槽，继续处理队列中的下一张。

这样可以兼顾速度和稳定性，避免 4 个请求同时打接口，也避免中途失败时丢失已成功素材。

### 2.1 并发上限建议

当前实测结果显示，`4` 并发和 `2` 并发都可能出现 `RemoteDisconnected('Remote end closed connection without response')`，因此并发能力需要按通道状态保守使用：

- 默认推荐：`concurrency = 2`。

无论并发上限是多少，都必须用素材 ID 绑定请求结果，回填时按 `id` 更新对应 manifest 项，不依赖请求完成顺序。

### 3. 单张重试策略

单张图片失败时，默认最多尝试 10 次：

| 尝试次数 | 建议等待 |
| --- | --- |
| 第 1 次失败后 | 10 秒 |
| 第 2 次失败后 | 20 秒 |
| 第 3 次失败后 | 30 秒 |
| 第 4 次失败后 | 45 秒 |
| 第 5 次失败后 | 60 秒 |
| 第 6-10 次失败后 | 每次 60 秒 |

重试适用于临时性错误，例如：

- 网络超时
- 5xx 服务端错误
- 临时限流
- 下载 URL 短暂不可用

不建议自动重试的错误：

- 鉴权失败
- 余额不足
- 模型不存在
- 尺寸不支持
- 明确的 prompt 安全拒绝

这些错误不应继续重试同一个主 API；如果 `.env` 已启用并完整配置同格式备用 KFC V50 API，则自动切换备用 API 处理当前图片。主 API 和备用 API 都不可用时，再停止当前图片处理并提示用户修正配置或提示词。

### 4. 失败回填规则

图片生成最终失败时，不应静默跳过。需要在 `asset-manifest.json` 对应素材中记录：

- `image_status`: `failed`
- `image_attempts`: 主 API 实际尝试次数
- `image_error`: 最终错误摘要
- `image_last_attempt_at`: 最后一次尝试时间
- `image_provider`: 最后使用的 provider，例如 `kfcv50-primary` 或 `kfcv50-fallback`
- `image_model`: 最后使用的模型，例如 `gpt-image-2`
- `image_size`: `1152x2048`
- `image_fallback_used`: 是否已尝试备用 API
- `image_fallback_attempts`: 备用 API 实际尝试次数；未启用备用 API 时为 `0`
- `image_approved`: `false`

主 API 生成成功时，建议记录：

- `image_status`: `generated`
- `image_attempts`: 主 API 实际尝试次数
- `image_provider`: `kfcv50-primary`
- `image_model`: `gpt-image-2`
- `image_size`: `1152x2048`
- `image_original_url`: `data[0].url`
- `image_task_id`: 如果响应没有任务 ID，则为 `null`
- `image_file`: 计划图片路径
- `image_fallback_used`: `false`
- `image_approved`: `false`

主 API 失败但备用 API 生成成功时，建议记录：

- `image_status`: `generated`
- `image_attempts`: 主 API 实际尝试次数
- `image_provider`: `kfcv50-fallback`
- `image_model`: 实际备用模型，例如 `gpt-image-2`
- `image_size`: `1152x2048`
- `image_original_url`: 备用 API 返回的 `data[0].url`
- `image_task_id`: 如果响应没有任务 ID，则为 `null`
- `image_file`: 计划图片路径
- `image_fallback_used`: `true`
- `image_fallback_from`: `kfcv50-primary`
- `image_fallback_reason`: 主 API 失败原因摘要
- `image_fallback_attempts`: 备用 API 实际尝试次数
- `image_approved`: `false`

### 5. 批量完成后的暂停点

生图处理完成后，进入统一暂停点：

- 如果全部图片成功：等待用户逐张确认图片是否可用。
- 如果部分图片在主 API 和备用 API 都尝试后仍失败：先汇总失败项，等待用户选择下一步。
- 如果第一张正式图在主 API 和备用 API 都尝试后仍失败：不进入后续小并发队列，直接提示用户修复配置或更换通道。

可提供给用户的选择：

1. 只重试失败项。
2. 修改失败项提示词后重试。
3. 授权切换到 `dreamina-cli` 重新生成失败项。
4. 跳过失败项，仅继续处理成功图片。
5. 停止当前素材生成流程。

### 6. fallback 策略

默认 fallback 只支持同调用格式的 KFC V50 备用 API，不自动 fallback 到 `dreamina-cli`。

原因：

- 备用 API 仍走 KFC V50 / OpenAI-compatible 生图格式，请求体、模型字段、尺寸字段和响应解析逻辑与主 API 一致。
- 同格式备用 API 可以复用同一套下载、回填和错误处理逻辑。
- `dreamina-cli` 属于不同 provider，命令格式、模型能力和风格可能不同，不应作为默认自动 fallback。

`.env` 中建议增加备用 API 配置：

```env
# 主 KFC V50 生图 API
KFCV50_API_KEY=sk-...
KFCV50_BASE_URL=https://kfcv50.link
KFCV50_IMAGE_MODEL=gpt-image-2

# 备用 KFC V50 生图 API，调用格式必须与主 API 一致
KFCV50_FALLBACK_API_KEY=sk-...
KFCV50_FALLBACK_BASE_URL=https://kfcv50.link
KFCV50_FALLBACK_IMAGE_MODEL=gpt-image-2
KFCV50_FALLBACK_ENABLED=true
```

自动 fallback 规则：

1. 主 API 单张图片按重试策略失败后，检查 `KFCV50_FALLBACK_ENABLED` 是否为 `true`。
2. 如果备用 API 配置完整，则自动用备用 API 请求同一张图片。
3. 备用 API 也按同样的单张重试策略执行。
4. 备用 API 成功后，立即下载图片并回填 manifest。
5. 主 API 和备用 API 都失败时，才将该图片标记为 `failed`。

切换到备用 API 时无需再次提示用户确认，因为备用 API 已在 `.env` 中显式配置为同格式备用通道。manifest 中必须记录：

- `image_provider`: `kfcv50-fallback`
- `image_model`: 实际备用模型，例如 `gpt-image-2`
- `image_fallback_from`: `kfcv50-primary`
- `image_fallback_reason`: 主 API 失败原因摘要
- `image_fallback_attempts`: 备用 API 实际尝试次数
- `image_original_url`: 备用 API 返回的 `data[0].url`

如果后续要 fallback 到 `dreamina-cli`，仍然必须暂停并取得用户确认。

## 需要修改的文件

后续实现时建议修改以下源文件，而不是只改某个输出目录下的产物：

- `SKILL.md`：把“全部首帧图片生成”细化为小并发队列生成、单张完成即下载并回填，全部处理完成后再暂停确认。
- `references/gpt-image-api.md`：加入零成本配置检查、首张正式图出图探测、重试、失败回填、同格式 KFC V50 备用 API 自动 fallback 规则。
- `templates/media-commands.md`：让新生成的 `03-media-commands.md` 自动包含配置检查命令、首张正式图探测说明、生图小并发队列和失败处理说明。
- `templates/asset-manifest.schema.json`：如需机器校验失败字段，则补充 `image_status`、`image_attempts`、`image_error` 等字段。
- `evals/evals.json`：增加覆盖首张正式图探测、生图小并发队列回填、重试失败、fallback 配置与自动切换的测试用例。

## 验收标准

后续实现完成后，应满足：

- 新生成的 `03-media-commands.md` 明确区分“零成本配置检查”和“首张正式图出图探测”。
- 生图命令或脚本体现小并发队列生成、单张完成即下载并回填。
- `asset-manifest.json` 支持成功和失败两种状态记录。
- 单张失败有明确重试次数和间隔。
- 鉴权失败、余额不足、模型不存在、尺寸不支持等不可恢复错误不会盲目重试。
- fallback 到同格式 KFC V50 备用 API 时无需再次确认，但必须要求 `.env` 显式启用并配置完整。
- fallback 到 `dreamina-cli` 前仍必须暂停并取得用户确认。
- 全部图片无论成功或失败，都能从 manifest 看出当前状态和下一步动作。

## 待确认问题

后续真正实现前，还需要确认：

1. `gpt-image-2` 当前失败响应的实际 JSON 结构。
2. `1152x2048` 在当前 KFC V50 通道是否稳定可用。
3. 图片 URL 的有效期和下载失败后的最佳重试策略。
4. 是否需要写一个统一的执行脚本来替代手动复制 `curl`。
5. `asset-manifest.schema.json` 是否应强制要求运行时状态字段。
6. 首张正式图探测失败时，是否自动把后续队列全部暂停，还是允许用户手动继续尝试后续素材。
