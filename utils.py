def get_discord_token():
    try:
        with open("discord.key") as f:
            lines = f.readlines()
        for line in lines:
            splitted = line.split(" ")
            if splitted[0] == "BOT_TOKEN":
                return splitted[1]
        return None
    except:
        return None

def second_to_minute(sec):
    return "{0[0]}m {0[1]}s".format(divmod(sec, 60))
