# add_lyrics

A python script for adding lyrics for your music library.

This script uses `Genius` API for searching lyrics for the songs from your local music library, and add them to your music files as lyrics tag.

**NOTE:** This script requires an **ACCESS_TOKEN** for `Genius` to request their API.

## Usage
1. Install required dependencies
    ```shell
    pip install -r requirements
    ```
2. Run the script
    ```shell
    python main.py /path/to/library --genius-access-token YOUR_ACCESS_TOKEN
    ```
   this will run recursively on the library using `os.walk` and search for any valid music file.

   You can also provide a single file, like:
   ```shell
    python main.py /path/to/song.mp3 ...
    ```

## Other Options
1. You can use `.env` file in your current directory and provide a `GENIUS_CLIENT_ACCESS_TOKEN=...` instead of supplying `--genius-access-token` as in the example above
2. When recursively running, you can hit `CTRL+C` any time to abort and get the current statistic of how many files succeed, skipped or failed.

## TODO:
1. Support other music format other than `.mp3` and `.m4a`
2. Parallel/Async work on files
