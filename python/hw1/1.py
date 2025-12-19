# 讓機器人向前移動一格
move()
# 定義「向右轉」的函式：機器人原生只能左轉，連續左轉三次等於向右轉
def turn_right():
    turn_left()
    turn_left()
    turn_left()

# 在目前位置放下一個物品
put()

# 牆壁偵測與轉向：
# 當前方有障礙物（front_is_clear 為 False）時，就向左轉，直到前方沒障礙物為止
while not front_is_clear():
    turn_left()

# 轉向後向前移動一格
move()

# 主要邏輯循環：沿著牆壁走（Maze/Wall Follower 演算法）
# 只要目前位置沒有物品（object_here 為 False），就繼續執行
while not object_here():
    
    # 優先判斷右側：如果右邊是空的，就向右轉並前進（確保緊貼右側牆壁）
    if right_is_clear():
        turn_right()
        move()
        
    # 如果右邊有牆但前方是空的，就直接向前走
    elif front_is_clear():
        move()
        
    # 如果右邊和前方都有牆，則原地向左轉（尋找新的出路）
    else:
        turn_left()

# 迴圈結束，代表找到了物品，執行拾取動作
take()

################################################################
# WARNING: Do not change this comment.
# Library Code is below.
################################################################
