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
        """建立四個重疊的畫布圖層：網格、牆壁、足跡、機器人"""
        return {
            "grid": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "walls": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "objects": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "robots": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
        }

    def _init_html(self):
        """初始化 HTML 結構，將畫布放入指定的 div 中"""
        container = html.DIV(style={
            "position": "relative",
            "width": f"{self.width * CELL_SIZE}px",
            "height": f"{self.height * CELL_SIZE}px",
        })
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
        """在 grid 圖層繪製灰色背景網格線"""
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
        """通用圖片繪製函式，並處理座標轉換 (y 軸翻轉)"""
        img = html.IMG()
        img.src = src
        def onload(evt):
            px = x * CELL_SIZE + offset_x
            py = (self.height - 1 - y) * CELL_SIZE + offset_y
            ctx.drawImage(img, px, py, w, h)
        img.bind("load", onload)

    def _draw_walls(self):
        """繪製地圖四邊的牆壁邊界"""
        ctx = self.layers["walls"].getContext("2d")
        for x in range(self.width):
            # 北牆 (上方邊界)
            self._draw_image(ctx, IMG_PATH + "north.png", x, self.height - 1, CELL_SIZE, WALL_THICKNESS)
            # 南牆 (下方邊界)
            self._draw_image(ctx, IMG_PATH + "north.png", x, 0, CELL_SIZE, WALL_THICKNESS, offset_y=CELL_SIZE - WALL_THICKNESS)
        for y in range(self.height):
            # 西牆 (左側邊界)
            self._draw_image(ctx, IMG_PATH + "east.png", 0, y, WALL_THICKNESS, CELL_SIZE)
            # 東牆 (右側邊界)
            self._draw_image(ctx, IMG_PATH + "east.png", self.width - 1, y, WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)

    def robot(self, x, y):
        """在地圖上放置靜態機器人圖示 (初始位置)"""
        ctx = self.layers["robots"].getContext("2d")
        self._draw_image(ctx, IMG_PATH + "blue_robot_e.png", x - 1, y - 1, CELL_SIZE, CELL_SIZE)


# --- 動畫機器人類別 ---
class AnimatedRobot:
    """處理機器人的狀態管理、動作佇列與平滑動畫"""
    def __init__(self, world, x, y):
        self.world = world
        self.x = x - 1    # 內部使用 0-indexed 座標
        self.y = y - 1
        self.facing = "E" # 初始面向東方
        self.facing_order = ["E", "N", "W", "S"] # 逆時針方向順序
        self.robot_ctx = world.layers["robots"].getContext("2d")
        self.trace_ctx = world.layers["objects"].getContext("2d")
        self.queue = []      # 動作命令佇列 (FIFO)
        self.running = False # 標記目前是否正在播放動畫
        self._draw_robot()

    def _robot_image(self):
        """根據目前面向的方向回傳正確的機器人圖片名稱"""
        return {
            "E": "blue_robot_e.png", "N": "blue_robot_n.png",
            "W": "blue_robot_w.png", "S": "blue_robot_s.png",
        }[self.facing]

    def _draw_robot(self):
        """清除舊位置的機器人並在目前座標重新繪製"""
        self.robot_ctx.clearRect(0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE)
        self.world._draw_image(self.robot_ctx, IMG_PATH + self._robot_image(), self.x, self.y, CELL_SIZE, CELL_SIZE)

    def _draw_trace(self, from_x, from_y, to_x, to_y):
        """在機器人移動時，於 trace 圖層繪製紅色的軌跡線"""
        ctx = self.trace_ctx
        ctx.strokeStyle = "#d33"
        ctx.lineWidth = 2
        ctx.beginPath()
        fx = from_x * CELL_SIZE + CELL_SIZE / 2
        fy = (self.world.height - 1 - from_y) * CELL_SIZE + CELL_SIZE / 2
        tx = to_x * CELL_SIZE + CELL_SIZE / 2
        ty = (self.world.height - 1 - to_y) * CELL_SIZE + CELL_SIZE / 2
        ctx.moveTo(fx, fy)
        ctx.lineTo(tx, ty)
        ctx.stroke()

    def move(self, steps):
        """將移動命令加入佇列"""
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
                
                next_x, next_y = self.x + dx, self.y + dy
                # 檢查下一步是否會撞牆
                if 0 <= next_x < self.world.width and 0 <= next_y < self.world.height:
                    self.x, self.y = next_x, next_y
                    self._draw_trace(from_x, from_y, self.x, self.y)
                    self._draw_robot()
                    steps -= 1
                    timer.set_timeout(step, 200) # 移動每格間隔 200ms
                else:
                    print("🚨 已經撞牆，停止移動！")
                    next_done()
            step()
        self.queue.append(action)
        self._run_queue()

    def turn_left(self):
        """將轉向命令加入佇列 (逆時針轉 90 度)"""
        def action(done):
            idx = self.facing_order.index(self.facing)
            self.facing = self.facing_order[(idx + 1) % 4]
            self._draw_robot()
            timer.set_timeout(done, 300) # 轉向延遲 300ms
        self.queue.append(action)
        self._run_queue()

    def _run_queue(self):
        """從佇列中取出下一個動作並執行"""
        if self.running or not self.queue:
            return
        self.running = True
        action = self.queue.pop(0)
        action(lambda: self._done())

    def _done(self):
        """動作完成後的回呼，繼續執行下一個佇列命令"""
        self.running = False
        self._run_queue()


# --- 主程式執行區塊 (10x10 地圖與 5 個迴圈邏輯) ---

w = World(10, 10)  # 建立 10x10 的方格世界
w.robot(1, 1)      # 初始化畫面上的機器人圖示
r = AnimatedRobot(w, 1, 1) # 建立會動的機器人，起始座標 (1, 1)

# 使用 5 個迴圈走完 10 列：每 1 個迴圈處理 2 橫列 (S 型一來一回)
for i in range(5):
    # --- 第 1 部分：橫向走到底 (例如：從左到右) ---
    r.move(9)          # 移動 9 步到達第 10 格
    r.turn_left()      # 轉向北
    r.move(1)          # 向上移動 1 格進入下一列
    r.turn_left()      # 轉向西

    # --- 第 2 部分：反向橫向走到底 (例如：從右到左) ---
    r.move(9)          # 移動 9 步回到第 1 格

    # --- 第 3 部分：準備進入下一個雙列迴圈 ---
    # 如果不是最後一次迴圈，則需要上移並轉向東邊，開始下一輪
    if i < 4:
        # 這裡利用連續三次左轉達成「右轉」
        r.turn_left()
        r.turn_left()
        r.turn_left()  # 順時針轉向北
        r.move(1)      # 向上移動 1 格
        r.turn_left()
        r.turn_left()
        r.turn_left()  # 順時針轉向東，準備下一次迴圈首行的 move(9)

# 執行完畢後，機器人會精確停在 (1, 10) 面向西。
