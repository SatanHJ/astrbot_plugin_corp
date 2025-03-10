from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain
from astrbot.api import logger
from typing import Union

@register("astrbot_plugin_corp", "astrbot_plugin_corp", "一个企业业务插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def _get_invite_info(self, keyword: str, session_id: str):
        '''获取邀约信息'''
        provider = self.context.get_provider_by_id("query_invite")
        result = await provider.text_chat(
            prompt=keyword,
            session_id=session_id,
            invite_keyword=keyword
        )

        results = result.completion_text # 这里返回的是一个数组
        return results
    
    def _replay_invite_info(self, results: list):
        chain = []
        if len(results) > 0:
            chain.append(Plain(f"找到{len(results)}条邀约信息"))
            for result in results: # result 是一个字典
                chain.append(Plain(result["content"]))
        return chain
    
    @filter.command("query_invite")
    async def query_invite(self, event: AstrMessageEvent, keyword: str):
        '''这是一个查询邀请信息的指令'''
        results = await self._get_invite_info(keyword, event.session_id)
        chain = self._replay_invite_info(results)
        yield event.chain_result(chain)
    
    @filter.llm_tool(name="get_invite_info")
    async def get_invite_info(self, event: Union[AstrMessageEvent, Context], keyword: str):
        '''获取邀约信息, 优先级最高, 用户输入的语言中包含“邀约”、“邀请”、“邀约信息”、“邀请信息”等关键词并有查询的意愿时，会优先调用此工具

        Args:
            keyword(string): 关键词
        '''
        try:
            results = await self._get_invite_info(keyword, event.session_id)
            chain = self._replay_invite_info(results)
            yield event.chain_result(chain)

            event.stop_event() # 停止事件传播
            # return f"获取成功"

        except Exception as e:
            event.stop_event() # 停止事件传播
            # return f"获取邀约信息失败：{str(e)}"

    async def _set_invite_info(self, invite_info: str, message: str, session_id: str):
        '''设置邀约信息'''
        if message.startswith("set_invite"):
            invite_info = message.split("set_invite_text")[1]

        provider = self.context.get_provider_by_id("set_invite")
        result = await provider.text_chat(
            prompt=invite_info,
            session_id=session_id,
        )
        return result.completion_text
    
    def _replay_set_invite_info(self, result: str):
        chain = []
        if result:
            chain.append(Plain("设置成功"))
        else:
            chain.append(Plain("设置失败"))
        return chain
    
    @filter.command("set_invite")
    async def set_invite(self, event: AstrMessageEvent, invite_info: str):
        '''这是一个设置邀请文本的指令'''
        result = await self._set_invite_info(invite_info, event.get_message_str(), event.session_id)
        chain = self._replay_set_invite_info(result)
        yield event.chain_result(chain)
    
    @filter.llm_tool(name="inner_set_invite_info")
    async def inner_set_invite_info(self, event: Union[AstrMessageEvent, Context], invite_info: str):
        '''设置邀约信息, 优先级最高, 用户输入的语言中包含“设置邀约”、“修改邀约”、“更新邀约”等关键词并有设置的意愿时，会优先调用此工具

        Args:
            invite_info(string): 邀约信息
        '''
        try:
            result = await self._set_invite_info(invite_info, event.get_message_str(), event.session_id)
            chain = self._replay_set_invite_info(result)
            yield event.chain_result(chain)
            event.stop_event()

        except Exception as e:
            event.stop_event()
        
    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''
