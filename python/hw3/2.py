from brython_robot4 import init, load_scene_from_url, get_url_parameter
from browser import aio


# 機器人行為腳本
async def robot_actions(robot):
    print("開始執行機器人程式，沿著路徑採收胡蘿蔔。")

    # 定義輔助函式：轉向 n 次
    async def turn(n):
        for i in range(n):
            await robot.turn_left()

    # 定義輔助函式：移動 n 格
    async def new_move(n):
        for i in range(n):
            await robot.move(1)

    # 定義輔助函式：採收一行
    async def harvest_one_row():
        while robot.background_is("pale_grass"):
            robot.pick_carrot()
        await robot.move(1)

    # 移動到田地起點
    await new_move(2)
    await robot.turn_left()
    await new_move(2)

    # 重複 3 次大循環
    for i in range(6):
        # 採收 6 行
        for j in range(6):
            await harvest_one_row()

        # 根據當前是奇數列還是偶數列來決定轉向
        if i % 2 == 0:  # 第 0, 2 次（面向北方）
            # 轉向並移動到下一列
            for k in range(2):
                await turn(3)  # 右轉
                await robot.move(1)
        else:  # 第 1 次（面向南方）
            # 轉向並移動到下一列
            for k in range(2):
                await robot.turn_left()
                await robot.move(1)

    print("路徑完成！")
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
