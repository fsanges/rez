from rez.contrib.version.requirement import VersionedObject
from rez.rex import Comment, EnvAction, Shebang, Setenv, Alias, Appendenv
from rez.resolved_context import ResolvedContext
import unittest
import os



class TestRexCommands(unittest.TestCase):
    def __init__(self, fn):
        unittest.TestCase.__init__(self, fn)
        path = os.path.dirname(__file__)
        self.packages_path = os.path.join(path, "data", "packages")

    def _test_package(self, pkg, env, expected_commands):
        orig_environ = os.environ.copy()

        r = ResolvedContext([str(pkg)],
                            caching=False,
                            package_paths=self.packages_path,
                            add_implicit_packages=False,
                            add_bootstrap_path=False)

        self.assertEqual(orig_environ, os.environ)

        commands = r.get_actions(parent_environ=env)
        commands_ = []
        ignore_keys = set(["REZ_USED",
                           "REZ_REQUEST_TIME",
                           "PATH"
                           ])

        for cmd in commands:
            if isinstance(cmd, (Comment, Shebang)):
                continue
            elif isinstance(cmd, EnvAction) and cmd.key in ignore_keys:
                continue
            else:
                commands_.append(cmd)

        self.assertEqual(commands_, expected_commands)

    def _get_rextest_commands(self, pkg):
        verstr = str(pkg.version)
        base = os.path.join(self.packages_path, "rextest", verstr)
        cmds = [Setenv('REZ_REXTEST_VERSION', verstr),
                Setenv('REZ_REXTEST_BASE', base),
                Setenv('REZ_REXTEST_ROOT', base),
                Setenv('REXTEST_ROOT', base),
                Setenv('REXTEST_VERSION', verstr),
                Setenv('REXTEST_MAJOR_VERSION', str(pkg.version[0])),
                Setenv('REXTEST_DIRS', os.path.join(base, "data")),
                Alias('rextest', 'foobar')]
        return cmds

    def _test_rextest_package(self, version):
        pkg = VersionedObject("rextest-%s" % version)

        cmds = [Setenv('REZ_REQUEST', str(pkg)),
                Setenv('REZ_RESOLVE', str(pkg))]
        cmds += self._get_rextest_commands(pkg)

        self._test_package(pkg, {}, cmds)
        # first prepend should still override
        self._test_package(pkg, {"REXTEST_DIRS":"TEST"}, cmds)

    def test_old_yaml(self):
        self._test_rextest_package("1.1")

    def test_new_yaml(self):
        self._test_rextest_package("1.2")

    def test_py(self):
        self._test_rextest_package("1.3")

    def test_2(self):
        pkg = VersionedObject("rextest2-2")
        base = os.path.join(self.packages_path, "rextest2", "2")

        cmds = [Setenv('REZ_REQUEST', "rextest2-2"),
                Setenv('REZ_RESOLVE', "rextest-1.3 rextest2-2")]
        cmds += self._get_rextest_commands(VersionedObject("rextest-1.3"))
        cmds += [Setenv('REZ_REXTEST2_VERSION', '2'),
                 Setenv('REZ_REXTEST2_BASE', base),
                 Setenv('REZ_REXTEST2_ROOT', base),
                 Appendenv('REXTEST_DIRS', os.path.join(base, "data2")),
                 Setenv('REXTEST2_REXTEST_VER', '1.3'),
                 Setenv('REXTEST2_REXTEST_BASE',
                        os.path.join(self.packages_path, "rextest", "1.3"))]

        self._test_package(pkg, {}, cmds)
        # first prepend should still override
        self._test_package(pkg, {"REXTEST_DIRS":"TEST"}, cmds)


def get_test_suites():
    suites = []
    suite = unittest.TestSuite()
    suite.addTest(TestRexCommands("test_old_yaml"))
    suite.addTest(TestRexCommands("test_new_yaml"))
    suite.addTest(TestRexCommands("test_py"))
    suite.addTest(TestRexCommands("test_2"))
    suites.append(suite)
    return suites
