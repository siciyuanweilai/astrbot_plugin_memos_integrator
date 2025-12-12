"""
MemOS记忆集成插件
使用HTTP方式实现记忆获取、注入和更新功能
"""

import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.provider import ProviderRequest, LLMResponse
from astrbot.api import AstrBotConfig, logger
from .memory_manager import MemoryManager

# 主插件类
@register("astrbot_plugin_memos_integrator","zz6zz666", "MemOS记忆集成插件", "1.1.0")
class MemosIntegratorPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.memory_manager = None
        self.memory_limit = 5
        self.prompt_language = "auto"
        # 用于保存原始prompt的字典，key为session_id
        self.original_prompts = {}

        # 在 __init__ 中初始化记忆管理器
        try:
            # 验证配置
            api_key = self.config.get("api_key", "")
            if not api_key:
                logger.warning("MemOS API密钥未配置,插件功能将不可用")
                return

            # 获取配置
            base_url = self.config.get("base_url", "https://memos.memtensor.cn/api/openmem/v1")
            self.memory_limit = self.config.get("memory_limit", 5)
            self.prompt_language = self.config.get("prompt_language", "auto")

            # 初始化记忆管理器
            self.memory_manager = MemoryManager(
                api_key=api_key,
                base_url=base_url
            )

            logger.info("MemOS记忆集成插件已加载")
            logger.info(f"插件配置: API地址={base_url}, 记忆注入限制={self.memory_limit}, 提示词语言={self.prompt_language}")
        except Exception as e:
            logger.error(f"初始化MemOS记忆管理器失败: {e}")
            self.memory_manager = None
            
    def _get_session_id(self, event: AstrMessageEvent) -> str:
        """获取会话ID（统一消息来源）"""
        # 使用AstrBot框架提供的统一消息来源作为会话ID
        # 格式: platform_id:message_type:session_id
        session_id = event.unified_msg_origin
        logger.debug(f"会话ID: {session_id}")
        return session_id

    async def _get_conversation_id(self, event: AstrMessageEvent) -> str:
        """获取当前对话ID"""
        # 从框架的对话管理器获取当前对话ID
        session_id = event.unified_msg_origin
        conversation_id = await self.context.conversation_manager.get_curr_conversation_id(session_id)

        # 如果没有对话，创建一个新对话
        if not conversation_id:
            conversation_id = await self.context.conversation_manager.new_conversation(session_id)
            logger.info(f"为会话 {session_id} 创建新对话: {conversation_id}")
        else:
            logger.debug(f"使用现有对话ID: {conversation_id}")

        return conversation_id
        
    @filter.on_llm_request(priority=-10000)  # 确保在其他插件（如内置群聊LTM插件）之后执行
    async def inject_memories(self, event: AstrMessageEvent, req: ProviderRequest):
        """在LLM请求前获取记忆并注入"""

        # 检查memory_manager是否已初始化
        if self.memory_manager is None:
            logger.warning("memory_manager未初始化，跳过记忆注入")
            return

        # 获取会话ID和对话ID（从AstrBot框架）
        session_id = self._get_session_id(event)
        conversation_id = await self._get_conversation_id(event)

        # 提取用户消息并保存原始prompt
        user_message = req.prompt
        self.original_prompts[session_id] = user_message  # 保存原始prompt

        logger.info(f"收到LLM请求，会话ID: {session_id}, 对话ID: {conversation_id}")
        logger.debug(f"用户消息长度: {len(user_message)}")

        # 获取记忆（使用session_id作为user_id）
        memories = await self.memory_manager.retrieve_relevant_memories(
            user_message, session_id, conversation_id, limit=self.memory_limit
        )

        logger.debug(f"检索到 {len(memories)} 条相关记忆，会话ID: {session_id}")

        if memories:
            # 注入记忆到用户消息，使用新的记忆注入逻辑
            # 确定语言
            if self.prompt_language == "auto":
                # 自动检测语言，默认为中文
                language = "zh"
                # 改进的语言检测：只有当消息完全是英文（没有中文字符）时才使用英文
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_message)
                if not has_chinese and any(ord(c) < 128 and c.isalpha() for c in user_message):
                    # 没有中文且有英文字母
                    language = "en"
            else:
                # 使用用户配置的语言
                language = self.prompt_language

            # 检测模型类型，默认为default
            model_type = "default"
            if hasattr(req, "model") and req.model:
                if "qwen" in req.model.lower():
                    model_type = "qwen"
                elif "gemini" in req.model.lower():
                    model_type = "gemini"

            logger.info(f"检测到语言: {language}, 模型类型: {model_type}")

            # 使用新的记忆注入逻辑
            req.prompt = await self.memory_manager.inject_memory_to_prompt(
                user_message, memories, language, model_type
            )

            # 使用debug级别记录注入后的完整prompt
            logger.debug(f"记忆注入后的完整prompt:\n{req.prompt}")
            logger.info(f"已为会话 {session_id} 注入 {len(memories)} 条记忆")
            logger.debug(f"原始prompt长度: {len(user_message)}, 注入后prompt长度: {len(req.prompt)}")
        else:
            logger.info(f"未找到相关记忆，会话ID: {session_id}")
            
    @filter.on_llm_response()
    async def save_memories(self, event: AstrMessageEvent, resp: LLMResponse):
        """在LLM响应后保存对话到记忆，并清洗上下文中的记忆注入"""

        try:
            # 检查memory_manager是否已初始化
            if self.memory_manager is None:
                logger.warning("memory_manager未初始化，跳过记忆保存")
                return

            # 获取会话ID和对话ID（从AstrBot框架）
            session_id = self._get_session_id(event)
            conversation_id = await self._get_conversation_id(event)

            logger.info(f"收到LLM响应，会话ID: {session_id}, 对话ID: {conversation_id}")

            # 恢复原始prompt（避免记忆注入被保存到AstrBot对话历史）
            # 同时用于保存到MemOS
            user_message = None
            if session_id in self.original_prompts:
                original_prompt = self.original_prompts[session_id]
                user_message = original_prompt  # 使用原始prompt作为用户消息

                # 从event中获取ProviderRequest对象
                req = event.get_extra("provider_request")
                if req is not None:
                    # 恢复原始prompt到req.prompt，这样_save_to_history会使用原始prompt
                    req.prompt = original_prompt
                    logger.debug(f"已恢复原始prompt到req.prompt，避免记忆注入被保存，长度: {len(original_prompt)}")
                else:
                    logger.warning("无法从event中获取provider_request，跳过上下文清洗")

                # 清理已使用的原始prompt
                del self.original_prompts[session_id]

            # 如果没有保存的原始prompt，则从event获取（作为兜底）
            if not user_message:
                user_message = event.message_str

            if not user_message:
                logger.warning("未找到用户消息，跳过记忆保存")
                return

            # 从响应中提取AI回复内容
            ai_response = resp.completion_text

            if not ai_response:
                logger.warning("未找到AI响应内容，跳过记忆保存")
                return

            logger.debug(f"用户消息长度: {len(user_message)}")
            logger.debug(f"AI响应长度: {len(ai_response)}")

            # 创建后台任务保存对话到MemOS（不阻塞响应返回）
            async def _save_memory_task():
                """后台保存记忆任务"""
                try:
                    success = await self.memory_manager.save_conversation(
                        user_message=user_message,
                        ai_response=ai_response,
                        user_id=session_id,
                        conversation_id=conversation_id
                    )
                    if success:
                        logger.info(f"成功保存对话到MemOS，会话ID: {session_id}")
                    else:
                        logger.warning(f"保存对话到MemOS失败，会话ID: {session_id}")
                except Exception as e:
                    logger.error(f"后台保存对话记忆时出错，会话ID: {session_id}, 错误: {e}")

            # 提交后台任务，不等待完成
            task = asyncio.create_task(_save_memory_task())

            # 添加回调处理任务异常（可选，但推荐）
            def task_done_callback(t: asyncio.Task):
                """后台任务完成时的回调，用于捕获未处理的异常"""
                try:
                    t.result()  # 获取任务结果，如果有异常会在这里抛出
                except asyncio.CancelledError:
                    logger.info(f"记忆保存任务被取消，会话ID: {session_id}")
                except Exception as e:
                    logger.error(f"后台记忆保存任务执行失败，会话ID: {session_id}, 错误: {e}", exc_info=True)

            task.add_done_callback(task_done_callback)
            logger.debug(f"已提交记忆保存任务到后台，会话ID: {session_id}")

        except Exception as e:
            logger.error(f"处理记忆保存流程失败: {e}")