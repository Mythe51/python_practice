from nonebot import on_command, get_driver, on_fullmatch, Bot
from nonebot.permission import SUPERUSER
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from nonebot.message import run_preprocessor, IgnoredException
from nonebot.matcher import Matcher
from nonebot.log import logger
from nonebot.adapters.onebot.v11.event import (
    PrivateMessageEvent,
    FriendAddNoticeEvent,
    FriendRecallNoticeEvent,
    FriendRequestEvent,
    GroupRequestEvent,
)

import time

from .AuthSql import *
from .CdkeySql import *

sv_GenerateCdkey = on_command('生成cdkey', permission=SUPERUSER)
sv_SearchCdkey = on_command('查询cdkey', permission=SUPERUSER)
sv_DeleteCdkey = on_command('删除cdkey', permission=SUPERUSER)
sv_UseCdkey = on_fullmatch('使用cdkey')

driver = get_driver()

@driver.on_bot_connect
async def _(bot: Bot):
    # 获取所有已加入的群，写入数据库
    groups = await bot.call_api('get_group_list')
    for group in groups:
        auth_sql = AuthSql()
        data = auth_sql.SelectTableByGroup(group['group_id'])
        if not data:
            auth_sql.InsertTable(group['group_id'])
    logger.info(f"已加载{len(groups)}个群到数据库")
    return

@run_preprocessor
async def _(bot: Bot, ev: Event, matcher: Matcher):
    # 过滤器，指定未授权的群只能使用核心插件

    if ev.get_user_id() in get_driver().config.superusers:
        return      # 超级管理员无条件放行

    model = matcher.module_name
    if not isinstance(model, str):
        return      # 模块的点路径名称为空，应该是什么碰都不能碰的滑梯，直接放行
    if model.startswith('kernel'):
        return      # 模块的点路径开头是kernel，无论何时都应该放行

    if isinstance(model, PrivateMessageEvent) or \
        isinstance(model, FriendAddNoticeEvent) or \
        isinstance(model, FriendRecallNoticeEvent) or \
        isinstance(model, FriendRequestEvent) or \
        isinstance(model, GroupRequestEvent):
        return      # 指定的非拦截对象

    # 剩下的是其他插件，这里就需要检查群的权限了
    auth_sql = AuthSql()
    data = auth_sql.SelectTableByGroup(ev.get_session_id().split('_')[1])


    now = time.time()
    validate = data.deadline if data.deadline is not None else 0

    if now < validate:
        return

    await bot.send(ev, 'permission denied: group not authorizated')
    matcher.stop_propagation()
    raise IgnoredException('permission denied: group not authorizated')

    return
