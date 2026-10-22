from pathlib import Path
import os


def postprocess(comic_info, pages, global_values):
    (Path(os.environ['OUTPUT_DIR']) / '.hook-private').write_text('Must be filtered after hooks')
