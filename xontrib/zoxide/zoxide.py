import subprocess
import os
import sys
import hashlib
from xonsh.built_ins import XSH
from pathlib import Path

_cache_name = "zoxide_init_cache.py"


def get_cache_dir():
    """
    Determine the cache directory, preferring XDG_CACHE_HOME.
    Default to ~/.cache or /tmp if necessary.
    """
    cache_base_dir = os.getenv("XDG_CACHE_HOME")
    if not cache_base_dir:
        # Fallback to ~/.cache if XDG_CACHE_HOME is not set
        home_dir = Path.home()
        cache_base_dir = str(home_dir.joinpath(".cache"))
    if not os.access(cache_base_dir, os.W_OK | os.X_OK):
        cache_base_dir = "/tmp"
    cache_dir = os.path.join(cache_base_dir, "xontrib-zoxide-cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _cache_zoxide_init(zoxide_init, z_cache_path):
    if not (Path(z_cache_path).name == _cache_name):
        print(
            f"xontrib-zoxide: error: cache file should be '{_cache_name}', got {Path(z_cache_path).name}"
        )
        return
    print(
        "xontrib-zoxide: creating a zoxide init cache file to speed up subsequent loads"
    )
    with open(z_cache_path, "wb") as f:
        f.write(zoxide_init.encode("utf-8"))


def _initZoxide():
    script_path = get_cache_dir()  # Use updated cache directory selection
    z_cache_path = os.path.join(script_path, _cache_name)

    # Capture zoxide init output as text
    zoxide_init_proc = subprocess.run(
        ["zoxide", "init", "xonsh"], capture_output=True, text=True
    )
    zoxide_init = zoxide_init_proc.stdout
    zoxide_init_err = zoxide_init_proc.stderr

    if zoxide_init_err:
        print("xontrib-zoxide: error: 'zoxide init xonsh' failed with:")
        print(zoxide_init_err)
        return

    if not Path(z_cache_path).exists():  # Cache & Load (slow)
        _cache_zoxide_init(zoxide_init, z_cache_path)
        exec(zoxide_init, XSH.ctx)
    else:  # Hash & Load
        hash_init = hashlib.md5(zoxide_init.encode("utf-8")).hexdigest()
        hash_cache = hashlib.md5(open(z_cache_path, "rb").read()).hexdigest()

        if hash_init == hash_cache:  # Load fast from cache
            sys.path.append(script_path)  # Ensure cache dir is in the PATH
            import zoxide_init_cache
        else:  # Cache & Load (slow)
            _cache_zoxide_init(zoxide_init, z_cache_path)
            exec(zoxide_init, XSH.ctx)
    _initZoxide()
