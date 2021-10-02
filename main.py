import argparse
import os
import sys
import logging
import re

import lyricsgenius
import music_tag
from termcolor import colored

try:
    # not essential, so pass if not available
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

MUSIC_EXTENSIONS = ['.mp3', '.m4a']
LYRICS_DEFAULT_EXTENSION = '.lyrics'
PATTERN = re.compile(r'((?:\d+)?EmbedShare URLCopyEmbedCopy)')


def clean_lyrics(lyrics: str) -> str:
    result = PATTERN.findall(lyrics)
    if result:
        len_to_cut = len(result[0])
        lyrics = lyrics[:-len_to_cut]
    return lyrics


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('root', help='root path')
    args_parser.add_argument('--lyrics-ext', help='the lyrics files extension',
                             default=LYRICS_DEFAULT_EXTENSION)
    args_parser.add_argument('--genius-access-token', default=os.environ.get('GENIUS_CLIENT_ACCESS_TOKEN'))
    args_parser.add_argument('--log-level', default='INFO')
    args = args_parser.parse_args()

    logger = logging.getLogger('AddLyrics')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(getattr(logging, args.log_level))

    if not os.path.isdir(args.root):
        logger.error('"%s" is not a directory', args.root)
        sys.exit(1)

    if not args.genius_access_token:
        logger.error('No genius_access_token available. abort')
        sys.exit(1)

    genius = lyricsgenius.Genius(args.genius_access_token)

    logger.info('Start walking "%s"', args.root)

    songs_succeed = 0
    songs_skip = 0
    songs_failed = 0

    for dir_path, _, filenames in os.walk(args.root):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            if ext in MUSIC_EXTENSIONS:
                lyrics_path = os.path.join(dir_path, f'{name}.{args.lyrics_ext}')
                logger.debug('lyrics file path for "%s": "%s"', filename, lyrics_path)
                if os.path.isfile(lyrics_path):
                    logger.info('Lyrics file for "%s" already exists, skipping...', name)
                    songs_skip += 1
                else:
                    filepath = os.path.join(dir_path, filename)
                    logger.info('Analyze file "%s"...', filepath)

                    try:
                        t = music_tag.load_file(filepath)
                        title = str(t['name'])
                        artist = str(t['artist'])
                        logger.info('Fetching lyrics for "%s" By "%s"', title, artist)

                        song = genius.search_song(title, artist)

                        logger.info('Successfully fetched lyrics for "%s" By "%s"', title, artist)

                        # remove suffix
                        lyrics = clean_lyrics(song.lyrics)

                        logger.info('Set lyrics for "%s" By "%s"', title, artist)
                        t['lyrics'] = lyrics
                        t.save()

                        with open(lyrics_path, 'w') as f:
                            f.write(lyrics)

                        songs_succeed += 1
                    except Exception as e:
                        logger.exception(e)
                        songs_failed += 1

    logger.info('Done!')
    logger.info(colored(f'{songs_succeed} succeed', 'green'))
    logger.info(colored(f'{songs_skip} skipped', 'yellow'))
    logger.info(colored(f'{songs_failed}', 'red'))
