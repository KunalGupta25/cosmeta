import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

def main():
    # Connect to the database using environment variables
    conn_string = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    
    # List all users
    print("Current users in the database:")
    cur.execute("SELECT id, username, discord_id, role FROM \"user\"")
    users = cur.fetchall()
    
    if not users:
        print("No users found in the database.")
        conn.close()
        return
    
    print("ID | Username | Discord ID | Role")
    print("-" * 50)
    for user in users:
        role_name = {
            1: "User",
            2: "Supporter",
            3: "Author",
            4: "Admin"
        }.get(user[3], "Unknown")
        
        print(f"{user[0]} | {user[1]} | {user[2]} | {role_name} ({user[3]})")
    
    # Ask which user to promote
    user_id = input("\nEnter the ID of the user you want to promote: ")
    
    # Ask for the new role
    print("\nAvailable roles:")
    print("1 - Regular User")
    print("2 - Supporter")
    print("3 - Author")
    print("4 - Admin")
    new_role = input("Enter the new role number: ")
    
    try:
        user_id = int(user_id)
        new_role = int(new_role)
        
        if new_role not in [1, 2, 3, 4]:
            print("Invalid role number.")
            conn.close()
            return
        
        # Update the user's role
        cur.execute(
            sql.SQL("UPDATE \"user\" SET role = %s WHERE id = %s"),
            [new_role, user_id]
        )
        conn.commit()
        
        print(f"User with ID {user_id} has been updated to role {new_role}.")
        
    except ValueError:
        print("Invalid input. Please enter numeric values.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()