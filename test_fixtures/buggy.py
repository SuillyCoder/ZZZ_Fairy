import os  # Import os module
def divide(a, b):  # Define function divide that takes a and b
    if b == 0:
        raise ValueError("Cannot divide by 0")
    return a / b  # Return result of dividing a by b

def get_user(data, id): # function definition
    for u in data: # iterate over each user in data
        if u["id"] == id: # check if user id matches given id
            return u # return the matching user
        
def save_file(path, content): # function definition
    try:
        f = open(path, "w") # open file for writing
        f.write(content) # write content to file
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
    except Exception as e:
        print(f"An error occured: {e}")

def process_list(items): # function to process list
    result = [] # initialize result list
    for i in range(len(items)): # loop over indices
        result.append(items[i] * 2) # append doubled element
    return result # return processed list