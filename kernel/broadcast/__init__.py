from nonebot import on_command, get_driver, Bot
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.log import logger
from asyncio import sleep
from random import randint, random

svcmd = on_command("广播")

@svcmd.handle()
async def _(bot: Bot, ev: PrivateMessageEvent, msg: Message=CommandArg()):
    if ev.get_user_id() not in get_driver().config.superusers:
        await svcmd.finish("permission denied: you are not admin")
    msgline = msg.extract_plain_text()
    if not msgline:
        await svcmd.finish("广播内容为空")

    groups = await bot.call_api('get_group_list')
    grouplist = []
    for group in groups:
        grouplist.append(group['group_id'])

    await svcmd.send(f'开始推送...')

    for group in grouplist:
        msglinexx = msgline + f'\n随机数防暴毙：{randint(1000, 9999)}'
        message_id = await bot.call_api('send_msg', group_id=group, message=msglinexx)
        if message_id:
            logger.info(f'向{group}推送消息成功')
        else:
            logger.info(f'向{group}推送消息失败')
            await svcmd.send(f'向{group}推送消息失败')
        await sleep(random() * 2)

    await svcmd.send(f'推送完成，共计向{len(grouplist)}个群推送了消息')

    return
