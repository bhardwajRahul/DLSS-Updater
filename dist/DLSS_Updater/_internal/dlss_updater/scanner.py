import os
from pathlib import Path
from .config import LauncherPathName, config_manager
from .whitelist import is_whitelisted
from .constants import DLL_GROUPS
import asyncio
from dlss_updater.logger import setup_logger
import sys

logger = setup_logger()


def get_steam_install_path():
    try:
        if config_manager.check_path_value(LauncherPathName.STEAM):
            path = config_manager.check_path_value(LauncherPathName.STEAM)
            # Remove \steamapps\common if it exists
            path = path.replace("\\steamapps\\common", "")
            logger.debug(f"Using configured Steam path: {path}")
            return path

        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"
        )
        value, _ = winreg.QueryValueEx(key, "InstallPath")
        config_manager.update_launcher_path(LauncherPathName.STEAM, str(value))
        return value
    except (FileNotFoundError, ImportError) as e:
        logger.debug(f"Could not find Steam install path: {e}")
        return None


def get_steam_libraries(steam_path):
    logger.debug(f"Looking for Steam libraries in: {steam_path}")
    library_folders_path = Path(steam_path) / "steamapps" / "libraryfolders.vdf"
    logger.debug(f"Checking libraryfolders.vdf at: {library_folders_path}")

    if not library_folders_path.exists():
        default_path = Path(steam_path) / "steamapps" / "common"
        logger.debug(
            f"libraryfolders.vdf not found, using default path: {default_path}"
        )
        return [default_path]

    libraries = []
    with library_folders_path.open("r", encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            if "path" in line:
                path = line.split('"')[3]
                library_path = Path(path) / "steamapps" / "common"
                logger.debug(f"Found Steam library: {library_path}")
                libraries.append(library_path)

    logger.debug(f"Found total Steam libraries: {len(libraries)}")
    for lib in libraries:
        logger.debug(f"Steam library path: {lib}")
    return libraries


async def find_dlls(library_paths, launcher_name, dll_names):
    """Find DLLs from a filtered list of DLL names"""
    dll_paths = []
    logger.debug(f"Searching for DLLs in {launcher_name}")

    for library_path in library_paths:
        logger.debug(f"Scanning directory: {library_path}")
        try:
            for root, _, files in os.walk(library_path):
                for dll_name in dll_names:
                    if dll_name.lower() in [f.lower() for f in files]:
                        dll_path = os.path.join(root, dll_name)
                        logger.debug(f"Found DLL: {dll_path}")
                        if not await is_whitelisted(dll_path):
                            logger.info(
                                f"Found non-whitelisted DLL in {launcher_name}: {dll_path}"
                            )
                            dll_paths.append(dll_path)
                        else:
                            logger.info(
                                f"Skipped whitelisted game in {launcher_name}: {dll_path}"
                            )
                await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error scanning {library_path}: {e}")

    logger.debug(f"Found {len(dll_paths)} DLLs in {launcher_name}")
    return dll_paths


def get_user_input(prompt):
    user_input = input(prompt).strip()
    return None if user_input.lower() in ["n/a", ""] else user_input


async def get_ea_games():
    ea_path = config_manager.check_path_value(LauncherPathName.EA)
    if not ea_path or ea_path == "":
        return []
    ea_games_path = Path(ea_path)
    return [ea_games_path] if ea_games_path.exists() else []


def get_ubisoft_install_path():
    try:
        if config_manager.check_path_value(LauncherPathName.UBISOFT):
            return config_manager.check_path_value(LauncherPathName.UBISOFT)
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Ubisoft\Launcher"
        )
        value, _ = winreg.QueryValueEx(key, "InstallDir")
        config_manager.update_launcher_path(LauncherPathName.UBISOFT, str(value))
        return value
    except (FileNotFoundError, ImportError):
        return None


async def get_ubisoft_games(ubisoft_path):
    ubisoft_games_path = Path(ubisoft_path) / "games"
    if not ubisoft_games_path.exists():
        return []
    return [ubisoft_games_path]


async def get_epic_games():
    epic_path = config_manager.check_path_value(LauncherPathName.EPIC)
    if not epic_path or epic_path == "":
        return []
    epic_games_path = Path(epic_path)
    return [epic_games_path] if epic_games_path.exists() else []


async def get_gog_games():
    gog_path = config_manager.check_path_value(LauncherPathName.GOG)
    if not gog_path or gog_path == "":
        return []
    gog_games_path = Path(gog_path)
    return [gog_games_path] if gog_games_path.exists() else []


async def get_battlenet_games():
    battlenet_path = config_manager.check_path_value(LauncherPathName.BATTLENET)
    if not battlenet_path or battlenet_path == "":
        return []
    battlenet_games_path = Path(battlenet_path)
    return [battlenet_games_path] if battlenet_games_path.exists() else []


async def get_xbox_games():
    xbox_path = config_manager.check_path_value(LauncherPathName.XBOX)
    if not xbox_path or xbox_path == "":
        return []
    xbox_games_path = Path(xbox_path)
    return [xbox_games_path] if xbox_games_path.exists() else []


async def get_custom_folder(folder_num):
    custom_path = config_manager.check_path_value(
        getattr(LauncherPathName, f"CUSTOM{folder_num}")
    )
    if not custom_path or custom_path == "":
        return []
    custom_path = Path(custom_path)
    return [custom_path] if custom_path.exists() else []


async def find_all_dlls():
    logger.info("Starting find_all_dlls function")
    all_dll_paths = {
        "Steam": [],
        "EA Launcher": [],
        "Ubisoft Launcher": [],
        "Epic Games Launcher": [],
        "GOG Launcher": [],
        "Battle.net Launcher": [],
        "Xbox Launcher": [],
        "Custom Folder 1": [],
        "Custom Folder 2": [],
        "Custom Folder 3": [],
        "Custom Folder 4": [],
    }

    # Get user preferences
    update_dlss = config_manager.get_update_preference("DLSS")
    update_ds = config_manager.get_update_preference("DirectStorage")
    update_xess = config_manager.get_update_preference("XeSS")

    # Build list of DLLs to search for based on preferences
    dll_names = []
    if update_dlss:
        dll_names.extend(DLL_GROUPS["DLSS"])
    if update_ds:
        dll_names.extend(DLL_GROUPS["DirectStorage"])
    if update_xess and DLL_GROUPS["XeSS"]:  # Only add if there are XeSS DLLs defined
        dll_names.extend(DLL_GROUPS["XeSS"])

    # Skip if no technologies selected
    if not dll_names:
        logger.info("No technologies selected for update, skipping scan")
        return all_dll_paths

    steam_path = get_steam_install_path()
    if steam_path:
        steam_libraries = get_steam_libraries(steam_path)
        all_dll_paths["Steam"] = await find_dlls(steam_libraries, "Steam", dll_names)

    ea_games = await get_ea_games()
    if ea_games:
        ea_dlls = await find_dlls(ea_games, "EA Launcher", dll_names)
        all_dll_paths["EA Launcher"].extend(ea_dlls)

    ubisoft_path = get_ubisoft_install_path()
    if ubisoft_path:
        ubisoft_games = await get_ubisoft_games(ubisoft_path)
        all_dll_paths["Ubisoft Launcher"] = await find_dlls(
            ubisoft_games, "Ubisoft Launcher", dll_names
        )

    epic_games = await get_epic_games()
    if epic_games:
        all_dll_paths["Epic Games Launcher"] = await find_dlls(
            epic_games, "Epic Games Launcher", dll_names
        )

    gog_games = await get_gog_games()
    if gog_games:
        all_dll_paths["GOG Launcher"] = await find_dlls(
            gog_games, "GOG Launcher", dll_names
        )

    battlenet_games = await get_battlenet_games()
    if battlenet_games:
        all_dll_paths["Battle.net Launcher"] = await find_dlls(
            battlenet_games, "Battle.net Launcher", dll_names
        )

    xbox_games = await get_xbox_games()
    if xbox_games:
        all_dll_paths["Xbox Launcher"] = await find_dlls(
            xbox_games, "Xbox Launcher", dll_names
        )

    # Add custom folders
    for i in range(1, 5):
        custom_folder = await get_custom_folder(i)
        if custom_folder:
            all_dll_paths[f"Custom Folder {i}"] = await find_dlls(
                custom_folder, f"Custom Folder {i}", dll_names
            )

    # Remove duplicates
    unique_dlls = set()
    for launcher in all_dll_paths:
        all_dll_paths[launcher] = [
            dll
            for dll in all_dll_paths[launcher]
            if str(dll) not in unique_dlls and not unique_dlls.add(str(dll))
        ]

    return all_dll_paths


def find_all_dlls_sync():
    """Synchronous wrapper for find_all_dlls to use in non-async contexts"""
    import asyncio

    try:
        # Use a new event loop to avoid conflicts with Qt
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(find_all_dlls())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in find_all_dlls_sync: {e}")
        import traceback

        logger.error(traceback.format_exc())
        # Return an empty dict as fallback
        return {
            "Steam": [],
            "EA Launcher": [],
            "Ubisoft Launcher": [],
            "Epic Games Launcher": [],
            "GOG Launcher": [],
            "Battle.net Launcher": [],
            "Xbox Launcher": [],
            "Custom Folder 1": [],
            "Custom Folder 2": [],
            "Custom Folder 3": [],
            "Custom Folder 4": [],
        }
