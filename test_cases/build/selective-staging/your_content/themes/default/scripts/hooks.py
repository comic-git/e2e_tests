from pathlib import Path
import os


def postprocess(config, pages, global_values):
    output = Path(os.environ.get('OUTPUT_DIR', 'build'))
    (output / '.hook-private').write_text('hidden hook output', encoding='utf-8')
