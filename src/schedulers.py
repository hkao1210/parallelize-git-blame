"""Bounded independent Git processes; dense composition stays sequential."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from time import perf_counter
from .history import discover, lines
from .diff_map import edge
from .provenance import Origin, compose, identity

def sequential(repo, revision, path):
    return run(repo, revision, path, 'sequential')[0]

def run(repo, revision, path, mode='sequential', workers=1, window=8):
    if mode not in ('sequential', 'full', 'windowed'):
        raise ValueError('unknown scheduling mode')
    if not 1 <= workers <= 32 or window < 1:
        raise ValueError('workers must be 1..32 and window positive')
    if mode == 'sequential' and workers != 1:
        raise ValueError('sequential requires one worker')
    start = perf_counter()
    stats = dict(mode=mode, workers=workers, initial_window=window, diffs=0,
                 identity_edges=0, duplicate_diffs=0, diff_input_bytes=0,
                 patch_bytes=0, diff_task_seconds=0.0, summary_task_seconds=0.0,
                 edge_stage_seconds=0.0, compose_seconds=0.0, windows=0)
    commits, blobs = discover(repo, revision, path, stats)
    summary = identity(len(lines(blobs[-1][1])))
    tip = len(commits)-1
    width = 1 if mode == 'sequential' else (window if mode == 'windowed' else tip)

    def compute(index):
        details = {}
        if blobs[index-1][0] == blobs[index][0]:
            return identity(len(lines(blobs[index][1]))), details
        mapping = edge(repo, commits[index-1], commits[index], path,
                       blobs[index-1][1], blobs[index][1], details)
        return mapping, details

    # Threads coordinate real CPU-running Git child processes. Python summary
    # construction/composition is still GIL-bound and not claimed CPU-parallel.
    context = ThreadPoolExecutor(max_workers=workers) if workers > 1 else nullcontext(None)
    with context as pool:
        while tip > 0 and (mode == 'full' or any(isinstance(x, int) for x in summary)):
            low = max(0, tip-width)
            indices = list(range(tip, low, -1))
            stats['windows'] += 1
            # At most workers futures exist. A window completes before origins
            # are inspected, including its speculative, potentially unused edges.
            mappings = []
            stage = perf_counter()
            for offset in range(0, len(indices), workers):
                chunk = indices[offset:offset+workers]
                batch = list(pool.map(compute, chunk)) if pool else [compute(i) for i in chunk]
                mappings.extend(batch)
            stats['edge_stage_seconds'] += perf_counter()-stage
            stage = perf_counter()
            for mapping, details in mappings:
                summary = compose(mapping, summary)
                if details:
                    stats['diffs'] += 1
                    stats['diff_task_seconds'] += details['diff_seconds']
                    stats['summary_task_seconds'] += details['summary_seconds']
                    stats['diff_input_bytes'] += details['diff_input_bytes']
                    stats['patch_bytes'] += details['patch_bytes']
                else:
                    stats['identity_edges'] += 1
            stats['compose_seconds'] += perf_counter()-stage
            tip = low
            if mode == 'windowed':
                width *= 2
    stage = perf_counter()
    summary = tuple(Origin(commits[0], x+1) if isinstance(x, int) else x for x in summary)
    result = [(x.commit, x.line, i+1) for i, x in enumerate(summary)]
    stats['origin_seconds'] = perf_counter()-stage
    stats['unprocessed_edges'] = tip
    stats['total_seconds'] = perf_counter()-start
    return result, stats
