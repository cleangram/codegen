def snake(name: str):
    return "".join([w if w.islower() else "_" + w.lower() for w in name]).lstrip('_')
