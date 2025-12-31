import os

target_key = "GOOGLE_API_KEY"
new_value = "AIzaSyCfRmhsyhRhFUMa-uC_WoRR72YeoikZJOg"
env_path = ".env"

if not os.path.exists(env_path):
    print("Creating new .env")
    lines = []
else:
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

new_lines = []
found = False
for line in lines:
    if line.strip().startswith(target_key):
        new_lines.append(f"{target_key}={new_value}\n")
        found = True
    else:
        new_lines.append(line)

if not found:
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines.append("\n")
    new_lines.append(f"{target_key}={new_value}\n")

with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Updated {target_key}")
