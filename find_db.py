import os

print("Searching for .db files...")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            print(f"FOUND: {os.path.join(root, file)}")
            print(f"ABSOLUTE: {os.path.abspath(os.path.join(root, file))}")
