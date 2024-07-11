import random
from shutil import which
import subprocess


cows = ["apt", "bud-frogs", "bunny", "calvin", "cheese", "cock", "cower", "daemon", "default", "dragon",
        "dragon-and-cow", "duck", "elephant", "elephant-in-snake", "eyes", "flaming-sheep", "fox",
        "ghostbusters", "gnu", "hellokitty", "kangaroo", "koala", "kosh", "luke-koala",
        "mech-and-cow", "milk", "moofasa", "moose", "pony", "pony-smaller", "ren", "sheep", "skeleton",
        "snowman", "stegosaurus", "stimpy", "suse", "three-eyes", "turkey", "turtle", "tux", "unipony",
        "unipony-smaller", "vader", "vader-koala", "www"]


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

def fortune():
    subprocess.call("fortune | cowsay")

def fortune_with_cow():
    cow = random.choice(cows)
    fortune = subprocess.Popen(("fortune"), stdout=subprocess.PIPE)
    subprocess.run(["cowsay", "-f", cow], stdin=fortune.stdout)

def cow_with_message(msg):
    subprocess.run(["cowsay", "-f", random.choice(cows), msg])

def shenanigans():
    msg = getMessage()

    print("--------------")
    if which("fortune"):
        fort = random.choice([True, False])
        if which("cowsay"):
            if fort:
                fortune_with_cow()
            else:
                cow_with_message(msg)
        else:
            if fort:
                fortune()
            else:
                print(msg)
    else:
        if which("cowsay"):
            cow_with_message(msg)
        else:
            print(msg)
    print("--------------")
        


if __name__=="main":    
    print(getMessage())