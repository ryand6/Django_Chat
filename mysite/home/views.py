from better_profanity import profanity


def sanitise_text(text):
    if profanity.contains_profanity(text):
        return profanity.censor(text)
    else:
        return text