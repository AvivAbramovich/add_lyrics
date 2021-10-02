import argparse
import os
import sys
import logging
import re
import enum

import lyricsgenius
import music_tag
from termcolor import colored

try:
    # not essential, so pass if not available
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    print('module python-dotenv not available')

MUSIC_EXTENSIONS = ['.mp3', '.m4a']
LYRICS_DEFAULT_EXTENSION = '.lyrics'
PATTERN = re.compile(r'((?:\d+)?EmbedShare URLCopyEmbedCopy)')

logger = logging.getLogger('add_lyrics')
logger.addHandler(logging.StreamHandler())


class Status(enum.Enum):
    SUCCEED = 1
    SKIPPED = 2
    NO_MUSIC_FILE = 3
    NO_LYRICS_FOUND = 4


def clean_lyrics(lyrics: str) -> str:
    result = PATTERN.findall(lyrics)
    if result:
        len_to_cut = len(result[0])
        lyrics = lyrics[:-len_to_cut]
    return lyrics


def work(genius, dir_path, filename) -> Status:
    name, ext = os.path.splitext(filename)
    if ext not in MUSIC_EXTENSIONS:
        return Status.NO_MUSIC_FILE

    lyrics_path = os.path.join(dir_path, f'{name}.{args.lyrics_ext}')
    logger.debug('lyrics file path for "%s": "%s"', filename, lyrics_path)
    if os.path.isfile(lyrics_path):
        logger.info('Lyrics file for "%s" already exists, skipping...', name)
        return Status.SKIPPED
    else:
        filepath = os.path.join(dir_path, filename)
        logger.info('Analyze file "%s"...', filepath)

        t = music_tag.load_file(filepath)
        title = str(t['name'])
        artist = str(t['artist'])
        logger.info('Fetching lyrics for "%s" By "%s"', title, artist)

        song = genius.search_song(title, artist)

        if song is None:
            logger.error('No lyrics found for "%s" by "%s"', title, artist)
            return Status.NO_LYRICS_FOUND

        logger.info('Successfully fetched lyrics for "%s" By "%s"', title, artist)

        # remove suffix
        lyrics = clean_lyrics(song.lyrics)

        logger.info('Set lyrics for "%s" By "%s"', title, artist)
        t['lyrics'] = lyrics
        t.save()

        with open(lyrics_path, 'w') as f:
            f.write(lyrics)

        return Status.SUCCEED


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('path', help='path to a file or directory')
    args_parser.add_argument('--lyrics-ext', help='the lyrics files extension',
                             default=LYRICS_DEFAULT_EXTENSION)
    args_parser.add_argument('--genius-access-token',
                             default=os.environ.get('GENIUS_CLIENT_ACCESS_TOKEN'))
    args_parser.add_argument('--log-level', default='INFO')
    args = args_parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level))

    if not os.path.exists(args.path):
        logger.error('"%s" does not exist', args.path)
        sys.exit(1)

    if not args.genius_access_token:
        logger.error('No genius_access_token available. abort')
        sys.exit(1)

    genius = lyricsgenius.Genius(args.genius_access_token)

    logger.info('Start walking "%s"', args.path)

    songs_succeed = 0
    songs_skipped = 0
    songs_failed = 0

    if os.path.isfile(args.path):
        dir_path, filename = os.path.split(args.path)
        res = work(genius, dir_path, filename)
        if res in [Status.NO_MUSIC_FILE, Status.NO_LYRICS_FOUND]:
            sys.exit(1)
    else:
        try:
            for dir_path, _, filenames in os.walk(args.path):
                for filename in filenames:
                    try:
                        res = work(genius, dir_path, filename)
                        if res is Status.SUCCEED:
                            songs_succeed += 1
                        elif res is Status.SKIPPED:  # res could be None if the file isn't music file
                            songs_skipped += 1
                        elif res is Status.NO_LYRICS_FOUND:
                            songs_failed += 1
                    except Exception as e:
                        logger.exception(e)
                        songs_failed += 1
        except KeyboardInterrupt:
            logger.info('Keyboard Interrupt')

        logger.info('Done!')
        logger.info(colored(f'{songs_succeed} succeed', 'green'))
        logger.info(colored(f'{songs_skipped} skipped', 'yellow'))
        logger.info(colored(f'{songs_failed} failed', 'red'))
