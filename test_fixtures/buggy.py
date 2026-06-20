import os

def divide(a, b):
    return a / b

def get_user(data, id):
    for u in data:
        if u["id"] == id:
            return u

def save_file(path, content):
    f = open(path, "w")
    f.write(content)

def process_list(items):
    result = []
    for i in range(len(items)):
        result.append(items[i] * 2)
    return result