# 日记记忆层设计

让聊天页的 AI 能够参考用户日记中的心情、经历与情绪，作为长期记忆为回复提供上下文。本文档描述该记忆层的设计与实现。

接口相关说明见 [接口明细](./api.md)；隐私开关见 [设置功能](./settings.md)。

## 总体设计

记忆层分为四层，最终被组装成一段文本，作为额外的 system 消息注入聊天提示：

| 层 | 名称 | 内容 | 实现位置 |
| --- | --- | --- | --- |
| L1 | 短期记忆 | 当前对话的历史消息 | `routers/chat.py` |
| L2 | 近期记忆 | 最近 N 条日记原文 | `memory.py` `_recent_entries` |
| L3 | 相关记忆 | 与当前消息语义相关的日记（向量检索） | `memory.py` `_related_entries` |
| L4 | 长期记忆 | LLM 提炼的用户情绪画像 | `memory.py` `maybe_refresh_profile` |

组装顺序为 L4 画像 → L3/L2 日记摘录（去重，按相关度与时间排序），由 `memory.py` 的 `build_diary_context` 完成，并受字数预算约束。

所有查询均按 `user_id` 隔离；整层由用户级开关 `allow_ai_diary`（默认开启）与全局 `memory.enabled` 门控，关闭时 `build_diary_context` 返回空字符串，不影响正常聊天。

## 向量检索（L3）

- **本地嵌入模型**：默认 `BAAI/bge-small-zh-v1.5`（中文、CPU 友好），通过 `sentence-transformers` 加载，实现于 `app/embeddings.py`。
- **懒加载 + 单例缓存**：模型在进程内首次使用时加载一次，常驻复用；不区分用户，所有用户共用同一实例。
- **启动预热**：`main.py` 启动时通过 `embeddings.warmup()` 在后台守护线程预加载模型，避免首个请求承担加载/下载耗时；受 `memory.enabled` 控制。
- **向量存储**：每条日记的向量以 JSON 浮点数组存入 `diary_embeddings` 表（无需向量数据库扩展）。检索时取出该用户全部向量，在应用层用 numpy 计算余弦相似度取 top-k。单用户日记量小，这种方式简单且天然隔离。
- **降级策略**：模型或依赖不可用时，`encode` 返回 `None`，检索自动回退为「关键词 LIKE + 最近 N 条」，应用无需任何配置也能运行。

## 情绪画像（L4）

- 每新增 `profile_refresh_every` 条日记触发一次增量刷新（`maybe_refresh_profile`）。
- 取该用户最近 30 条日记，调用对话模型（`ai.summarize`）提炼一份 150 字以内的「长期情绪画像」，涵盖整体心情趋势、近期重要经历、反复出现的情绪标签、在意的话题。
- 画像存入 `user_memories` 表；未配置 `ai.api_key` 或调用失败时跳过，不影响日记发布。

## 图片语义（视觉描述）

- 日记发布时若配置了视觉模型且带图片，后端通过 `ai.describe_image` 调用视觉模型（OpenAI 兼容 `image_url` base64 协议）生成一段中文描述，存入 `diary_entries.image_caption`。
- 由于 DeepSeek 官方 API 无视觉端点，`ai.vision` 默认指向通义千问 Qwen-VL（DashScope 兼容端点），与主对话模型解耦。
- 描述会与日记正文合并（`memory.py` `entry_text`）一起参与编码、检索与注入，使纯图片日记的语义也能进入记忆层。
- 未配置 `ai.vision.api_key` 时该步骤为无操作，不影响发布。

## 重建接口

`POST /api/diary/reindex/` 用于为历史日记补全配图描述并重建向量索引，常用于首次开启记忆功能或更换模型后。逐条尽力处理，单条失败跳过。详见 [接口明细](./api.md#重建日记记忆)。

## 数据表

| 表 | 说明 |
| --- | --- |
| `diary_entries.image_caption` | 视觉模型为图片生成的中文描述（新增字段） |
| `diary_embeddings` | 单条日记的语义向量（JSON 浮点数组、模型名、维度） |
| `user_memories` | 用户长期情绪画像（summary + source_count） |
| `user_settings` | 用户级设置，含 `allow_ai_diary` |

> 注意：`init_db()` 使用 `create_all`，不会为已存在的 `diary_entries` 表自动补 `image_caption` 列。已有数据库需手动执行：
>
> ```sql
> ALTER TABLE diary_entries ADD COLUMN image_caption TEXT NOT NULL;
> ```

## 配置项（`backend/config.json`）

```json
{
  "ai": {
    "vision": {
      "api_key": "",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-vl-plus",
      "prompt": "请用一句简洁的中文描述这张图片……"
    }
  },
  "memory": {
    "enabled": true,
    "embedding_model": "BAAI/bge-small-zh-v1.5",
    "recent_n": 5,
    "top_k": 5,
    "char_budget": 1800,
    "profile_refresh_every": 3
  }
}
```

| 配置 | 默认 | 说明 |
| --- | --- | --- |
| `memory.enabled` | `true` | 是否启用记忆层（全局开关） |
| `memory.embedding_model` | `BAAI/bge-small-zh-v1.5` | 本地嵌入模型 |
| `memory.recent_n` | `5` | L2 注入的最近日记条数 |
| `memory.top_k` | `5` | L3 语义检索条数 |
| `memory.char_budget` | `1800` | 注入上下文的字数上限 |
| `memory.profile_refresh_every` | `3` | 每新增多少条日记刷新一次 L4 画像 |

各项均支持同名大写环境变量覆盖（如 `MEMORY_TOP_K`、`AI_VISION_API_KEY`）。
