# AI 聊天 & 轻日记 接口明细

后端使用 FastAPI + SQLAlchemy 暴露接口，前端通过 `/api` 访问（开发环境由 Webpack DevServer 代理到后端）。需要登录的接口使用 Token 认证：

```http
Authorization: Token <token>
```

FastAPI 自动文档地址：

- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`

## 前端 URL 包装

前端统一在 `frontend/src/api/urls.ts` 维护接口 URL：

| 包装字段 | URL |
| --- | --- |
| `apiUrls.auth.login` | `/api/login/` |
| `apiUrls.auth.register` | `/api/register/` |
| `apiUrls.chat.send` | `/api/chat/` |
| `apiUrls.chat.conversations` | `/api/chat/conversations/` |
| `apiUrls.chat.conversation(id)` | `/api/chat/conversations/{id}/` |
| `apiUrls.diary.list` | `/api/diary/` |
| `apiUrls.diary.create` | `/api/diary/` |
| `apiUrls.diary.detail(id)` | `/api/diary/{id}/` |
| `apiUrls.diary.reindex` | `/api/diary/reindex/` |
| `apiUrls.settings.get` | `/api/settings/` |
| `apiUrls.settings.update` | `/api/settings/` |

## 认证接口

### 注册

- Method: `POST`
- URL: `/api/register/`
- Body:

```json
{ "username": "username", "email": "user@example.com", "password": "password" }
```

- 规则：用户名和密码至少 6 个字符，用户名与邮箱唯一。

### 登录

- Method: `POST`
- URL: `/api/login/`
- Body:

```json
{ "username": "username", "password": "password" }
```

- Response:

```json
{ "token": "token-value", "username": "username" }
```

## 聊天接口

### 发送消息（多轮对话）

- Method: `POST`
- URL: `/api/chat/`
- 认证：需要
- Body:

```json
{ "content": "你好", "conversation_id": 12 }
```

- `conversation_id` 为空时会自动新建一个对话；后端会带上最近若干条历史消息请求 AI。
- 当用户开启「允许 AI 参考我的日记」（默认开启）时，后端会注入日记记忆作为上下文，详见 [日记记忆层设计](./memory-layer.md)。
- Response:

```json
{
  "conversation_id": 12,
  "title": "你好",
  "user_message": { "id": 1, "role": "user", "content": "你好", "created_at": "..." },
  "assistant_message": { "id": 2, "role": "assistant", "content": "...", "created_at": "..." }
}
```

### 对话列表

- Method: `GET`
- URL: `/api/chat/conversations/`
- 认证：需要
- Response: `Conversation[]`（按更新时间倒序）

### 对话详情（含全部消息）

- Method: `GET`
- URL: `/api/chat/conversations/{id}/`
- 认证：需要
- Response: `ConversationDetail`（含 `messages`）

### 删除对话

- Method: `DELETE`
- URL: `/api/chat/conversations/{id}/`
- 认证：需要
- Response: `204 No Content`

## 日记接口

### 日记列表

- Method: `GET`
- URL: `/api/diary/`
- 认证：需要
- Response: `DiaryEntry[]`（按创建时间倒序）

### 发布日记

- Method: `POST`
- URL: `/api/diary/`
- 认证：需要
- Content-Type: `multipart/form-data`
- Form:

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `content` | string | 否 | 配图文字 |
| `image` | file | 否 | 图片文件（jpg/png/gif/webp/bmp） |

- 规则：`content` 与 `image` 至少提供一个。
- 若配置了视觉模型且上传了图片，后端会为图片生成中文描述并纳入记忆层向量索引，详见 [日记记忆层设计](./memory-layer.md)。未配置时自动跳过，不影响发布。

### 重建日记记忆

- Method: `POST`
- URL: `/api/diary/reindex/`
- 认证：需要
- 说明：为历史日记补全配图描述并重建语义向量索引。详见 [日记记忆层设计](./memory-layer.md)。
- Response:

```json
{ "processed": 12, "captioned": 3, "embedded": 12 }
```

| 字段 | 说明 |
| --- | --- |
| `processed` | 扫描的日记条数 |
| `captioned` | 新生成配图描述的条数 |
| `embedded` | 重建（或新建）向量的条数 |

### 删除日记

- Method: `DELETE`
- URL: `/api/diary/{id}/`
- 认证：需要
- Response: `204 No Content`

## 设置接口

用户级设置，目前包含隐私开关「允许 AI 参考我的日记」。功能说明详见 [设置功能](./settings.md)。

### 读取设置

- Method: `GET`
- URL: `/api/settings/`
- 认证：需要
- Response：

```json
{ "allow_ai_diary": true }
```

- 首次读取时若不存在会自动创建默认设置（`allow_ai_diary = true`）。

### 更新设置

- Method: `PUT`
- URL: `/api/settings/`
- 认证：需要
- Body：

```json
{ "allow_ai_diary": false }
```

- Response：同「读取设置」，返回更新后的设置。

## AI 配置

后端通过 `backend/config.json`（已在 `.gitignore` 中，不会提交）配置 DeepSeek 兼容接口。`ai.vision` 为可选的视觉模型（用于把日记图片转成中文描述），`memory` 为日记记忆层配置，二者说明分别见 [日记记忆层设计](./memory-layer.md)：

```json
{
  "ai": {
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "system_prompt": "你是一个温暖、贴心的 AI 助手。",
    "vision": {
      "api_key": "",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "model": "qwen-vl-plus"
    }
  }
}
```

未配置 `ai.api_key` 时，后端会返回本地模拟回复，便于在无凭据时直接体验。未配置 `ai.vision.api_key` 时，日记图片不会生成描述，其余功能不受影响。
