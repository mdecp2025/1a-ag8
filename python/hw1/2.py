# 讓機器人向前移動一格
move()
# 自定義函式：透過連續左轉三次來實現「向右轉」
def turn_right():
    turn_left()
    turn_left()
    turn_left()

# 在目前所在的位置放下一個物品（通常作為標記或任務需求）
put()

# --- 初始方向調整 ---
# 如果前方有牆（front_is_clear 為 False），就持續左轉直到找到出口
while not front_is_clear():
    turn_left()

# 確定前方沒牆後，移動進入路徑
move()

# --- 主要導航迴圈：沿著牆壁尋找目標 ---
# 持續執行動作，直到機器人所在位置偵測到物品（object_here）為止
while not object_here():
    
    # 【決策 1】：優先檢查右方空間
    # 如果右邊是空的，為了緊貼右牆，必須先右轉再前進
    if right_is_clear():
        turn_right()
        move()
        
    # 【決策 2】：如果右邊有牆，則檢查前方
    # 如果前方是空的，則穩定直行
    elif front_is_clear():
        move()
        
    # 【決策 3】：如果右邊和前方都被堵死（死胡同或拐角）
    # 則向左轉，嘗試尋找新的前進方向
    else:
        turn_left()

# 迴圈結束（代表 object_here 為真），將該位置的物品撿起來
take()

################################################################
# WARNING: Do not change this comment.
# Library Code is below.
################################################################
