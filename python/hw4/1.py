from brython_robot4 import init, load_scene_from_url, get_url_parameter
from browser import aio


# 機器人行為腳本
async def robot_actions(robot):
    print("開始執行機器人程式，探索並採收所有胡蘿蔔。")
    print("開始執行水平採收模式...")

    # 定義一個採收並檢查的動作
    def collect_here():
        while robot.background_is("pale_grass"):
            robot.pick_carrot()

    async def collect_and_move(n):
        for i in range(n):
            collect_here()
            await robot.move(1)

    # 定義向右轉 (因為只有 turn_left)
    async def turn_right():
        for _ in range(3):
            await robot.turn_left()

    await robot.move(2)
    await robot.turn_left()
    await robot.move(2)
    await robot.turn_right()
    await collect_and_move(5)
    for _ in range(2):
        await robot.turn_left()
        collect_here()
        await collect_and_move(1)
        await robot.turn_left()
        collect_here()
        await collect_and_move(5)

        await turn_right()
        collect_here()
        await robot.move(1)
        await turn_right()
        collect_here()
        await collect_and_move(5)
    await robot.turn_left()
    await collect_and_move(1)
    await robot.turn_left()
    await collect_and_move(5)
    collect_here()
    # 所有的探索和回溯動作都結束後，才會執行這裡的程式碼
    print("所有可達格子都已探索完畢。")
    print(f"程式執行完畢。總共採收了 {robot.carrots_collected} 個胡蘿蔔。")


# 程式啟動點
async def main():
    world_url = get_url_parameter("world")
    if world_url:
        scene_data = await load_scene_from_url(world_url)
        # 設定機器人容量上限為 50
        world, robot = init(scene_data, robot_config={"max_carrots": 50})
    else:
        # 預設場景也設定容量上限
        world, robot = init(robot_config={"max_carrots": 50})

    if robot:
        await robot_actions(robot)


# 啟動主程式
aio.run(main())
