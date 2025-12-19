# 定義右轉函數：因為機器人內建只有左轉，所以連續左轉三次等於右轉一次
def turn_right():
    turn_left()
    turn_left()
    turn_left()

# --- 起點標記 ---
# 在起點放下一個物體（例如球），作為「終點線」的記號
put()

# --- 起始方向調整 ---
# 如果前面是牆壁，就一直左轉直到前方空曠為止
while not front_is_clear():
    turn_left()

# 向前邁出第一步，這樣機器人才會離開起點的物體，避免迴圈立刻結束
move()

# --- 主迴圈：開始繞圈 ---
# 只要腳下沒有偵測到物體（也就是還沒回到起點），就持續執行
while not object_here():

    # 沿右牆走的邏輯：
    if right_is_clear():
        # 情況 A：如果右邊有空間（遇到轉角），就向右轉並前進
        turn_right()
        move()

    elif front_is_clear():
        # 情況 B：如果右邊有牆但前面沒牆，就穩定直走
        move()

    else:
        # 情況 C：如果前面和右邊都是牆（遇到死路），就向左轉
        turn_left()

# --- 結束動作 ---
# 當機器人偵測到起點放下的物體時，跳出迴圈並把東西撿起來，完美結束
take()
