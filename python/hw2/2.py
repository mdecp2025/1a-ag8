from browser import document, html, timer

# --- 全域常數設定 ---
CELL_SIZE = 40      # 每個格子的大小 (像素)
WALL_THICKNESS = 6  # 牆壁的厚度
IMG_PATH = "https://mde.tw/cp2025/reeborg/src/images/"

# --- 世界繪製類別 ---
class World:
    """負責建立網格、牆壁與管理不同繪圖層"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = self._create_layers()
        self._init_html()
        self._draw_grid()
        self._draw_walls()

    def _create_layers(self):
        """建立四個重疊的畫布圖層：網格、牆壁、軌跡、機器人"""
        return {
            "grid": html.CANVAS(
                width=self.width * CELL_SIZE, height=self.height * CELL_SIZE
            ),
            "walls": html.CANVAS(
                width=self.width * CELL_SIZE, height=self.height * CELL_SIZE
            ),
            "objects": html.CANVAS(
                width=self.width * CELL_SIZE, height=self.height * CELL_SIZE
            ),
            "robots": html.CANVAS(
                width=self.width * CELL_SIZE, height=self.height * CELL_SIZE
            ),
        }

    def _init_html(self):
        """初始化 HTML 結構，將畫布放入指定的 div 中並設定層次 (zIndex)"""
        container = html.DIV(
            style={
                "position": "relative",
                "width": f"{self.width * CELL_SIZE}px",
                "height": f"{self.height * CELL_SIZE}px",
            }
        )
        for z, canvas in enumerate(self.layers.values()):
            canvas.style = {
                "position": "absolute",
                "top": "0px",
                "left": "0px",
                "zIndex": str(z),
            }
            container <= canvas
        document["brython_div1"].clear()
        document["brython_div1"] <= container

    def _draw_grid(self):
        """在 grid 圖層繪製背景網格線"""
        ctx = self.layers["grid"].getContext("2d")
        ctx.strokeStyle = "#cccccc"
        for i in range(self.width + 1):
            ctx.beginPath()
            ctx.moveTo(i * CELL_SIZE, 0)
            ctx.lineTo(i * CELL_SIZE, self.height * CELL_SIZE)
            ctx.stroke()
        for j in range(self.height + 1):
            ctx.beginPath()
            ctx.moveTo(0, j * CELL_SIZE)
            ctx.lineTo(self.width * CELL_SIZE, j * CELL_SIZE)
            ctx.stroke()

    def _draw_image(self, ctx, src, x, y, w, h, offset_x=0, offset_y=0):
        """通用圖片繪製函式，處理座標轉換並確保圖片載入後繪製"""
        img = html.IMG()
        img.src = src

        def onload(evt):
            # 座標轉換：將邏輯座標 (x, y) 轉換為畫布像素座標
            px = x * CELL_SIZE + offset_x
            py = (self.height - 1 - y) * CELL_SIZE + offset_y
            ctx.drawImage(img, px, py, w, h)

        img.bind("load", onload)

    def _draw_walls(self):
        """繪製地圖四邊的邊界牆"""
        ctx = self.layers["walls"].getContext("2d")
        for x in range(self.width):
            # 北牆：貼在頂部格子邊緣
            self._draw_image(
                ctx,
                IMG_PATH + "north.png",
                x,
                self.height - 1,
                CELL_SIZE,
                WALL_THICKNESS,
                offset_y=0,
            )
            # 南牆：貼在底部格子邊緣
            self._draw_image(
                ctx,
                IMG_PATH + "north.png",
                x,
                0,
                CELL_SIZE,
                WALL_THICKNESS,
                offset_y=CELL_SIZE - WALL_THICKNESS,
            )
        for y in range(self.height):
            # 西牆：貼在左側格子邊緣
            self._draw_image(
                ctx, IMG_PATH + "east.png", 0, y, WALL_THICKNESS, CELL_SIZE, offset_x=0
            )
            # 東牆：貼在右側格子邊緣
            self._draw_image(
                ctx,
                IMG_PATH + "east.png",
                self.width - 1,
                y,
                WALL_THICKNESS,
                CELL_SIZE,
                offset_x=CELL_SIZE - WALL_THICKNESS,
            )

    def robot(self, x, y):
        """在地圖上放置靜態機器人圖示 (標示初始位置)"""
        ctx = self.layers["robots"].getContext("2d")
        self._draw_image(
            ctx, IMG_PATH + "blue_robot_e.png", x - 1, y - 1, CELL_SIZE, CELL_SIZE
        )


# --- 動畫機器人類別 ---
class AnimatedRobot:
    """處理機器人的動作佇列、轉向與移動動畫"""
    def __init__(self, world, x, y):
        self.world = world
        self.x = x - 1    # 內部使用 0-indexed 座標
        self.y = y - 1
        self.facing = "E" # 預設面向東
        self.facing_order = ["E", "N", "W", "S"] # 逆時針方向定義
        self.robot_ctx = world.layers["robots"].getContext("2d")
        self.trace_ctx = world.layers["objects"].getContext("2d")
        self.queue = []      # 待執行動作佇列
        self.running = False # 是否正在執行動畫
        self._draw_robot()

    def _robot_image(self):
        """根據目前面向的方向回傳對應的圖片檔名"""
        return {
            "E": "blue_robot_e.png",
            "N": "blue_robot_n.png",
            "W": "blue_robot_w.png",
            "S": "blue_robot_s.png",
        }[self.facing]

    def _draw_robot(self):
        """在畫布上重新繪製目前位置與方向的機器人"""
        self.robot_ctx.clearRect(
            0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE
        )
        self.world._draw_image(
            self.robot_ctx,
            IMG_PATH + self._robot_image(),
            self.x,
            self.y,
            CELL_SIZE,
            CELL_SIZE,
        )

    def _draw_trace(self, from_x, from_y, to_x, to_y):
        """在機器人移動路徑上繪製紅色足跡線"""
        ctx = self.trace_ctx
        ctx.strokeStyle = "#d33"
        ctx.lineWidth = 2
        ctx.beginPath()
        # 計算格子中心點座標
        fx = from_x * CELL_SIZE + CELL_SIZE / 2
        fy = (self.world.height - 1 - from_y) * CELL_SIZE + CELL_SIZE / 2
        tx = to_x * CELL_SIZE + CELL_SIZE / 2
        ty = (self.world.height - 1 - to_y) * CELL_SIZE + CELL_SIZE / 2
        ctx.moveTo(fx, fy)
        ctx.lineTo(tx, ty)
        ctx.stroke()

    def move(self, steps):
        """將移動命令加入佇列並啟動執行"""
        def action(next_done):
            def step():
                nonlocal steps
                if steps == 0:
                    next_done()
                    return
                from_x, from_y = self.x, self.y
                dx, dy = 0, 0
                if self.facing == "E": dx = 1
                elif self.facing == "W": dx = -1
                elif self.facing == "N": dy = 1
                elif self.facing == "S": dy = -1
                
                next_x = self.x + dx
                next_y = self.y + dy

                # 邊界檢查：防止機器人走出世界外
                if 0 <= next_x < self.world.width and 0 <= next_y < self.world.height:
                    self.x, self.y = next_x, next_y
                    self._draw_trace(from_x, from_y, self.x, self.y)
                    self._draw_robot()
                    steps -= 1
                    timer.set_timeout(step, 200) # 每格移動間隔 200ms
                else:
                    print("🚨 已經撞牆，停止移動！")
                    next_done()

            step()

        self.queue.append(action)
        self._run_queue()

    def turn_left(self):
        """將左轉命令加入佇列"""
        def action(done):
            idx = self.facing_order.index(self.facing)
            self.facing = self.facing_order[(idx + 1) % 4]
            self._draw_robot()
            timer.set_timeout(done, 300) # 轉向間隔 300ms

        self.queue.append(action)
        self._run_queue()

    def _run_queue(self):
        """依序執行動作佇列中的任務"""
        if self.running or not self.queue:
            return
        self.running = True
        action = self.queue.pop(0)
        action(lambda: self._done())

    def _done(self):
        """動作完成後，標記狀態為非執行中並嘗試下一個動作"""
        self.running = False
        self._run_queue()


# --- 主程式執行區塊 ---

w = World(10, 10)  # 建立 10x10 的世界
w.robot(1, 1)      # 在 (1,1) 放置初始參考機器人

r = AnimatedRobot(w, 1, 1) # 建立執行移動動畫的機器人

# 初始動作：先轉向北邊開始垂直蛇形走法
r.turn_left()

# 使用 5 個迴圈，每個迴圈走完一組「上來、右移、下去、再右移」
for j in range(5):
    # 1. 向上走到底 (9 步)
    r.move(9)
    
    # 2. 右轉 (連續三次左轉) 並右移一格
    r.turn_left()
    r.turn_left()
    r.turn_left()
    r.move(1)
    
    # 3. 再右轉 (連續三次左轉) 轉向南邊向下
    r.turn_left()
    r.turn_left()
    r.turn_left()
    
    # 4. 向下走到底 (9 步)
    r.move(9)
    
    # 5. 左轉並右移一格，為下一次垂直向上的路徑準備
    r.turn_left()
    r.move(1)
    
    # 6. 最後左轉轉回北邊
    r.turn_left()

# 註：此垂直蛇形走法最後會因為最後一次 move(1) 觸碰邊界而結束。
