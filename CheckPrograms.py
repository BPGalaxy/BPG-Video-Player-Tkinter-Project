import winreg

def _read_key(root, path):
    programs = []
    try:
        with winreg.OpenKey(root, path) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey_path = f"{path}\\{subkey_name}"
                try:
                    with winreg.OpenKey(root, subkey_path) as subkey:
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        programs.append(display_name)
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
    except OSError:
        pass
    return programs

def list_installed_programs():
    all_programs = set()

    all_programs.update(_read_key(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"))

    all_programs.update(_read_key(
        winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"))

    all_programs.update(_read_key(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"))

    return sorted(all_programs)

if __name__ == "__main__":
    for prog in list_installed_programs():
        print(prog)
