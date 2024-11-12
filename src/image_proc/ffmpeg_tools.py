import os
import shutil
import subprocess

from werkzeug.exceptions import  InternalServerError, NotFound

class FFMPEGCommands:
    def __init__(self):
        self.video_bitrates = {"720": "3500k", "480": "1690k", "240": "326k"}
        pass

    def toHLS(self, input_file: str, output_dir: str):
        if not os.path.exists(input_file):
            raise NotFound("input file doesn't exists")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        print(output_dir)
        video_bitrates = self.video_bitrates
       
        # Constructing filter complex part
        filter_complex = (
            f"[0:v]split={len(video_bitrates)}" +
            "".join([f"[{res}_in]" for res in video_bitrates.keys()]) + ";" +
            ";".join([f"[{res}_in]scale=-2:{res}[{res}_out]" for res in video_bitrates.keys()])
        )

        # Video and audio map commands
        video_map_commands = [["-map", f'"[{res}_out]"'] for res in video_bitrates.keys()]
        audio_map_commands = [["-map", "0:a"] for _ in video_bitrates.keys()]

        # Bitrate settings using video_bitrates
        video_bitrate_commands = [[f"-b:v:{i}", video_bitrates[res], f"-maxrate:v:{i}", video_bitrates[res], f"-bufsize:v:{i}", video_bitrates[res]] for i, res in enumerate(video_bitrates.keys())]
        audio_bitrate_commands = [[f"-b:a:{i}", "128k"] for i in range(len(video_bitrates))]

       

        # Constructing var_stream_map, including the video copy stream
        var_stream_map = " ".join(
            [f"v:{i},a:{i},name:{res}p-{video_bitrates[res]}" for i, res in enumerate(video_bitrates.keys())]
        )


        # Combine everything into the command
        command = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-filter_complex", f'"{filter_complex}"',
            *[cmd for sublist in video_map_commands + audio_map_commands for cmd in sublist],
            *[cmd for sublist in video_bitrate_commands + audio_bitrate_commands for cmd in sublist],
            "-x264-params", '"keyint=60:min-keyint=60:scenecut=0"',
            "-var_stream_map", f'"{var_stream_map}"',
            "-hls_list_size", "0",
            "-hls_time", "2",
            "-hls_segment_filename", f"{output_dir}/adaptive-%v-%03d.ts",
            #"-master_pl_name", "adaptive.m3u8",
            f"{output_dir}/adaptive-%v.m3u8"
        ]
        print(' '.join(command))
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            raise InternalServerError("\n".join([str(e), process.stderr.read(),' '.join(command)]))
        if not os.path.exists(f"{output_dir}/adaptive.m3u8"):
            raise NotFound( description="\n".join([f'failed to open {output_dir}/adaptive.m3u8', process.stderr.read(),' '.join(command)]))
        return 
      


if __name__ == "__main__":
    FFMPEGCommands().toHLS(
        input_file='/disks/data/git/github/asarangaram/dash_experiment/VID_20240206_095544.mp4',
        output_dir='/disks/data/git/github/asarangaram/dash_experiment/VID_20240206_095544')