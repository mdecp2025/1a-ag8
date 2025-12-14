import robot
import asyncio


async def main():
    world, r = await robot.init(10, 10, 1, 1)
    print("機器人開始行動")
    # 繞場一圈
    await r.turn_left()
    for j in range(5):
        await r.walk(9)
        await r.turn_left()
        await r.turn_left()
        await r.turn_left()
        await r.walk(1)
        await r.turn_left()
        await r.turn_left()
        await r.turn_left()
        await r.walk(9)
        await r.turn_left()
        await r.walk(1)
        await r.turn_left()
    print("🚩 巡邏完成！")


await main()
