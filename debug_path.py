import os

print(f"Current CWD: {os.getcwd()}")
print("Files in current directory:")
for f in os.listdir('.'):
    print(f" - {f}")

db_path = 'plex_manager.db'
print(f"Checking for {db_path}: {os.path.exists(db_path)}")

abs_path = os.path.abspath(db_path)
print(f"Absolute path: {abs_path}")
print(f"Exists at absolute path: {os.path.exists(abs_path)}")
