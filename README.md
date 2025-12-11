# AstrBot MemOS 集成插件

这是一个为AstrBot开发的MemOS集成插件，允许Bot记忆用户对话内容，并在后续对话中提供个性化响应。

## 功能特点

- **记忆管理**: 自动保存和管理用户对话内容
- **智能检索**: 根据当前对话检索相关记忆
- **记忆注入**: 在LLM请求前注入相关记忆，提供上下文
- **多语言支持**: 支持中文和英文记忆注入
- **多模型支持**: 针对不同模型（通义千问、Gemini等）优化提示词
- **安全协议**: 使用"四步判决"确保记忆使用的安全性

## 安装

1. 将插件文件夹复制到AstrBot的plugins目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 在AstrBot的配置文件中添加插件配置（见下文）

## 配置

插件使用AstrBot的配置系统。在AstrBot的配置文件中添加以下配置：

```json
{
  "plugins": {
    "memos_integrator": {
      "api_key": "your_memos_api_key",
      "max_memory_length": 1000
    }
  }
}
```

- `api_key`: MemOS API密钥
- `max_memory_length`: 记忆内容的最大长度

## 使用方法

### 自动记忆

1. 在LLM请求前检索相关记忆并注入到提示词
2. 在LLM响应后保存对话内容到记忆

**注意**: MemOS记忆集成插件仅提供自动记忆功能，不支持手动管理命令。

## 记忆注入逻辑

插件使用以下逻辑进行记忆注入：

1. **语言检测**: 自动检测用户消息的语言（中文/英文）
2. **模型检测**: 识别LLM模型类型（通义千问/Gemini/其他）
3. **记忆检索**: 根据用户查询检索相关记忆
4. **记忆格式化**: 将记忆格式化为适合的模板
5. **提示词注入**: 将格式化的记忆注入到提示词中

## 记忆安全协议

插件使用"四步判决"确保记忆使用的安全性：

1. **来源真值检查**: 区分用户原话与AI推测
2. **主语归因检查**: 确认记忆中的行为主体是用户本人
3. **强相关性检查**: 确认记忆与当前查询相关
4. **时效性检查**: 确认记忆内容与用户最新意图不冲突

## 文件结构

```
astrbot_plugin_memos_integrator/
├── __init__.py              # 插件入口
├── main.py                  # 主插件文件
├── memory_manager.py        # 记忆管理器
├── memory_templates.py      # 记忆注入模板
├── memos_client.py          # MemOS API客户端
├── config.py                # 配置类
├── requirements.txt         # 依赖列表
└── README.md               # 说明文档
```

## 开发说明

### 记忆管理器

`MemoryManager`类负责记忆的检索、注入和更新：

- `retrieve_relevant_memories`: 检索相关记忆
- `inject_memory_to_prompt`: 将记忆注入到提示词
- `update_memory`: 更新记忆内容

### 记忆模板

`MemoryTemplates`类提供不同语言和模型的记忆注入模板：

- `get_injection_template`: 获取注入模板
- `format_memory_content`: 格式化记忆内容

### MemOS客户端

`MemOSClient`类负责与MemOS API的交互：

- `search_memory`: 搜索记忆
- `add_message`: 添加消息
- `create_conversation`: 创建对话

## 许可证

MIT License