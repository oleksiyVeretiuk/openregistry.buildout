import sys
import os
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
    "NOSE_PROCESSES": 0,
    "NOSE_WITH_DOCTEST": 1,
    "NOSE_NOCAPTURE": 1
}
os.environ['PYTEST_ADDOPTS'] = '--ignore=src/ --junitxml=pytest.xml'


def get_tests(packages, test_type):
    tested_packages = list()
    all_tests = list()
    for pack in packages:
        group = pack.split('.')[0] if pack.split('.')[0:1] else None
        if group is None:
            continue
        for entry_point in iter_entry_points(group=group + '.' + test_type):
            package_name = group + '.{}'
            package_name = package_name.format(entry_point.name)
            tested_packages.append(package_name)
            suite = entry_point.load()
            if package_name.startswith(pack):
                if test_type == 'tests':
                    for tests in suite():
                        all_tests.append(tests)
                elif test_type == 'pytests':
                    all_tests.append(suite)
    return all_tests, tested_packages


def unpack_suites(suites):
    tests = list()
    for suite in suites:
        if hasattr(suite, '_tests'):
            tests += unpack_suites(suite._tests)
        else:
            tests.append(suite)
    return tests


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
    unique_packages = set(args.packages)
    nose_tests, cover_packages = get_tests(unique_packages, 'tests')
    pytests, pytest_packages = get_tests(unique_packages, 'pytests')
    if args.list_packages:
        logger.info('NOSETESTS:')
        for p in cover_packages:
            logger.info("> {}".format(p))
        logger.info('PYTESTS:')
        for p in pytest_packages:
            logger.info("> {}".format(p))
        exit()
    nose_env['NOSE_COVER_PACKAGE'] = cover_packages
    unpacked_tests = unpack_suites(nose_tests)
    sys.exit([suite() for suite in pytests],
             nose.run_exit(suite=unpacked_tests, env=nose_env))
