import random

def getMessage():
    names = ["Wes", "Trevor", "Nathan", "Viraj"]
    name = random.choice(names)

    messages = [
        f"Welcome to the Thunder Dome, {name}!",
        f"PO-TA-TOES! BOIL 'EM, MASH 'EM, STICK 'EM IN A STEW!",
        f"{name}, you're cooking right now",
        f"I think it's lunch time, {name}",
        f"Drink more water, {name}",
        f"You're giving off top-right energy, {name}",
        f"You're being a bottom-left, {name}",
        f"Welcome to the experiment, {name}"
    ]

    return random.choice(messages)

if __name__=="main":    
    print(getMessage())