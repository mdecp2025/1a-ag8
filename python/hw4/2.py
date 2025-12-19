# 巡邏完畢後, 使用鍵盤 j 前進, i 左轉, 也可以利用觸控按鈕控制前進與左轉
import js, asyncio

# --- 全域常數設定 ---
CELL_SIZE = 40      # 每個格子的大小 (像素)
WALL_THICKNESS = 6  # 牆壁的厚度
IMG_PATH = "https://mde.tw/cp2025/reeborg/src/images/"

# --- 世界繪製類別 ---
class World:
    """負責建立網格、牆壁與管理不同的 HTML5 Canvas 繪圖層"""
    _image_cache = {} # 靜態類別屬性，用於快取已載入的圖片

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = self._create_layers()
        self._init_html()

    def _create_layers(self):
        """建立四個重疊的 Canvas 元素：網格、牆壁、軌跡、機器人"""
        return {
            "grid": js.document.createElement("canvas"),
            "walls": js.document.createElement("canvas"),
            "objects": js.document.createElement("canvas"),
            "robots": js.document.createElement("canvas"),
        }

    def _init_html(self):
        """初始化 HTML 結構，設定畫布層次並新增控制按鈕"""
        container = js.document.createElement("div")
        container.style.position = "relative"
        container.style.width = f"{self.width * CELL_SIZE}px"
        container.style.height = f"{self.height * CELL_SIZE}px"

        for z, canvas in enumerate(self.layers.values()):
            canvas.width = self.width * CELL_SIZE
            canvas.height = self.height * CELL_SIZE
            canvas.style.position = "absolute"
            canvas.style.top = "0px"
            canvas.style.left = "0px"
            canvas.style.zIndex = str(z)
            container.appendChild(canvas)

        # 建立按鈕容器
        button_container = js.document.createElement("div")
        button_container.style.marginTop = "10px"
        button_container.style.textAlign = "center"

        # 前進按鈕
        move_button = js.document.createElement("button")
        move_button.innerHTML = "Move Forward"
        move_button.style.margin = "5px"
        move_button.style.padding = "10px 20px"
        move_button.style.fontSize = "16px"
        button_container.appendChild(move_button)

        # 左轉按鈕
        turn_button = js.document.createElement("button")
        turn_button.innerHTML = "Turn Left"
        turn_button.style.margin = "5px"
        turn_button.style.padding = "10px 20px"
        turn_button.style.fontSize = "16px"
        button_container.appendChild(turn_button)

        # 取得目標 div 並注入內容
        brython_div = js.document.getElementById("brython_div1")
        if not brython_div:
            raise RuntimeError("🚨 'brython_div1' element not found in HTML!")
        brython_div.innerHTML = ""
        brython_div.appendChild(container)
        brython_div.appendChild(button_container)

        # 儲存按鈕引用以便後續綁定事件
        self.move_button = move_button
        self.turn_button = turn_button

    def _draw_grid(self):
        """繪製背景網格"""
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

    def _draw_image(self, ctx, img_key, x, y, w, h, offset_x=0, offset_y=0):
        """繪製快取中的圖片，包含座標轉換"""
        img = World._image_cache.get(img_key)
        if img and img.complete and img.naturalWidth > 0:
            px = x * CELL_SIZE + offset_x
            py = (self.height - 1 - y) * CELL_SIZE + offset_y
            ctx.drawImage(img, px, py, w, h)
            return True
        else:
            print(f"⚠️ Image '{img_key}' not ready for drawing.")
            return False

    async def _draw_walls(self):
        """繪製地圖四周的牆壁"""
        ctx = self.layers["walls"].getContext("2d")
        ctx.clearRect(0, 0, self.width * CELL_SIZE, self.height * CELL_SIZE)
        success = True
        for x in range(self.width):
            # 北牆與南牆
            success &= self._draw_image(ctx, "north", x, self.height - 1, CELL_SIZE, WALL_THICKNESS, offset_y=0)
            success &= self._draw_image(ctx, "north", x, 0, CELL_SIZE, WALL_THICKNESS, offset_y=CELL_SIZE - WALL_THICKNESS)
        for y in range(self.height):
            # 西牆與東牆
            success &= self._draw_image(ctx, "east", 0, y, WALL_THICKNESS, CELL_SIZE, offset_x=0)
            success &= self._draw_image(ctx, "east", self.width - 1, y, WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)
        return success

    async def _preload_images(self):
        """非同步預載所有機器人與牆壁圖片"""
        image_files = {
            "blue_robot_e": "blue_robot_e.png", "blue_robot_n": "blue_robot_n.png",
            "blue_robot_w": "blue_robot_w.png", "blue_robot_s": "blue_robot_s.png",
            "north": "north.png", "east": "east.png",
        }

        promises = []
        for key, filename in image_files.items():
            if key in World._image_cache and World._image_cache[key].complete:
                continue

            img = js.document.createElement("img")
            img.crossOrigin = "Anonymous"
            img.src = IMG_PATH + filename
            World._image_cache[key] = img

            def make_promise(img_element):
                def executor(resolve, reject):
                    def on_load(event): resolve(img_element)
                    def on_error(event): reject(f"Failed to load: {img_element.src}")
                    img_element.addEventListener("load", on_load)
                    img_element.addEventListener("error", on_error)
                    if img_element.complete: resolve(img_element)
                return js.Promise.new(executor)

            promises.append(make_promise(img))

        if not promises: return True
        try:
            await js.await_promise(js.Promise.all(promises))
            return True
        except Exception as e:
            print(f"🚨 Preload error: {e}")
            return False

    async def setup(self):
        """執行啟動流程：載入圖片 -> 繪製網格 -> 繪製牆壁"""
        if not await self._preload_images(): return False
        await asyncio.sleep(0) # 讓出執行權
        self._draw_grid()
        if not await self._draw_walls(): return False
        return True


# --- 動畫機器人類別 ---
class AnimatedRobot:
    """處理機器人的邏輯位置、轉向與非同步移動動畫"""
    def __init__(self, world, x, y):
        self.world = world
        self.x = x - 1
        self.y = y - 1
        self.facing = "E"
        self.facing_order = ["E", "N", "W", "S"]
        self.robot_ctx = world.layers["robots"].getContext("2d")
        self.trace_ctx = world.layers["objects"].getContext("2d")
        self._draw_robot()

    def _robot_image_key(self):
        return f"blue_robot_{self.facing.lower()}"

    def _draw_robot(self):
        """重繪機器人目前的圖像"""
        self.robot_ctx.clearRect(0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE)
        self.world._draw_image(self.robot_ctx, self._robot_image_key(), self.x, self.y, CELL_SIZE, CELL_SIZE)

    def _draw_trace(self, from_x, from_y, to_x, to_y):
        """繪製移動後的紅色軌跡"""
        ctx = self.trace_ctx
        ctx.strokeStyle = "#d33"
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(from_x * CELL_SIZE + CELL_SIZE/2, (self.world.height-1-from_y) * CELL_SIZE + CELL_SIZE/2)
        ctx.lineTo(to_x * CELL_SIZE + CELL_SIZE/2, (self.world.height-1-to_y) * CELL_SIZE + CELL_SIZE/2)
        ctx.stroke()

    async def move(self, steps=1):
        """前進指定步數（非同步執行）"""
        for _ in range(steps):
            from_x, from_y = self.x, self.y
            dx, dy = 0, 0
            if self.facing == "E": dx = 1
            elif self.facing == "W": dx = -1
            elif self.facing == "N": dy = 1
            elif self.facing == "S": dy = -1
            
            next_x, next_y = self.x + dx, self.y + dy
            if 0 <= next_x < self.world.width and 0 <= next_y < self.world.height:
                self.x, self.y = next_x, next_y
                self._draw_trace(from_x, from_y, self.x, self.y)
                self._draw_robot()
                await asyncio.sleep(0.2)
            else:
                print("🚨 撞牆了！")
                break

    async def turn_left(self):
        """向左轉 90 度"""
        idx = self.facing_order.index(self.facing)
        self.facing = self.facing_order[(idx + 1) % 4]
        self._draw_robot()
        await asyncio.sleep(0.3)


# --- 主程式：巡邏序列與手動控制 ---
async def start_robot_patrol():
    print("🚀 啟動模擬...")
    world = World(10, 10)
    if not await world.setup(): return

    # 全域引用，讓事件處理器能存取
    global robot_instance
    robot_instance = AnimatedRobot(world, 1, 1)

    print("🧭 自動巡邏開始...")
    robot_instance.turn_left()
    for j in range(5):
        await robot_instance.move(9)
        await robot_instance.turn_left()
        await robot_instance.move(1)
        await robot_instance.turn_left()
        await robot_instance.move(9)
        # 轉向右移並回到向上方向
        await robot_instance.turn_left()
        await robot_instance.turn_left()
        await robot_instance.turn_left()
        await robot_instance.move(1)
        await robot_instance.turn_left()
        await robot_instance.turn_left()
        await robot_instance.turn_left()

    print("🚩 巡邏完成！現在你可以用鍵盤或按鈕手動控制。")

    # --- 事件處理定義 ---
    def handle_key(event):
        """處理鍵盤 j (前進) 與 i (左轉)"""
        try:
            if event.key == "j":
                asyncio.create_task(robot_instance.move(1))
            elif event.key == "i":
                asyncio.create_task(robot_instance.turn_left())
        except Exception as e: print(e)

    def handle_move_button(event):
        asyncio.create_task(robot_instance.move(1))

    def handle_turn_button(event):
        asyncio.create_task(robot_instance.turn_left())

    # --- 註冊事件監聽器 ---
    try:
        # 鍵盤監聽
        js.window.py_handle_key = handle_key
        js.document.addEventListener("keydown", js.Function("event", "py_handle_key(event);"))
        
        # 按鈕監聽 (利用之前儲存的按鈕引用)
        js.window.py_handle_move_button = handle_move_button
        js.window.py_handle_turn_button = handle_turn_button
        world.move_button.addEventListener("click", js.Function("event", "py_handle_move_button(event);"))
        world.turn_button.addEventListener("click", js.Function("event", "py_handle_turn_button(event);"))
        
        print("✅ 控制事件已註冊成功。")
    except Exception as e:
        print(f"🚨 事件註冊失敗: {e}")

# 啟動非同步主任務
asyncio.create_task(start_robot_patrol())
