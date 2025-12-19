def turn_right():
    turn_left()
    turn_left()
    turn_left()

# 1. 在起點放下一顆球（或標記），當作終點線
put()

# 2. 先跨出第一步，避免原地偵測到標記就結束
if front_is_clear():
    move()
else:
    turn_left()
    if front_is_clear():
        move()

# 3. 沿路走，直到再次遇見剛才放下的標記
while not object_here():
    if right_is_clear():
        # 優先沿著右邊轉彎
        turn_right()
        move()
    elif front_is_clear():
        # 前方沒障礙就直走
        move()
    else:
        # 撞牆就左轉
        turn_left()

# 4. 回到起點後，把東西撿起來，完美結束
take()
