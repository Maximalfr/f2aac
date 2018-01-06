#!/usr/bin/python3
# Requirement:
# mutagen (1.39-1)
# fdkaac (0.6.3-1)
# ffmpeg
# TODO add args to modify encoder param
# TODO fix the print issue with parallel encoding
# TODO fix the bug with invisible text in terminal after convert a directory.
#      Maybe it's the threading (reset)
# TODO Add arg to choose the number of threads for encoding

import subprocess
import os
import sys
import argparse
import threading
from time import sleep
from mutagen.flac import FLAC
from mutagen.mp3 import MP3, EasyMP3
from mutagen.easymp4 import EasyMP4, EasyMP4KeyError
from mutagen.mp4 import MP4, MP4Cover

__version__ = "0.6.0-2"  # major.minor.(patch)-(revision) | (int.int.int-hexa)
f2aac_version = __version__
verbose = True


class doc():
    """Contains all help strings for argparse"""
    DESC = "Convert flac and mp3 file to aac file"
    INPUT = "file or directory"
    OUT = "output directory"
    QUIET = "don't print progress messages"
    VERSION = "print the version of the script."


def print_verb(message):
    """Print a message on the screen if the global variable verbose = True"""
    global verbose
    if verbose:
        print(message)


def listfile(path):
    """ List all the files in a directory.
    Return a list which contains DirEntry Object.
    Files are filtered by extension (mp3, flac).
    """
    files = []
    with os.scandir(path) as it:
        for entry in it:
            if (entry.name.endswith('.flac') or entry.name.endswith('.mp3')) \
                 and entry.is_file():

                files.append(entry)
    return files


def tag(mp4_file, input_file, tag=True, cover=True):
    """Tag the mp4 file with input_file's tags.
    We can choose to put just the cover of the input file into the mp4 file:
    - tag = False
    or just tags:
    - cover = False.
    """
    def _tag(infos):
        m4a = EasyMP4(mp4_file)
        for tag in infos.items():
            try:
                m4a.setdefault(tag[0], tag[1])  # 0: key, 1: value
            except EasyMP4KeyError:  # if is not a mp4 tag key
                pass
        m4a.save()

    # For flac input
    if input_file.endswith('.flac'):
        infos = FLAC(input_file)
        if tag:
            _tag(infos)
        if cover:
            # Pictures
            m4a = MP4(mp4_file)
            mp4_pic = []
            for pic in infos.pictures:
                mp4_pic.append(MP4Cover(pic.data))
            m4a['covr'] = mp4_pic
            m4a.save()

    elif input_file.endswith('.mp3'):
        infos = EasyMP3(input_file)
        if tag:
            _tag(infos)
        if cover:
            # Pictures
            mp3 = MP3(input_file)
            m4a = MP4(mp4_file)
            if mp3.get('APIC:') is not None:
                m4a['covr'] = [mp3.get('APIC:').data]
                m4a.save()


def encoder(input_file, output_directory=None):
    """Encode mp3 or flac file to aac (mp4 container).
    It's using ffmpeg to decode the input file and fdkaac to encode.
    fdkaac is configured to encode in VBR mode in quality 5 (max).
    """
    # We convert DirEntry type to str
    if type(input_file) is os.DirEntry:
        input_name = input_file.name
        input_path = input_file.path
    else:
        input_name = input_file.split('/')[-1]  # remove the path
        input_path = input_file

    # Need the file extension
    file_ext = os.path.splitext(input_name)[1]

    if output_directory:
        if os.path.isdir(output_directory) is False:  # create the dir if not exist
            os.makedirs(output_directory)
        if output_directory.endswith('/') is False:  # add '/' if not exist
            output_directory += '/'

        new_file = output_directory + input_name.replace(file_ext, '.m4a')
    else:
        new_file = input_name.replace(file_ext, '.m4a')

    param_ffmpeg = ['ffmpeg', '-v', '0', '-i', input_path, '-f', 'caf', 'pipe:1']
    param_fdkaac = ['fdkaac', '-', '-o', new_file, '-m', '5']
    if verbose is False:
        param_fdkaac.append('-S')  # Silence mode for fdkaac

    print_verb(new_file)
    fdec = subprocess.Popen(param_ffmpeg, stdout=subprocess.PIPE)
    subprocess.run(param_fdkaac, stdin=fdec.stdout)
    fdec.wait()

    tag(new_file, input_path, tag=False)
    # tag=False because we use caf format as output for ffmpeg. And fdkaac can
    # copy tags from caf into the m4a file.
    print_verb("Tag : %s \n" % input_name)


def main(argv):
    global verbose
    parser = argparse.ArgumentParser(description=doc.DESC)
    parser.add_argument('input', help=doc.INPUT)
    parser.add_argument('-o', metavar='OUTPUT_DIR', dest='out', help=doc.OUT)
    parser.add_argument('-q', dest='quiet', action='store_true', help=doc.QUIET)
    parser.add_argument('--version', action='version', help=doc.VERSION,
                        version='%(prog)s: {}'.format(f2aac_version))

    results = parser.parse_args(argv)

    if results:
        if results.quiet:
            verbose = False
        if os.path.isdir(results.input):  # If it's a directory
            for f in listfile(results.input):
                while threading.active_count() > 4:  # 4 threads
                    sleep(0.5)
                threading.Thread(target=encoder, args=[f, results.out]).start()
        else:
            encoder(results.input, results.out)

    os.system('stty sane')  # Temporary fix for the terminal issue
    exit(0)  # Useless?


if __name__ == "__main__":
    main(sys.argv[1:])
