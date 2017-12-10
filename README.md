# f2aac
Script to easily encode audio files in aac format.
f2acc can convert mp3 and flac file.
The input can be a file or a directory.
For the moment, encoding parameters are aac VBR V5 (the max). For more information, see fdkaac doc.

## Requirement
- mutagen (1.39-1)
- fdkaac (0.6.3-1)

## Example
```
./f2aac.py darude-sandstorm.flac
```
```
./f2aac.py album -o converted_album
```
