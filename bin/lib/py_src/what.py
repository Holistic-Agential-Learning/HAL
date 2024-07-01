import random

def getMessage():
    names = ["Wes", "Trevor", "Nathan", "Viraj"]
    name = random.choice(names)

    messages = [
        f"Welcome to the Thunder Dome, {name}!",
        f"PO-TA-TOES! BOIL 'EM, MASH 'EM, STICK 'EM IN A STEW!"
        f"{name}, you're cooking right now"
    ]

    return random.choice(messages)

print(getMessage())