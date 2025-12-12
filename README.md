# AstrBot MemOS 集成插件 v2.0

这是一个为AstrBot开发的MemOS集成插件,允许Bot记忆用户对话内容,并在后续对话中提供个性化响应。

## ✨ v2.0 重大更新

### 架构优化
- **移除 SDK 依赖**: 不再依赖 `MemoryOS` SDK,改用 HTTP API 直接访问
- **简化类结构**: 合并 `MemOS_Client` 和 `MemoryManager`,消除循环依赖
- **优化初始化**: 解决了 v1.0 中 "memory_manager 未初始化" 的问题
- **减少依赖**: 仅需 `aiohttp`,安装更简单

### 配置增强
- **新增 base_url 配置**: 支持自定义 MemOS API 地址
- **从配置文件读取**: 不依赖环境变量

## 功能特点

- **记忆管理**: 自动保存和管理用户对话内容
- **智能检索**: 根据当前对话检索相关记忆
- **记忆注入**: 在LLM请求前注入相关记忆,提供上下文
- **多语言支持**: 支持中文和英文记忆注入
- **多模型支持**: 针对不同模型(通义千问、Gemini等)优化提示词
- **安全协议**: 使用"四步判决"确保记忆使用的安全性

## 安装

1. 将插件文件夹复制到AstrBot的plugins目录
2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```
3. 在AstrBot的配置界面中配置插件

## 配置

插件使用AstrBot的配置系统。配置项如下:

```json
{
  "api_key": "your_memos_api_key",
  "base_url": "https://memos.memtensor.cn/api/openmem/v1",
  "max_memory_length": 1000,
  "memory_limit": 5,
  "prompt_language": "auto"
}
```

### 配置项说明

- `api_key` (必填): MemOS API密钥
- `base_url` (可选): MemOS API基础URL,默认为官方地址

## 使用方法

### 自动记忆

插件会自动执行以下操作:

1. **LLM请求前**: 检索相关记忆并注入到提示词
2. **LLM响应后**: 保存对话内容到记忆

无需手动干预,插件会在后台自动工作。

## 记忆注入逻辑

插件使用以下逻辑进行记忆注入:

1. **语言检测**: 自动检测用户消息的语言(中文/英文)
2. **模型检测**: 识别LLM模型类型(通义千问/Gemini/其他)
3. **记忆检索**: 根据用户查询检索相关记忆
4. **记忆格式化**: 将记忆格式化为适合的模板
5. **提示词注入**: 将格式化的记忆注入到提示词中

## 记忆安全协议

插件使用"四步判决"确保记忆使用的安全性:

1. **来源真值检查**: 区分用户原话与AI推测
2. **主语归因检查**: 确认记忆中的行为主体是用户本人
3. **强相关性检查**: 确认记忆与当前查询相关
4. **时效性检查**: 确认记忆内容与用户最新意图不冲突

## 文件结构

```
astrbot_plugin_memos_integrator/
├── __init__.py              # 包标识文件(空文件,通过@register自动发现)
├── main.py                  # 主插件类
├── memory_manager.py        # 记忆管理器(HTTP API)
├── memory_templates.py      # 记忆注入模板(工具类)
├── metadata.yaml            # 插件元数据
├── _conf_schema.json        # 配置项定义
├── requirements.txt         # 依赖列表
└── README.md                # 本文件
```

## 技术细节

### 类关系对比

**v1.0 (旧版 - 有循环依赖):**
```
main.py → MemOS_Client (SDK封装)
       → MemoryManager (依赖 MemOS_Client)
       → MemoryTemplates
```

**v2.0 (新版 - 简化结构):**
```
main.py → MemoryManager (直接HTTP API)
       → MemoryTemplates (纯工具类,无依赖)
```

### 初始化流程

1. 插件加载时,`on_load()` 方法被调用
2. 读取配置文件中的 `api_key` 和 `base_url`
3. 创建单一的 `MemoryManager` 实例
4. `MemoryManager` 持有 API 密钥和基础 URL
5. 后续请求直接通过 `aiohttp` 发送 HTTP 请求

### HTTP API 端点

- `POST /add/message` - 添加对话消息
- `POST /search/memory` - 搜索相关记忆

### 记忆管理器 API

`MemoryManager` 类提供以下方法:

- `add_message()`: 添加对话消息到 MemOS
- `search_memory()`: 搜索相关记忆
- `save_conversation()`: 保存对话到 MemOS
- `retrieve_relevant_memories()`: 检索相关记忆
- `update_memory()`: 更新记忆内容
- `inject_memory_to_prompt()`: 将记忆注入到提示词

### 记忆模板

`MemoryTemplates` 类提供不同语言和模型的记忆注入模板:

- `get_injection_template()`: 获取注入模板
- `format_memory_content()`: 格式化记忆内容

## 故障排查

### 问题 1: memory_manager 未初始化

**原因**: API 密钥未配置或配置错误

**解决方法**:
1. 检查插件配置中是否填写了 `api_key`
2. 查看 AstrBot 日志中的错误信息
3. 确认 API 密钥有效且未过期

### 问题 2: HTTP 请求超时

**原因**: 网络问题或 MemOS API 服务不可用

**解决方法**:
1. 检查网络连接是否正常
2. 尝试自定义 `base_url` 配置项
3. 检查 MemOS API 服务状态
4. 查看日志中的详细错误信息

### 问题 3: 记忆未保存

**原因**: API 请求失败或配置错误

**解决方法**:
1. 检查日志中是否有 "保存对话失败" 的错误
2. 确认 `api_key` 和 `base_url` 配置正确
3. 尝试手动访问 API 地址测试连接

## 从 v1.0 迁移

如果你正在使用 v1.0 版本,升级到 v2.0 非常简单:

1. **更新代码**: 替换所有插件文件
2. **更新配置**: 在配置中添加 `base_url` 项(可选)
3. **更新依赖**: 运行 `pip install -r requirements.txt` (会自动卸载 MemoryOS SDK)
4. **重启 AstrBot**: 重启后即可使用新版本

配置文件无需改动(除非你想自定义 `base_url`)。

## 作者

zz6zz666

## 许可证

MIT License
