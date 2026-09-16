import subprocess

result = subprocess.run(
    ["top", "-b", "-n", "1"],
    capture_output=True,
    text=True
)

print(result.stdout)
