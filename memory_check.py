import subprocess

result = subprocess.run(
    ["free", "-h"],
    capture_output=True,
    text=True
)

print(result.stdout)
