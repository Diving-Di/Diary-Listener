# 设置功能

为聊天与日记提供用户级设置入口。前端在「聊天」「日记」下方新增「设置」菜单，目前包含隐私开关与记忆重建。

接口定义见 [接口明细](./api.md#设置接口)；记忆层原理见 [日记记忆层设计](./memory-layer.md)。

## 允许 AI 参考我的日记

- 隐私开关，**默认开启**。
- 开启时，聊天会注入用户日记中的心情、经历、情绪作为 AI 的上下文（见记忆层 L2/L3/L4）。
- 关闭时，`build_diary_context` 直接返回空，聊天不再读取任何日记内容。
- 持久化于 `user_settings.allow_ai_diary`；首次读取时自动创建默认值 `true`。
- 后端门控逻辑：`memory.diary_allowed` 同时校验全局 `memory.enabled` 与该用户开关，任一为关即不注入。

## 重建日记记忆

- 设置页提供「重建」按钮，调用 `POST /api/diary/reindex/`。
- 作用：为历史日记补全配图的中文描述，并重建语义向量索引。
- 适用场景：首次开启记忆功能、补全旧数据、或更换嵌入/视觉模型后。
- 返回扫描条数、新增描述条数、重建向量条数，前端以提示展示。

## 前端实现

| 项 | 位置 |
| --- | --- |
| 设置页组件 | `frontend/src/components/settings/Settings.tsx` |
| 设置 API | `frontend/src/api/settings.ts` |
| 重建 API | `frontend/src/api/diary.ts` (`reindexDiary`) |
| 菜单入口 | `frontend/src/App.tsx` |
| URL 包装 | `frontend/src/api/urls.ts` (`apiUrls.settings`、`apiUrls.diary.reindex`) |
