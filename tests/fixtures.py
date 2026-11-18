import random
from src.history import git

CASES = {
    'append_prepend': [b'a\n', b'a\nb\n', b'z\na\nb\n'],
    'middle_insert_delete': [b'a\nb\nc\n', b'a\nx\nb\nc\n', b'a\nx\nc\n'],
    'replace': [b'a\nb\n', b'a\nx\n'],
    'repeated_lines': [b'a\nx\na\nx\n', b'a\na\nx\n', b'x\na\nx\na\n'],
    'delete_reintroduce': [b'keep\nold\n', b'keep\n', b'keep\nold\n'],
    'empty': [b'', b'a\n', b''],
    'no_trailing_newline': [b'a\nb', b'a\nb\n', b'a\nc'],
    'whitespace': [b'a\n b\n', b'a \n\tb\n'],
    'alternating': [b'a\nb\n', b'x\nb\n', b'x\ny\n', b'a\ny\n'],
    'creation_untouched': [None, None, b'a\n', b'a\n', b'a\n'],
    'crlf': [b'a\r\nb\r\n', b'a\r\nc\r\n'],
}

def random_versions(seed):
    rng = random.Random(seed)
    content = [rng.choice([b'a', b'b', b'', b'  x', b'}']) for _ in range(rng.randrange(8))]
    versions = []
    for _ in range(7):
        pos = rng.randrange(len(content) + 1)
        content[pos:pos + rng.randrange(3)] = [rng.choice([b'a', b'b', b'', b'  x', b'}']) for _ in range(rng.randrange(4))]
        versions.append(b'\n'.join(content) + (b'\n' if content and rng.random() < .8 else b''))
    return versions

def create(repo, versions):
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, 'init', '-q', '--object-format=sha1')
    git(repo, 'config', 'user.name', 'Fixture')
    git(repo, 'config', 'user.email', 'fixture@example.invalid')
    git(repo, 'config', 'core.autocrlf', 'false')
    git(repo, 'config', 'commit.gpgsign', 'false')
    commits = []
    for i, content in enumerate(versions):
        if content is not None:
            (repo / 'file.txt').write_bytes(content)
            git(repo, 'add', '--', 'file.txt')
        stamp = f'{1700000000 + i} +0000'
        git(repo, 'commit', '-q', '--allow-empty', '-m', f'revision {i}',
            env={'GIT_AUTHOR_DATE': stamp, 'GIT_COMMITTER_DATE': stamp})
        commits.append(git(repo, 'rev-parse', 'HEAD').decode().strip())
    return commits
