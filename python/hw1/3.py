def turn_right():
    turn_left()
    turn_left()
    turn_left()


put()


while not front_is_clear():
    turn_left()
move()

while not object_here():

    if right_is_clear():
        turn_right()
        move()

    elif front_is_clear():
        move()

    else:
        turn_left()

take()
################################################################
# WARNING: Do not change this comment.
# Library Code is below.
################################################################
