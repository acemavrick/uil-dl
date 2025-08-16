import os
import shutil
import sys
import subprocess
from pathlib import Path
from typing import Optional

def _ensure_icons_from_png(png_path: Path) -> tuple[Optional[Path], Optional[Path]]:
    """Create platform icons from a single PNG.

    Returns a tuple of (ico_path, icns_path). Either may be None if creation failed.
    - .ico is generated cross-platform using Pillow
    - .icns is generated on macOS using the system `iconutil` if available
    """
    ico_out: Optional[Path] = None
    icns_out: Optional[Path] = None

    if not png_path.exists():
        return None, None

    icons_dir = Path("build/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Create .ico (Windows) using Pillow
    try:
        from PIL import Image

        ico_out = icons_dir / "app.ico"
        with Image.open(png_path) as img:
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(ico_out, sizes=sizes)
    except Exception:
        ico_out = None

    # Create .icns (macOS) using iconutil if available
    if sys.platform == "darwin":
        try:
            iconset_dir = icons_dir / "UIL-DL.iconset"
            iconset_dir.mkdir(parents=True, exist_ok=True)

            # Generate the various PNG sizes expected by iconutil
            sizes = [16, 32, 64, 128, 256, 512]
            try:
                from PIL import Image  # type: ignore

                for base in sizes:
                    for scale in (1, 2):
                        size = base * scale
                        name = f"icon_{base}x{base}{'@2x' if scale == 2 else ''}.png"
                        out_path = iconset_dir / name
                        with Image.open(png_path) as img:
                            img.resize((size, size)).save(out_path)
            except Exception:
                # If Pillow not available, try sips to resize
                for base in sizes:
                    for scale in (1, 2):
                        size = base * scale
                        name = f"icon_{base}x{base}{'@2x' if scale == 2 else ''}.png"
                        out_path = iconset_dir / name
                        try:
                            subprocess.run([
                                "sips", "-z", str(size), str(size), str(png_path), "--out", str(out_path)
                            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception:
                            pass

            icns_out = icons_dir / "app.icns"
            subprocess.run([
                "iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_out)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            icns_out = None

    return ico_out, icns_out


def build_with_nuitka():
    """Build UIL-DL with Nuitka for the current OS.

    Notes:
    - Windows builds must be performed on Windows; macOS app bundles on macOS.
    """
    
    version = "1.0.0-beta"
    version_numeric = "1.0.0.1" # for windows; the last number indicates the beta version (1-indexed)
    company = "acemavrick"
    product_name = "UIL-DL"
    file_description = "UIL-DL"
    copyright_text = "Copyright © 2025 acemavrick. Licensed under the MIT License."
    
    try:
        # remove existing build and dist directories if they exist
        if Path("build").exists():
            a = input("remove build directory? (y/n) ")
            if "y" in a.lower():
                shutil.rmtree("build")
        
        if Path("dist").exists():
            a = input("remove dist directory? (y/n) ")
            if "y" in a.lower():
                shutil.rmtree("dist")
    except Exception:
        pass

    try:
        # if on macos
        if sys.platform == "darwin":
            # strip usign xattr and dotfiles
            subprocess.run(["xattr", "-cr", "."], check=True)
            # remove dotfiles
            subprocess.run(["dot_clean", "."], check=True)
    except Exception:
        pass

    # Create icons from PNG so users don't have to maintain multiple assets
    ico_path, icns_path = _ensure_icons_from_png(Path("assets/icon.png"))

    # optional
    use_onefile = False

    # optional
    compile_all_imports = True

    # Resolve parallel jobs to an integer (Nuitka requires a number, not 'auto')
    jobs_value = str(max(1, (os.cpu_count() or 1)))

    # Base Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",

        # Basic options
        "--standalone",  # reliable default; onefile toggled below when requested

        # Output directory
        "--output-dir=dist",

        # clean previous build to avoid stale files
        "--remove-output",

        # include data files for Flask templates/static
        "--include-data-dir=webapp/templates=webapp/templates",
        "--include-data-dir=webapp/static=webapp/static",

        # performance optimizations
        "--plugin-enable=multiprocessing",
        # "--plugin-enable=anti-bloat",
        "--lto=yes",  # link-time optimization
        f"--jobs={jobs_value}",  # parallel C/C++ compilation
        "--assume-yes-for-downloads",
        "--python-flag=no_docstrings",

        "--nofollow-import-to=nuitka_build",  # exclude this build script from the executable
        "--nofollow-import-to=nuitka",  # exclude Nuitka from the executable
        "--nofollow-import-to=sqlalchemy.dialects.mysql,sqlalchemy.dialects.postgresql,sqlalchemy.dialects.oracle",

        
        # "--verbose",
    ]

    if compile_all_imports:
        cmd.append("--follow-imports")
    
    # platform-specific metadata (Windows)
    if sys.platform == "win32":
        cmd.extend([
            f"--windows-company-name={company}",
            f"--windows-product-name={product_name}",
            f"--windows-file-description={file_description}",
            f"--windows-file-version={version_numeric}",
            f"--windows-product-version={version_numeric}",
            # f"--windows-copyright={copyright_text}",
            "--msvc=latest",
            "--windows-console-mode=disable",
        ])
        
        # add icon
        if ico_path and ico_path.exists():
            cmd.append(f"--windows-icon-from-ico={ico_path.as_posix()}")

        # optional onefile for a single .exe
        if use_onefile:
            cmd.append("--onefile")
            # make startup fast by keeping unpack cache between runs
            cmd.append("--onefile-tempdir-spec={CACHE_DIR}/uil-dl")
    
    # macOS specific options
    elif sys.platform == "darwin":
        cmd.extend([
            "--macos-create-app-bundle",
            f"--macos-app-name={product_name}",
            f"--macos-app-version={version}",
            # "--clang",
        ])

        # add icon (.icns required for macOS)
        # Prefer auto-generated icon; fall back to Resources/Icons.icns
        mac_icns = icns_path if icns_path else Path("Resources/Icons.icns")
        if mac_icns.exists():
            cmd.append(f"--macos-app-icon={mac_icns.as_posix()}")

        # macOS onefile can complicate app bundle behavior; keep standalone by default.
        # if use_onefile:
            # cmd.append("--onefile")
            # cmd.append("--onefile-tempdir-spec={CACHE_DIR}/uil-dl")
    
    # Add the main script
    cmd.append("main.py")
    
    print("Building with Nuitka...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        print("running...")
        # stream output to stdout instead of capturing it
        result = subprocess.run(cmd, check=True)

        # On macOS, Nuitka uses the script name for the bundle dir; normalize name and strip xattrs
        if sys.platform == "darwin":
            app_dir = Path("dist/main.app")
            final_app_dir = Path(f"dist/{product_name}.app")
            if app_dir.exists():
                try:
                    subprocess.run(["xattr", "-cr", str(app_dir)], check=False)
                except Exception:
                    pass
                try:
                    if final_app_dir.exists():
                        if final_app_dir.is_dir():
                            # remove existing dir to allow rename
                            subprocess.run(["rm", "-rf", str(final_app_dir)], check=False)
                        else:
                            final_app_dir.unlink()
                    app_dir.rename(final_app_dir)
                except Exception:
                    pass

        print("✅ Build successful!")
        
        # Show where the executable was created
        if sys.platform == "win32":
            print("Executable created: dist/uil-dl.exe")
        elif sys.platform == "darwin":
            print(f"App bundle created: dist/{product_name}.app")
        else:
            print("Executable created: dist/uil-dl")
            
    except subprocess.CalledProcessError as e:
        # On macOS, Nuitka performs ad-hoc signing and may fail due to xattrs; salvage the app if present
        if sys.platform == "darwin":
            app_dir = Path("dist/main.app")
            if app_dir.exists():
                try:
                    subprocess.run(["xattr", "-cr", str(app_dir)], check=False)
                except Exception:
                    pass
                final_app_dir = Path(f"dist/{product_name}.app")
                try:
                    if final_app_dir.exists():
                        subprocess.run(["rm", "-rf", str(final_app_dir)], check=False)
                    app_dir.rename(final_app_dir)
                except Exception:
                    pass
                print("⚠️ Nuitka reported a signing error, but the app bundle was created successfully.")
                print(f"App bundle available at: dist/{product_name}.app")
                return True
        print("❌ Build failed!")
        print(f"Error: {e.stderr}")
        return False
    
    return True

if __name__ == "__main__":
    success = build_with_nuitka()
    if success:
        print("build successful! app is in dist/")
        if sys.platform == "darwin":
            # chmod?
            # check if uil-dl exists in the app bundle
            uil_dl_path = Path("dist/uil-dl.app/Contents/MacOS/main")
            if uil_dl_path.exists():
                print("Making executable...")
                subprocess.run(["chmod", "+x", str(uil_dl_path)], check=True)
                print("Executable permissions set")
            else:
                print("uil-dl not found in app bundle")
            pass
    else:
        print("build failed! app is not in dist/")
    sys.exit(0 if success else 1)
