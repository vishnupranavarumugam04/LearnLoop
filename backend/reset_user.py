from database import delete_user, get_user_by_username, init_db

init_db()
username = "vpranav4126@gmail.com"
user = get_user_by_username(username)

if user:
    print(f"Found user {username} with ID {user['id']}. Deleting...")
    delete_user(user['id'])
    print("User deleted.")
else:
    print(f"User {username} not found.")
