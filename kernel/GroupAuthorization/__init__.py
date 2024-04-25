from nonebot import on_command, get_driver, on_fullmatch, Bot
from nonebot.permission import SUPERUSER
from nonebot.adapters import Message, Event
from nonebot.params import CommandArg
from nonebot.message import run_preprocessor, IgnoredException
from nonebot.exception import MatcherException
from nonebot.matcher import Matcher
from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.event import (
    PrivateMessageEvent,
    FriendAddNoticeEvent,
    FriendRecallNoticeEvent,
    FriendRequestEvent,
    GroupRequestEvent,
    GroupMessageEvent
)

import time
from random import choices
from datetime import datetime, timedelta

from .AuthSql import *
from .CdkeySql import *

sv_GenerateCdkey = on_command('生成cdkey', permission=SUPERUSER)
sv_SearchCdkey = on_command('查询cdkey', permission=SUPERUSER)
sv_DeleteCdkey = on_command('删除cdkey', permission=SUPERUSER)
sv_AdminAuth = on_command('群授权', permission=SUPERUSER)
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

    if isinstance(ev, PrivateMessageEvent) or \
        isinstance(ev, FriendAddNoticeEvent) or \
        isinstance(ev, FriendRecallNoticeEvent) or \
        isinstance(ev, FriendRequestEvent) or \
        isinstance(ev, GroupRequestEvent):
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

@sv_GenerateCdkey.handle()
async def _(ev: Event, arg: Message = CommandArg()):
    if not isinstance(ev, PrivateMessageEvent):
        await sv_GenerateCdkey.finish('only for private message')

    args = arg.extract_plain_text().split(' ')
    if len(args) != 2:
        await sv_GenerateCdkey.finish('usage: 生成cdkey [面值] [生效时长]')

    value = int(args[0])
    validate = int(args[1])

    if 0 >= value or 0 >= validate:
        await sv_GenerateCdkey.finish('args invalid')

    alphabats = "QWERTYUIOPASDFGHJKLZXCVBNM123456789"
    cdkey = '-'.join([''.join(choices(alphabats, k=5)) for _ in range(5)])

    cdkey_sql = CdkeySql()
    data = CdkeyTable(cdkey, createtime=int(time.time()),
                      validatetime=int(int(time.time())+timedelta(days=validate).total_seconds()),
                      value=value)

    cdkey_sql.InsertTable(data)

    await sv_GenerateCdkey.finish(f'''
cdkey：{cdkey}
请在 {datetime.datetime.fromtimestamp(data.validatetime).strftime("%Y-%m-%d %H:%M:%S")} 前使用
有效时长：{value} 天
    '''.strip())


    return

@sv_SearchCdkey.handle()
async def _(ev: Event, arg: Message = CommandArg()):
    if not isinstance(ev, PrivateMessageEvent):
        await sv_GenerateCdkey.finish('only for private message')

    cdkey_sql = CdkeySql()
    args = arg.extract_plain_text().strip()
    if '-u' == args:
        data = cdkey_sql.SelectCdkey(True)
    if '-unu' == args:
        data = cdkey_sql.SelectCdkey(False)
    if not args:
        data = cdkey_sql.SelectCdkey()
    else:
        await sv_SearchCdkey.finish('usage: 查询cdkey [-u] [-unu]')

    if not data:
        await sv_SearchCdkey.finish('cdkey not found')

    text = ''
    for i in data:
        text += '------\n'
        text += 'cdkey：' + i.cdkey + '\n'
        text += '有效期至：' + datetime.datetime.fromtimestamp(i.validatetime).strftime('%Y-%m-%d %H:%M:%S') + '\n'
        text += '有效时长：' + str(i.value) + '天\n'
        text += '使用状态：' + ('已使用\n' if i.state == CdkeyState.USED.value else '未使用\n')
    await sv_SearchCdkey.finish(text.strip())

    return

@sv_DeleteCdkey.handle()
async def _(ev: Event, arg: Message = CommandArg()):
    if not isinstance(ev, PrivateMessageEvent):
        await sv_GenerateCdkey.finish('only for private message')

    args = arg.extract_plain_text()
    if not args:
        await sv_GenerateCdkey.finish('usage: 删除cdkey [cdkey]')

    cdk_sql = CdkeySql()
    try:
        cdk_sql.DeleteCdkeyByCdkey(args)
        await sv_DeleteCdkey.finish('delete success')
    except Exception as e:
        if not isinstance(e, MatcherException):
            await sv_GenerateCdkey.finish(str(e))
        else:
            pass

@sv_UseCdkey.handle()
async def _(state: T_State, ev: Event, arg: Message = CommandArg()):
    if isinstance(ev, PrivateMessageEvent):
        await sv_GenerateCdkey.finish('请群聊使用')

    args = arg.extract_plain_text()
    if args is not None:
        state['cdkey'] = args

    return

@sv_UseCdkey.got('cdkey', prompt="请输入cdkey")
async def _(state: T_State, ev: GroupMessageEvent):
    cdkey = state['cdkey'].extract_plain_text()
    cdkey_sql = CdkeySql()

    data = cdkey_sql.SelectCdkeyByCdkey(cdkey)

    if data is None:
        await sv_UseCdkey.finish("cdkey 未找到，请检查输入是否正确")

    if data.validatetime < time.time():
        await sv_UseCdkey.finish("cdkey 已过期，请联系管理员")

    if data.state == CdkeyState.USED.value:
        await sv_UseCdkey.finish("cdkey 已使用，请勿重复使用")

    groupid = ev.group_id

    # cdkey状态置为已使用
    cdkey_sql.UpdateCdkeyState(cdkey, CdkeyState.USED)
    # 添加群授权
    auth_sql = AuthSql()
    auth_sql.DoSingleAuth(groupid, data.value, AuthType.CDKEY)

    auth = auth_sql.SelectTableByGroup(groupid)

    # 发送消息
    await sv_UseCdkey.finish(f'授权成功，本次授权时长{data.value}天，到期时间'
                             f'{datetime.datetime.fromtimestamp(auth.deadline).strftime("%Y-%m-%d %H:%M:%S")}')
    return

@sv_AdminAuth.handle()
async def _(ev: Event, arg: Message = CommandArg()):
    if not isinstance(ev, PrivateMessageEvent):
        await sv_AdminAuth.finish('only for private message')

    args = arg.extract_plain_text().split(' ')
    if args is None or len(args) < 2:
        await sv_AdminAuth.finish('usage: 群授权 [群号] [授权天数]')

    groupid = args[0]
    validate = int(args[1])

    auth_sql = AuthSql()
    auth_sql.DoSingleAuth(groupid, validate, AuthType.ADMIN)

    auth = auth_sql.SelectTableByGroup(groupid)

    # 发送消息
    await sv_UseCdkey.finish(f'授权成功，本次授权时长{validate}天，到期时间'
                             f'{datetime.datetime.fromtimestamp(auth.deadline).strftime("%Y-%m-%d %H:%M:%S")}')

    return
