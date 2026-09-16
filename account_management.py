import os
import pwd
import subprocess
import argparse
import shutil
import logging

logging.basicConfig(
    filename="/var/log/account_management.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def check_account_status(username):
    result = subprocess.run(
        ["passwd", "-S", username],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Failed to get account status")
        print(result.stderr)
        return "UNKNOWN"

    status = result.stdout.split()[1]

    if status == "LK":
        return "LOCKED"
    elif status == "PS":
        return "UNLOCKED"
    else:
        return status

def unlock_account(username):
    result = subprocess.run(
        ["passwd", "-u", username],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(result.stdout.strip())
        return True
    else:
        print("Unlock failed:")
        print(result.stderr.strip())
        return False

def reset_password(username):
    result = subprocess.run(
        ["passwd", username]
    )

    if result.returncode == 0:
        return True
    else:
        print("Password reset failed")
        return False

def reset_failed_logins(username):
    faillock_path = shutil.which("faillock")

    if faillock_path:
        result = subprocess.run(
            [faillock_path, "--user", username, "--reset"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("Failed-login records reset successfully")
            return True
        else:
            print("Failed-login reset failed:")
            print(result.stderr.strip())
            return False

    pam_tally_path = shutil.which("pam_tally2")

    if pam_tally_path:
        result = subprocess.run(
            [pam_tally_path, "--user", username, "--reset"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("Failed-login records reset successfully")
            return True
        else:
            print("Failed-login reset failed:")
            print(result.stderr.strip())
            return False

    print("Neither faillock nor pam_tally2 is available")
    return False

parser = argparse.ArgumentParser()

parser.add_argument(
    "--user",
    required=True,
    help="Username to manage"
)

parser.add_argument(
    "--action",
    required=True,
    choices=["unlock", "reset", "unlock-reset"],
    help="Action to perform"
)

args = parser.parse_args()

username = args.user

print("Username:", username)
print("Action:", args.action)

logging.info("User=%s Action=%s", username, args.action)

if os.geteuid() != 0:
    print("Please run this script as root")
    exit()

print("Running as root")


try:
    pwd.getpwnam(username)
    print("User exists:", username)

    status = check_account_status(username)

    if status == "LOCKED":
        print("Account is LOCKED")
    elif status == "UNLOCKED":
        print("Account is UNLOCKED")
    else:
        print("Account status:", status)

except KeyError:
    print("User does not exist:", username)
    exit(1)


if args.action == "unlock":
    if status == "LOCKED":
        if unlock_account(username):
            print("Account unlock successful")
            logging.info("User=%s Action=unlock Result=SUCCESS", username)

            reset_failed_logins(username)

            new_status = check_account_status(username)

            if new_status == "UNLOCKED":
                print("Verification: Account is UNLOCKED")
            else:
                print("Verification failed: Account is", new_status)
        else:
            print("Account unlock failed")
            logging.error("User=%s Action=unlock Result=FAILED", username)
    else:
        print("Account is already unlocked")


elif args.action == "reset":
    print("Starting password reset...")

    if reset_password(username):
        print("Password reset successful")
        logging.info("User=%s Action=reset Result=SUCCESS", username)

        new_status = check_account_status(username)

        if new_status == "UNLOCKED":
            print("Verification: Account is UNLOCKED")
        else:
            print("Verification: Account status is", new_status)
    else:
        print("Password reset failed")
        logging.error("User=%s Action=reset Result=FAILED", username)

elif args.action == "unlock-reset":
    print("Starting unlock + password reset...")

    if status == "LOCKED":
        if unlock_account(username):
            print("Account unlock successful")
        else:
            print("Account unlock failed")
            exit()

    if reset_password(username):
        print("Password reset successful")

        new_status = check_account_status(username)

        if new_status == "UNLOCKED":
            print("Verification: Account is UNLOCKED")
        else:
            print("Verification failed: Account status is", new_status)
    else:
        print("Password reset failed")
