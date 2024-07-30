import subprocess
import json
import logging
import shlex
import re
# Create a custom logger
_logger = logging.getLogger("exif_tool.log")
_logger.setLevel(logging.INFO)

# Create a handler and formatter
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger
_logger.addHandler(handler)


class ExifToolException(Exception):
    pass


class ExifTool:

    def human_read_to_byte(size):
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        size = size.split()                # divide '1 GB' into ['1', 'GB']
        num, unit = int(size[0]), size[1]
        # index in list of sizes determines power to raise it to
        idx = size_name.index(unit.upper())
        factor = 1024 ** idx               # ** is the "exponent" operator - you can use it instead of math.pow()
        return num * factor

    @classmethod
    def exiftool(cls, file, executable="/usr/local/bin/exiftool"):
        try:

            # dateFormat = r'-d "%Y-%m-%d %H:%M:%S"'
            file = f"\"{file}\""
            command = f'{executable} -j  -n {file}'
            _logger.info(f"Request for {file}")
            _logger.debug(f"Issued Command {command}")

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True  # Use shell=True to run terminal commands
            )
            _logger.debug(f"\n'''\n{result.stdout}\n'''\n")

            if result.returncode != 0 or result.stderr:
                _logger.info(result.returncode)
                _logger.info(result.stderr)
                raise ExifToolException("exiftool failed")

            if result.stdout and result.stdout == '':
                _logger.critical("Raising exception as no result found")
                raise ExifToolException("Empty result")
            return json.loads(result.stdout)[0]  # As we support only one file
        except Exception as e:
            _logger.critical("Exception raised. Did you handle it?")
            raise e


if __name__ == '__main__':
    with open("/home/anandas/Documents/mediaFromAnandaS/files.txt") as f:
        files = f.readlines()
    files1 = [
        "\"/home/anandas/Documents/mediaFromAnandaS/grouped/Photobooth/Archive/Photos/2019/5/19/4-up on 19-05-19 at 12.20 PM #2.jpg\"",
        '\"/home/anandas/Documents/mediaFromAnandaS/grouped/windows_phone/Archive/Photos/2015/7/18/WP_20150718_15_14_09_Pro(1).jpg\"']

    for file in files1:
        result = json.dumps(ExifTool.exiftool(file), indent=2)
        _logger.info(f"json decode successful, {len(result)}")
