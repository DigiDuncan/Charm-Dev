import random

TRICKY = 1

CHANCES = 1000
fun_choices = [TRICKY]
boring_choices = range(CHANCES-len(fun_choices))

state = random.choice([*fun_choices, *boring_choices])
