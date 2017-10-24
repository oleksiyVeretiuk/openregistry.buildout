import sys
import nose
import argparse
from pkg_resources import iter_entry_points
import logging


nose_env = {
    "NOSE_WITH_XUNIT": 1,
    "NOSE_WITH_COVERAGE": 1,
    "NOSE_COVER_PACKAGE": [],
    "NOSE_COVER_ERASE": 1,
    "NOSE_COVER_HTML": 1,
    "NOSE_PROCESSES": 0
}


def get_tests(packages):
    cover_packages = list()
    all_tests = list()
    for pack in packages:
        group = pack.split('.')[0] if pack.split('.')[0:1] else ''
        for entry_point in iter_entry_points(group=group + '.tests'):
            package_name = group + '.{}'
            package_name = package_name.format(entry_point.name)
            cover_packages.append(package_name)
            suite = entry_point.load()
            if package_name.startswith(pack):
                for tests in suite():
                    all_tests.append(tests)
    return all_tests, cover_packages


def get_pytests(packages):
    pytests = list()
    pytest_packages = list()
    for pack in packages:
        group = pack.split('.')[0] if pack.split('.')[0:1] else ''
        for entry_point in iter_entry_points(group=group + '.pytests'):
            package_name = group + '.{}'.format(entry_point.name)
            pytest_packages.append(package_name)
            if package_name.startswith(pack):
                pytests.append(entry_point.load())
    return pytests, pytest_packages


def unpack_suites(suites, tests, parent=None):
    for suite in suites:
        if hasattr(suite, '_tests'):
            unpack_suites(suite._tests, tests, parent=suite)
        elif parent:
            tests += parent._tests
            return
        else:
            tests += suite


if __name__ == '__main__':
    logger = logging.getLogger('console_output')
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    all_packages = ['openregistry', 'openprocurement']
    parser = argparse.ArgumentParser(description='Test some packages.')
    parser.add_argument('packages', metavar='P', type=str, nargs='*',
                        help='name of packages to test', default=all_packages)
    parser.add_argument('--list-packages', dest='list_packages', action='store_const',
                        const=True, default=False,
                        help='List packages that can be tested')
    args = parser.parse_args()
    nose_tests, cover_packages = get_tests(list(set(args.packages)))
    pytests, pytest_packages = get_pytests(args.packages)
    if args.list_packages:
        logger.info('NOSETESTS:')
        for p in cover_packages:
            logger.info("> {}".format(p))
        logger.info('PYTESTS:')
        for p in pytest_packages:
            logger.info("> {}".format(p))
        exit()
    nose_env['NOSE_COVER_PACKAGE'] = cover_packages
    unpacked_tests = []
    unpack_suites(nose_tests, unpacked_tests)
    sys.exit([suite() for suite in pytests],
             nose.run_exit(suite=unpacked_tests, env=nose_env))
