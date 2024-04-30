import os
import yaml
import copy
from types import SimpleNamespace

ROOT_PATH = os.path.dirname(os.path.dirname(__file__)) + "/"


class DictObject(SimpleNamespace):
    """A wrapper class that allows both dictionary-style and attribute-style access to items.
    Example:
        cfg = DictObject({"some_key": "some_val"})
        cfg["some_key"]  # -> "some_val" (dictionary-style)
        cfg.some_key  # -> "some_val" (attribute-style)
    """
    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


def load_profiles(path: str, filename: str = "config.yaml") -> dict:
    """Returns a dict with profiles and their configs"""
    profiles = {}
    if path.startswith("/") is False:
        path = os.path.join(ROOT_PATH, path)
    profile_folders = [p for p in os.listdir(path) if os.path.isdir(path + p) is True]
    for profile in profile_folders:
        profile_path = f"{path}/{profile}/"
        filepath = f"{profile_path}/{filename}"
        if os.path.isfile(f"{profile_path}/{filename}") is True:
            profiles[profile] = yaml.safe_load(open(filepath, "r")) or {}
        else:
            profiles[profile] = {}

        # Replace placeholder variables
        if profiles[profile].get("vars") is not None:
            profiles[profile] = replace_placeholders(profiles[profile], placeholders=profiles[profile]["vars"])

        # Add subdirs and files to paths
        files_or_dirs = [p for p in os.listdir(profile_path) if p != f"{filename}"]
        profiles[profile]["paths"] = {}
        for file_or_dir in files_or_dirs:
            profiles[profile]["paths"][file_or_dir] = f"{profile_path}/{file_or_dir}/"

    return profiles


def merge_cfgs(default: dict, new: dict):
    """Merges {new: dict} into {default: dict} recursively.
    NOTE:
    - Only keys that are in new will be updated
    - All default keys that are NOT in new will remain unchanged
    - It is therefore not possible to remove keys from default by omitting them in new
    """
    output = copy.deepcopy(default)
    for key, val in new.items():
        if isinstance(output[key], dict) and isinstance(val, dict):
            output[key] = merge_cfgs(output[key], val)  # Recursive update
        else:
            output[key] = val
    return output


def load_assistants(path: str, vars: dict = None):
    """Returns assistant prompts from a given path"""
    assistants = {}
    filesnames = [name for name in os.listdir(path) if name.endswith(".txt")]
    for filename in filesnames:
        assistant = filename.split(".")[0]
        assistant_path = f"{path}/{filename}"
        with open(assistant_path, "r") as f:
            assistants[assistant] = "".join(f.readlines())
        
    if vars is not None:
        assistants = replace_placeholders(assistants, vars)
    return assistants


def load_tasks(path: str, vars: dict = None):
    """Returns task prompts from a given path.
    The selected task is added to the question, and can be used to clarify how the chatbot should answer.
    """
    tasks = {}
    filesnames = [name for name in os.listdir(path) if name.endswith(".txt")]
    for filename in filesnames:
        task = filename.split(".")[0]
        task_path = f"{path}/{filename}"
        with open(task_path, "r") as f:
            tasks[task] = "".join(f.readlines())

    if vars is not None:
        tasks = replace_placeholders(tasks, vars)
    return tasks


def replace_placeholders(d: dict, placeholders: dict) -> dict:
    """Recursive function that loops through all string values in a dict and replaces all placeholders
    Example:
    - placeholders = {"some_placeholder": "foo"}
    - dict: {"some_key: "some text... ${some_placeholder}... some more text"}
    - result -> {"some_key": "some text... foo... some more text"}
    """
    def _replace(value: str, placeholders: dict) -> str:
        """Helper function to replace placeholders in strings."""
        for ph_key, ph_val in placeholders.items():
            value = value.replace(f"${{{ph_key}}}", ph_val)
        return value

    output = {}
    for key, val in d.items():
        if isinstance(val, dict):
            val = replace_placeholders(val, placeholders)
        elif isinstance(val, list):
            val = [replace_placeholders(item, placeholders) if isinstance(item, (dict, list)) else item for item in val]
            val = [v if not isinstance(v, str) else _replace(v, placeholders) for v in val]
        elif isinstance(val, str):
            val = _replace(val, placeholders)
        output[key] = val
    return output
