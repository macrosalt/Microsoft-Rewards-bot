import json
from argparse import ArgumentParser
from requests import get, exceptions
import sys
import os
from shutil import rmtree, copy
from subprocess import call
from typing import Union

# get args
parser = ArgumentParser(description="Microsoft Rewards Farmer Updater, use '--update'.")
parser.add_argument('--update', action='store_true', help='Update.', required=False)
parser.add_argument('--debug', action='store_true', help="Debug mode.", required=False)
parser.add_argument('-y', action='store_true', help="Will automatically say yes.", required=False)
args = parser.parse_args()

# important settings
temp_folder = "temp//"
dir_path = os.path.join(__file__.replace(os.path.basename(__file__), ""))
ignore_files = ["LICENSE", ".gitignore", ".deepsource.toml", "accounts.json.sample", "update.py",
                ".github", ".github/workflows", ".github/workflows/update-version-file.yml"]
repository = {
    "name": "farshadz1997",
    "repo": "Microsoft-Rewards-bot",
    "branch": "master"
}


def download(url, action, json_decode=True) -> str:
    """return GET of url. action is only for exit() not anything important"""
    # Attempt to downloaded_file
    try:
        downloaded_file = get(url)
    except exceptions.RequestException as exc:
        print(f"[UPDATER] Unable to {action}. ")
        sys.exit(exc)

    # Error handling
    if downloaded_file.status_code != 200:
        sys.exit(f"[UPDATER] Unable to {action} (Status: {downloaded_file.status_code})")

    # if need be - decode json
    if json_decode:
        try:
            response = json.loads(downloaded_file.text)
            return response
        except json.JSONDecodeError:
            sys.exit(f"[UPDATER] Unable to {action} (JSONDecodeError)")
    return downloaded_file.text


def validate(repo, specific_file="", api=False) -> str:
    """
    example.com (repo) + directory = example.com/directory if API then
    https://api.github.com/repos/USER/REPO/git/trees/BRANCH?recursive=1
    """
    if api:
        return fr'https://api.github.com/repos/{repo["name"]}/{repo["repo"]}/git/trees/{repo["branch"]}?recursive=1'
    repo_link = fr'https://raw.githubusercontent.com/{repo["name"]}/{repo["repo"]}/{repo["branch"]}'
    return f'{repo_link}{specific_file}' if repo_link[-1] == "/" else f'{repo_link}/{specific_file}'


def api_to_list(data) -> list:
    """GitHub API file paths to dictionary"""
    stripped, files = [], []

    # strip unnecessary data
    for file_path in data["tree"]:
        if file_path['path'] not in ignore_files:
            stripped.append(file_path)

    # convert useful file paths to list
    for _, value in enumerate(stripped):
        files.append(value['path'])

    return sorted(files)


def create_dir(dir_name: str) -> str:
    """Create directory"""
    path = dir_path + dir_name

    # check if folder exists, if so deleted L
    if os.path.isdir(path):
        delete_dir(dir_name)

    os.mkdir(path)
    print(f"Directory created: {path}")

    return path


def delete_dir(dir_name: str) -> None:
    """Delete directory"""
    path = dir_path + dir_name
    rmtree(path)
    print(f"Directory deleted: {path}")


def user_permissions() -> Union[str, bool]:
    """Ask user if Yes or No"""
    if not args.y:
        rights = input("Automatic installer will download and update your program files. If you have the appropriate file, and download rights please continue by entering 'Y'. [y/N] ")
        if rights.lower() not in ['y', 'yes']:
            print("Exiting script...")
            sys.exit(1)
        return rights
    return args.y


def debug(statement) -> None:
    """send debug info if --debug"""
    if args.debug:
        print(statement)


def download_online_files(path) -> list:
    """download files from the internet superhighway"""
    files = []
    for file in online_files:
        files.append(file)
        print(f"Attempting to download {file}.")
        try:
            downloaded_text = download(validate(repository, file), f"downloading {file}", False)
            with open(fr'{path}/{file}', "wb") as temp_file:
                temp_file.write(downloaded_text.encode(sys.stdout.encoding, errors='replace'))
        except Exception as exc:  # skipcq
            debug(exc)
            print(f"Failed to download {file}.\nError occurred whilst downloading files.\n"
                  "Before reporting this as an issue on github please run --debug and report the result.")
            delete_dir("temp")
            sys.exit(1)
        print(f"Successfully downloaded {file}.")
    return files


def delete_files():
    """Delete files"""
    for file in online_files:
        try:
            os.remove(dir_path + file)
        except FileNotFoundError:
            continue


def move_temp_files():
    """move files from /temp to working directory"""
    for file in online_files:
        copy(dir_path + temp_folder + file, dir_path)


def pip_install():
    """runs: pip install -r requirements.txt"""
    try:
        call("pip install -r requirements.txt", shell=True)
    except Exception as exc:  # skipcq
        debug(exc)
        print("Pip was unable to automatically update your modules."
              "\nPlease manually update your modules by using: 'pip install -r requirements.txt'.")
        return
    print("Updated pip modules.")


if __name__ == '__main__':
    # Force users to use --update
    if not args.update:
        print(f"Use 'py {os.path.basename(__file__)} --update'")
        sys.exit(0)

    # Check latest version
    print("Checking latest version online.")
    check_version = download(validate(repository, "version.json"), "check latest version")
    print(f"Found a version online! Attempting to update to {check_version['version']}.")
    debug(check_version)

    # Get online files
    print("Finding list of online files.")
    online_files = api_to_list(download(validate(repository, api=True), "check file directory"))
    print("Found list of online files.")
    debug(online_files)

    # Check for user permissions
    user_perm = user_permissions()
    debug(user_perm)

    # Create directory
    temp_path = create_dir("temp")

    # Download all files to local device
    print("Attempting to download files.")
    download_online_files(temp_path)
    print("Successfully downloaded files")

    # Delete local files
    print("Deleting local files.")
    delete_files()
    print("Deleted local files.")

    # Move files in temp to main directory
    print("Moving downloaded files to local directory.")
    move_temp_files()
    print("Moved downloaded files to local directory.")

    # Delete downloaded/temp folder
    print("Deleting temp folder.")
    delete_dir("temp")
    print("Deleted temp folder.")

    # Updating pip
    print("Updating pip modules.")
    pip_install()

    # Finishing message
    print(f"Successfully updated your script to {check_version['version']}.")
