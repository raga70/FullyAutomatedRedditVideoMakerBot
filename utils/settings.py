import os
import re
from pathlib import Path
import sys
from typing import Dict, Tuple

import toml
from rich.console import Console

from utils.console import handle_input, print_step, print_substep

console = Console()
config = dict  # autocomplete


def crawl(obj: dict, func=lambda x, y: print(x, y, end="\n"), path=None):
    if path is None:  # path Default argument value is mutable
        path = []
    for key in obj.keys():
        if type(obj[key]) is dict:
            crawl(obj[key], func, path + [key])
            continue
        func(path + [key], obj[key])


def check(value, checks, name):
    def get_check_value(key, default_result):
        return checks[key] if key in checks else default_result

    incorrect = False
    if value == {}:
        incorrect = True
    if not incorrect and "type" in checks:
        try:
            value = eval(checks["type"])(value)
        except:
            incorrect = True

    if (
        not incorrect and "options" in checks and value not in checks["options"]
    ):  # FAILSTATE Value is not one of the options
        incorrect = True
    if (
        not incorrect
        and "regex" in checks
        and (
            (isinstance(value, str) and re.match(checks["regex"], value) is None)
            or not isinstance(value, str)
        )
    ):  # FAILSTATE Value doesn't match regex, or has regex but is not a string.
        incorrect = True

    if (
        not incorrect
        and not hasattr(value, "__iter__")
        and (
            ("nmin" in checks and checks["nmin"] is not None and value < checks["nmin"])
            or ("nmax" in checks and checks["nmax"] is not None and value > checks["nmax"])
        )
    ):
        incorrect = True
    if (
        not incorrect
        and hasattr(value, "__iter__")
        and (
            ("nmin" in checks and checks["nmin"] is not None and len(value) < checks["nmin"])
            or ("nmax" in checks and checks["nmax"] is not None and len(value) > checks["nmax"])
        )
    ):
        incorrect = True

    if incorrect:
        value = handle_input(
            message=(
                (("[blue]Example: " + str(checks["example"]) + "\n") if "example" in checks else "")
                + "[red]"
                + ("Non-optional ", "Optional ")["optional" in checks and checks["optional"] is True]
            )
            + "[#C0CAF5 bold]"
            + str(name)
            + "[#F7768E bold]=",
            extra_info=get_check_value("explanation", ""),
            check_type=eval(get_check_value("type", "False")),
            default=get_check_value("default", NotImplemented),
            match=get_check_value("regex", ""),
            err_message=get_check_value("input_error", "Incorrect input"),
            nmin=get_check_value("nmin", None),
            nmax=get_check_value("nmax", None),
            oob_error=get_check_value(
                "oob_error", "Input out of bounds(Value too high/low/long/short)"
            ),
            options=get_check_value("options", None),
            optional=get_check_value("optional", False),
        )
    return value


def crawl_and_check(obj: dict, path: list, checks: dict = {}, name=""):
    if len(path) == 0:
        return check(obj, checks, name)
    if path[0] not in obj.keys():
        obj[path[0]] = {}
    obj[path[0]] = crawl_and_check(obj[path[0]], path[1:], checks, path[0])
    return obj


def check_vars(path, checks):
    global config
    crawl_and_check(config, path, checks)


def check_toml(template_file, config_file) -> Tuple[bool, Dict]:
    global config
    config = None
    try:
        template = toml.load(template_file)
    except Exception as error:
        console.print(f"[red bold]Encountered error when trying to to load {template_file}: {error}")
        return False
    try:
        config = toml.load(config_file)
    except toml.TomlDecodeError:
        console.print(
            f"""[blue]Couldn't read {config_file}.
Overwrite it?(y/n)"""
        )
        if not input().startswith("y"):
            print("Unable to read config, and not allowed to overwrite it. Giving up.")
            return False
        else:
            try:
                with open(config_file, "w") as f:
                    f.write("")
            except:
                console.print(
                    f"[red bold]Failed to overwrite {config_file}. Giving up.\nSuggestion: check {config_file} permissions for the user."
                )
                return False
    except FileNotFoundError:
        console.print(
            f"""[red bold]Couldn't find {config_file}
Creating it now."""
        )
        try:
            with open(config_file, "x") as f:
                f.write("")
            config = {}
        except:
            console.print(
                f"[red bold]Failed to write to {config_file}. Giving up.\nSuggestion: check the folder's permissions for the user."
            )
            return False

    console.print(
        """\
[blue bold]###############################
#                             #
# Checking TOML configuration #
#                             #
###############################
If you see any prompts, that means that you have unset/incorrectly set variables, please input the correct values.\
"""
    )
    crawl(template, check_vars)
    with open(config_file, "w") as f:
        toml.dump(config, f)
    return config

def check_AllEnvi():
    try:
        print_step(f"Checking Environment Variables...")
        print_substep("Checking REDDIT_CLIENT_ID")
        if check_Envi("REDDIT_CLIENT_ID"):
            console.print("[green]REDDIT_CLIENT_ID is set.")
        else:
            console.print("[red]REDDIT_CLIENT_ID is not set...")
            if set_Envi("REDDIT_CLIENT_ID"):
                console.print("[green]REDDIT_CLIENT_ID is set.")
            else:
                console.print("[red bold]No matching variable in set_Envi.")

        print()
        print_substep("Checking REDDIT_CLIENT_SECRET")
        if check_Envi("REDDIT_CLIENT_SECRET"):
            console.print("[green]REDDIT_CLIENT_SECRET is set.")
        else:
            console.print("[red]REDDIT_CLIENT_SECRET is not set...")
            if set_Envi("REDDIT_CLIENT_SECRET"):
                console.print("[green]REDDIT_CLIENT_SECRET is set.")
            else:
                console.print("[red bold]No matching variable in set_Envi.")

        print()
        print_substep("Checking REDDIT_USER")
        if check_Envi("REDDIT_USER"):
            console.print("[green]REDDIT_USER is set.")
        else:
            console.print("[red]REDDIT_USER is not set...")
            if set_Envi("REDDIT_USER"):
                console.print("[green]REDDIT_USER is set.")
            else:
                console.print("[red bold]No matching variable in set_Envi.")

        print()
        print_substep("Checking REDDIT_PASSWORD")
        if check_Envi("REDDIT_PASSWORD"):
            console.print("[green]REDDIT_PASSWORD is set.")
        else:
            console.print("[red]REDDIT_PASSWORD is not set...")
            if set_Envi("REDDIT_PASSWORD"):
                console.print("[green]REDDIT_PASSWORD is set.")
            else:
                console.print("[red bold]No matching variable in set_Envi.")

        print()
        print_substep("Checking TIKTOK_SESSIONID")
        if check_Envi("TIKTOK_SESSIONID"):
            console.print("[green]TIKTOK_SESSIONID is set.")
        else:
            console.print("[red]TIKTOK_SESSIONID is not set...")
            if set_Envi("TIKTOK_SESSIONID"):
                console.print("[green]TIKTOK_SESSIONID is set.")
            else:
                console.print("[red bold]No matching variable in set_Envi.")

    except:
        print("")
        
def check_Envi(variable):
    try:
        os.environ[variable]
        return True
    except:
        return False
    
def set_Envi(variable):
    match variable:
        case "REDDIT_CLIENT_ID":
            console.print("[green]Please input your Reddit Client ID.")
            console.print("[white]REDDIT_CLIENT_ID:", end="")
            user_input = input("").strip()
            if user_input == "":
                console.print("[red bold]Client ID can not be blank.")
                return False
            try:
                command = f'[Environment]::SetEnvironmentVariable(\\"{variable}\\", \\"{user_input}\\", \\"Machine\\")'
                os.system(f'powershell -Command "{command}"')
                return True
            except:
                Console.print("[red bold]Failed to set Reddit Client ID " + variable + ".")
                return False
            
        case "REDDIT_CLIENT_SECRET":
            console.print("[green]Please input your Reddit Client Secret.")
            console.print("[white]REDDIT_CLIENT_SECRET:", end="")
            user_input = input("").strip()
            if user_input == "":
                console.print("[red bold]Client ID can not be blank.")
                return False
            try:
                command = f'[Environment]::SetEnvironmentVariable(\\"{variable}\\", \\"{user_input}\\", \\"Machine\\")'
                os.system(f'powershell -Command "{command}"')
                return True
            except:
                Console.print("[red bold]Failed to set Reddit Client Secret " + variable + ".")
                return False
            
        case "REDDIT_USER":
            console.print("[green]Please input your Reddit Username.")
            console.print("[white]REDDIT_USER:", end="")
            user_input = input("").strip()
            if user_input == "":
                console.print("[red bold]Client ID can not be blank.")
                return False
            try:
                command = f'[Environment]::SetEnvironmentVariable(\\"{variable}\\", \\"{user_input}\\", \\"Machine\\")'
                os.system(f'powershell -Command "{command}"')
                return True
            except:
                Console.print("[red bold]Failed to set Reddit Username " + variable + ".")
                return False
            
        case "REDDIT_PASSWORD":
            console.print("[green]Please input your Reddit Password.")
            console.print("[white]REDDIT_PASSWORD:", end="")
            user_input = input("").strip()
            if user_input == "":
                console.print("[red bold]Client ID can not be blank.")
                return False
            try:
                command = f'[Environment]::SetEnvironmentVariable(\\"{variable}\\", \\"{user_input}\\", \\"Machine\\")'
                os.system(f'powershell -Command "{command}"')
                return True
            except:
                Console.print("[red bold]Failed to set Reddit Password " + variable + ".")
                return False
            
        case "TIKTOK_SESSIONID":
            console.print("[green]Please input your TikTok SessionID.")
            console.print("[white]TIKTOK_SESSIONID:", end="")
            user_input = input("").strip()
            if user_input == "":
                console.print("[red bold]TikTok SessionID can not be blank.")
                return False
            try:
                command = f'[Environment]::SetEnvironmentVariable(\\"{variable}\\", \\"{user_input}\\", \\"Machine\\")'
                os.system(f'powershell -Command "{command}"')
                return True
            except:
                Console.print("[red bold]Failed to set TikTok SessionID " + variable + ".")
                return False
            

        case _:
            console.print("[red bold]No matching variable in set_Envi.")
            return False

def get_Envi(variable):
    try:
        result = os.environ[f"{variable}"]
        return result
    except:
        error = f"[red bold]Failed to retrieve Environment Variable " + variable + "."
        return error

if __name__ == "__main__":
    directory = Path().absolute()
    check_toml(f"{directory}/utils/.config.template.toml", "config.toml")
