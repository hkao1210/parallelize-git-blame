import random
import tempfile
import unittest
from pathlib import Path
from src.history import Unsupported, git
from src.oracle import blame
from src.provenance import Origin, identity, compose
from src.schedulers import sequential, run
from .fixtures import CASES, create, random_versions

class Correctness(unittest.TestCase):
    def check_history(self, versions):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            commits = create(repo, versions)
            for commit, content in zip(commits, versions):
                if content is not None:
                    self.assertEqual(sequential(repo, commit, 'file.txt'), blame(repo, commit, 'file.txt'))

    def test_deterministic(self):
        for name, versions in CASES.items():
            with self.subTest(case=name):
                self.check_history(versions)

    def test_randomized(self):
        for seed in range(100):
            with self.subTest(seed=seed):
                self.check_history(random_versions(seed))

    def test_algebra(self):
        rng = random.Random(811)
        for trial in range(1000):
            sizes = [rng.randrange(9) for _ in range(4)]
            def summary(older, newer, tag):
                return tuple(rng.randrange(older) if older and rng.random() < .7 else Origin(tag, i+1) for i in range(newer))
            a, b, c = [summary(sizes[i], sizes[i+1], str(i)) for i in range(3)]
            self.assertEqual(compose(a, compose(b, c)), compose(compose(a, b), c))
            self.assertEqual(compose(identity(sizes[0]), a), a)
            self.assertEqual(compose(a, identity(sizes[1])), a)
            terminal = (Origin('new', 1),)
            self.assertEqual(compose(a, terminal), terminal)

    def test_reject_merge_binary_deletion_attributes(self):
        for kind in ('merge', 'binary', 'deletion', 'attributes'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                repo = Path(directory)
                commits = create(repo, [b'a\n', b'a\nb\n'])
                revision = 'HEAD'
                if kind == 'merge':
                    tree = git(repo, 'rev-parse', 'HEAD^{tree}').decode().strip()
                    revision = git(repo, 'commit-tree', tree, '-p', commits[0], '-p', commits[1], '-m', 'merge').decode().strip()
                elif kind == 'binary':
                    (repo / 'file.txt').write_bytes(b'a\0b')
                    git(repo, 'add', 'file.txt')
                    git(repo, 'commit', '-qm', 'binary')
                elif kind == 'deletion':
                    git(repo, 'rm', '-q', 'file.txt')
                    git(repo, 'commit', '-qm', 'delete')
                else:
                    (repo / '.gitattributes').write_text('* diff=custom\n')
                with self.assertRaises(Unsupported):
                    sequential(repo, revision, 'file.txt')

    def test_parallel_and_windows(self):
        cases = list(CASES.items()) + [(str(seed), random_versions(seed)) for seed in range(100)]
        for name, versions in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                repo = Path(directory)
                create(repo, versions)
                expected = blame(repo, 'HEAD', 'file.txt')
                for mode in ('full', 'windowed'):
                    actual, stats = run(repo, 'HEAD', 'file.txt', mode, 2, 2)
                    self.assertEqual(actual, expected)
                    self.assertEqual(stats['duplicate_diffs'], 0)

    def test_early_stop_and_full_work(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create(repo, [b'old\n'] * 10 + [b'new\n'])
            expected = blame(repo, 'HEAD', 'file.txt')
            for workers in (1, 2, 4, 8):
                actual, stats = run(repo, 'HEAD', 'file.txt', 'windowed', workers, 2)
                self.assertEqual(actual, expected)
                self.assertEqual(stats['unprocessed_edges'], 8)
                self.assertEqual(stats['commits'], 11)  # discovery remains eager
            actual, stats = run(repo, 'HEAD', 'file.txt', 'full', 4)
            self.assertEqual(actual, expected)
            self.assertEqual(stats['unprocessed_edges'], 0)

    def test_reject_rename_source(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create(repo, [b'a\n'])
            git(repo, 'mv', 'file.txt', 'renamed.txt')
            git(repo, 'commit', '-qm', 'rename')
            with self.assertRaises(Unsupported):
                sequential(repo, 'HEAD', 'renamed.txt')

    def test_scope_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            create(repo, [b'a\n'])
            git(repo, 'config', 'blame.ignoreRevsFile', 'ignored')
            with self.assertRaises(Unsupported):
                sequential(repo, 'HEAD', 'file.txt')
            git(repo, 'config', '--unset', 'blame.ignoreRevsFile')
            (repo / 'other').write_text('source')
            git(repo, 'add', 'other')
            git(repo, 'commit', '-qm', 'other file')
            self.assertEqual(sequential(repo, 'HEAD', 'file.txt'), blame(repo, 'HEAD', 'file.txt'))

if __name__ == '__main__':
    unittest.main()
