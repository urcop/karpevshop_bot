async def place_in_queue(_users, user_id):
    count = 0
    result = []
    while count < len(_users):
        if _users[count][0] == user_id:
            result.append((count, _users[count][1]))
            count += 1
        else:
            count += 1
    return result