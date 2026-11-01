
Import("env")
import os
import zipfile
import shutil
from pathlib import Path


# Get the version number from the build environment.
firmware_version = os.environ.get("VERSION", "")
if firmware_version == "":
    firmware_version = "0.0.1"

firmware_version = firmware_version.lstrip("v").strip(".")


# Get configuration from the build environment.
community_project = env.GetProjectOption(
    "custom_community_project", ""
)

custom_source_folder = env.GetProjectOption(
    "custom_source_folder", ""
)

zip_filename = env.GetProjectOption(
    "custom_zip_filename", ""
)

platform = env.BoardConfig().get("platform", {})


def copy_fw_files(source, target, env):
    fw_file_name = str(target[0])

    # Define source and staging paths.
    source_community_path = (
        Path(custom_source_folder) / "Community"
    )

    build_community_path = (
        Path("./_build") / custom_source_folder / "Community"
    )

    # Refresh Community files on EVERY build.
    # Existing compiled firmware files are preserved unless
    # a source file has the same relative path.
    build_community_path.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copytree(
        str(source_community_path),
        str(build_community_path),
        dirs_exist_ok=True
    )

    # Update firmware version in staged board JSON files.
    replacements = {
        "0.0.1": firmware_version
    }

    build_path_json = build_community_path / "boards"

    if build_path_json.exists():
        for file_path in build_path_json.rglob("*.json"):
            replace_in_file(file_path, replacements)

    print("Community files refreshed in _build")

    # Convert firmware to UF2 for Raspberry Pi targets.
    if platform == "raspberrypi":
        fw_file_name = fw_file_name[:-3] + "uf2"

    # Copy compiled firmware into the staged Community folder.
    firmware_path = build_community_path / "firmware"
    firmware_path.mkdir(parents=True, exist_ok=True)

    print("Copying firmware:", fw_file_name)
    shutil.copy2(fw_file_name, str(firmware_path))

    # Create the distribution ZIP.
    zip_file_path = (
        Path("./_dist") /
        f"{zip_filename}_{firmware_version}.zip"
    )

    print("Creating ZIP:", zip_file_path)

    createZIP(
        str(build_community_path),
        str(zip_file_path),
        community_project
    )


def createZIP(original_folder_path, zip_file_path, new_folder_name):
    # Ensure the distribution directory exists.
    Path(zip_file_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(
        zip_file_path, "w", zipfile.ZIP_DEFLATED
    ) as zipf:
        for root, dirs, files in os.walk(original_folder_path):
            for file in files:
                source_path = Path(root) / file

                # Preserve the expected top-level folder in the ZIP.
                relative_path = source_path.relative_to(
                    original_folder_path
                )

                archive_path = (
                    Path(new_folder_name) / relative_path
                )

                zipf.write(
                    str(source_path),
                    str(archive_path)
                )


def replace_in_file(file_path, replacements):
    """Replace configured strings in a text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    for old, new in replacements.items():
        content = content.replace(old, new)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


# Package firmware after the build.
env.AddPostAction(
    "$BUILD_DIR/${PROGNAME}.hex",
    copy_fw_files
)

env.AddPostAction(
    "$BUILD_DIR/${PROGNAME}.bin",
    copy_fw_files
)
