# game.py
from browser import document, html, timer, ajax, window
from random import random

canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")
WIDTH, HEIGHT = 800, 400

# 圖片
bird_img = html.IMG(src="/static/images/bird.png")
pig_img = html.IMG(src="/static/images/pig.png")

# 遊戲狀態
SLING_X, SLING_Y = 120, 300
MAX_SHOTS = 10
shots_fired = 0
total_score = 0
current_shot_score = 0
mouse_down = False
mouse_pos = (SLING_X, SLING_Y)
projectile = None
sent = False


def aabb_intersect(ax, ay, aw, ah, bx, by, bw, bh):
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# ------------------------------------------
# 類別
# ------------------------------------------
class Pig:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.w, self.h = 40, 40
        self.alive = True

        # 房舍相對於小豬的相對位置
        self.house_blocks = [
            (0, 40, 120, 15),
            (0, -10, 15, 50),
            (105, -10, 15, 50),
            (0, -25, 120, 15),
        ]

        # 與舊程式相容：重建房舍時會用到
        self.house_layout = self.house_blocks

    def draw(self):
        if self.alive:
            ctx.drawImage(pig_img, self.x, self.y, self.w, self.h)

    def hit(self, px, py):
        return (
            self.alive
            and self.x <= px <= self.x + self.w
            and self.y <= py <= self.y + self.h
        )

    def relocate(self):
        MIN_X = 450
        MAX_X = WIDTH - self.w - 120
        MIN_Y = 200
        MAX_Y = HEIGHT - self.h - 15

        new_x = MIN_X + random() * (MAX_X - MIN_X)
        new_y = MIN_Y + random() * (MAX_Y - MIN_Y)

        self.x = new_x
        self.y = new_y


class Block:

    def __init__(self, owner, rx, ry, w, h, hp=1):
        # owner: Pig
        # rx/ry: 相對於小豬位置的偏移（要跟原本 Pig.draw 的 house_blocks 畫法一致）
        self.owner = owner
        self.rx, self.ry = rx, ry
        self.w, self.h = w, h
        self.hp = hp
        self.alive = True

    def rect(self):
        # 原本房舍畫法是：ctx.fillRect(self.x + rx - 40, self.y + ry, ...)
        # 所以碰撞框也要用同樣的座標
        x = self.owner.x + self.rx - 40
        y = self.owner.y + self.ry
        return x, y, self.w, self.h

    def draw(self):
        if not self.alive:
            return
        x, y, w, h = self.rect()
        ctx.fillStyle = "saddlebrown"
        ctx.fillRect(x, y, w, h)

    def take_hit(self, damage=1):
        if not self.alive:
            return False
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False


class Bird:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.w, self.h = 35, 35
        self.active = True

    def update(self):
        global current_shot_score, total_score
        if not self.active:
            return
        self.vy += 0.35
        self.x += self.vx
        self.y += self.vy

        if self.y > HEIGHT - self.h or self.x > WIDTH or self.x < 0:
            self.active = False
        for b in blocks:
            if not b.alive:
                continue
            bx, by, bw, bh = b.rect()
            if aabb_intersect(self.x, self.y, self.w, self.h, bx, by, bw, bh):
                destroyed = b.take_hit(1)
                if destroyed:
                    current_shot_score += 10
                    total_score += 10
                    document["score_display"].text = str(total_score)

                    # 該豬的箱子全被打掉後，才給他新家
                    if all_blocks_destroyed_for_pig(b.owner):
                        give_pig_new_house(b.owner)

                # 簡化：撞到箱子就結束這發（你也可以改成反彈/減速）
                self.active = False
                return
        for p in pigs:
            if p.hit(self.x + self.w / 2, self.y + self.h / 2):
                if p.alive:
                    p.relocate()
                    current_shot_score += 50
                    total_score += 50
                    document["score_display"].text = str(total_score)

    def draw(self):
        ctx.drawImage(bird_img, self.x, self.y, self.w, self.h)


# ------------------------------------------
# 遊戲控制函數
# ------------------------------------------
pigs = []
blocks = []


def all_blocks_destroyed_for_pig(pig):
    return not any(b.alive and b.owner is pig for b in blocks)


def give_pig_new_house(pig):
    # 讓「新家」更有感：先換位置再重建一組箱子
    pig.relocate()
    rebuild_house_for_pig(pig)


def rebuild_house_for_pig(pig):
    """移除該豬舊的箱子，並依 house_layout 重建一組新的箱子"""
    global blocks
    blocks = [b for b in blocks if b.owner is not pig]
    for rx, ry, rw, rh in pig.house_layout:
        blocks.append(Block(pig, rx, ry, rw, rh, hp=1))


def init_level():
    global pigs, blocks
    pigs = []
    blocks = []
    pig = Pig(545, 260)
    pigs.append(pig)
    rebuild_house_for_pig(pig)


def reset_sling_state():
    global shots_fired, current_shot_score, projectile, sent
    shots_fired = 0
    current_shot_score = 0
    projectile = None
    sent = False
    init_level()
    update_shots_remaining()


def start_new_game():
    global total_score
    total_score = 0
    document["score_display"].text = str(total_score)
    reset_sling_state()


def update_shots_remaining():
    document["shots_remaining"].text = str(MAX_SHOTS - shots_fired)


def get_mouse_pos(evt):
    return evt.x - canvas.offsetLeft, evt.y - canvas.offsetTop


def mousedown(evt):
    global mouse_down, mouse_pos
    if projectile is None and shots_fired < MAX_SHOTS:
        mouse_down = True
        mouse_pos = get_mouse_pos(evt)


def mousemove(evt):
    global mouse_pos
    if mouse_down:
        mouse_pos = get_mouse_pos(evt)


def mouseup(evt):
    global mouse_down, projectile, shots_fired, current_shot_score
    if mouse_down and projectile is None:
        current_shot_score = 0
        mouse_down = False
        end_pos = get_mouse_pos(evt)
        dx = SLING_X - end_pos[0]
        dy = SLING_Y - end_pos[1]
        projectile = Bird(SLING_X, SLING_Y, dx * 0.25, dy * 0.25)
        shots_fired += 1
        update_shots_remaining()


canvas.bind("mousedown", mousedown)
canvas.bind("mousemove", mousemove)
canvas.bind("mouseup", mouseup)


def draw_sling():
    ctx.strokeStyle = "black"
    ctx.lineWidth = 4
    if mouse_down:
        mx, my = mouse_pos
        ctx.beginPath()
        ctx.moveTo(SLING_X - 5, SLING_Y)
        ctx.lineTo(mx, my)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(SLING_X + 5, SLING_Y)
        ctx.lineTo(mx, my)
        ctx.stroke()
        ctx.drawImage(bird_img, mx - 17, my - 17, 35, 35)
    else:
        if projectile is None and shots_fired < MAX_SHOTS:
            ctx.drawImage(bird_img, SLING_X - 17, SLING_Y - 17, 35, 35)


def send_score():
    """使用異步 AJAX 提交分數"""
    global sent, total_score
    if sent:
        return
    sent = True

    def on_complete(req):
        if req.status == 200:
            print("Score saved successfully.")
        else:
            try:
                resp = window.JSON.parse(req.text)
                msg = resp.message
            except:
                msg = "Server error or bad response format."
            print(f"Score submission failed: HTTP {req.status}, Message: {msg}")

    req = ajax.ajax()
    req.bind("complete", on_complete)

    req.open("POST", "/submit_score", True)
    req.set_header("Content-Type", "application/json")

    data = {"score": total_score}
    json_payload = window.JSON.stringify(data)

    req.send(json_payload)


# ------------------------------------------
# 遊戲主迴圈
# ------------------------------------------
def loop():
    global projectile
    ctx.clearRect(0, 0, WIDTH, HEIGHT)

    # 先畫箱子（被打爆就不畫）
    for b in blocks:
        b.draw()

    for p in pigs:
        p.draw()

    game_over = shots_fired >= MAX_SHOTS

    if projectile:
        projectile.update()
        projectile.draw()

        if not projectile.active:
            projectile = None

            if game_over:
                send_score()
                timer.set_timeout(start_new_game, 2000)
            else:
                pass

    elif game_over:
        send_score()
        timer.set_timeout(start_new_game, 2000)

    draw_sling()


timer.set_interval(loop, 30)
start_new_game()
