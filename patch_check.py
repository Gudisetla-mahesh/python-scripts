import subprocess

result = subprocess.run(
    ["uname", "-r"],
    capture_output=True,
    text=True
)

print("Kernel:", result.stdout.strip())
