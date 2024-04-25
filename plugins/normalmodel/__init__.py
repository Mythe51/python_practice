from nonebot import on_fullmatch

svping = on_fullmatch("!test")

@svping.handle()
async def _():
    await svping.finish("pong!")