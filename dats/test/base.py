# Dataplane Automated Testing System
# Copyright (c) 2015, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
The interface for all DATS tests.

This abstract base class defines the common properties and methods that
all DATS tests must implement, as well as test fixture functions that should
be overridden in subclasses to help with setup and teardown of the environment.

Suppose a class TestClass, derived from dats.test.passfail.PassFail,
implements test methods test1(), test2() and test3().

The test run looks like:
    - object testObject is instantiated from class TestClass
        - testObject.setup_class() is called
        - testObject.run_all_tests() is called
            - testObject.setup_test() is called
                - testObject.test1() is called
            - testObject.teardown_test() is called
            - testObject.setup_test() is called
                - testObject.test2() is called
            - testObject.teardown_test() is called
            - testObject.setup_test() is called
                - testObject.test3() is called
            - testObject.teardown_test() is called
        - testObject.teardown_class() is called
    - testObject is destroyed
"""

import abc
import sys
import logging

from dats.remote_control import remote_system
import dats.config as config


class TestBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Initialize the test object.

        The short and long description are extracted from the docstring of the
        test.

        Raises:
            AssertionError: if no docstring is present.
        """
        super(TestBase, self).__init__()

        assert self.__doc__, "Test {} has no docstring. This is needed for the test description.".format(self.__class__)

        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
        descr_lines = self.__doc__.expandtabs().splitlines()

        # Determine minimum indentation (first line doesn't count):
        indent = sys.maxint
        for descr_line in descr_lines[1:]:
            stripped = descr_line.lstrip()
            if stripped:
                indent = min(indent, len(descr_line) - len(stripped))

        # Remove indentation (first line is special):
        trimmed = [descr_lines[0].strip()]
        if indent < sys.maxint:
            for descr_line in descr_lines[1:]:
                trimmed.append(descr_line[indent:].rstrip())

        # Strip off trailing and leading blank lines:
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)

        # Short description is the first non-blank line
        self.__short_descr = trimmed.pop(0)

        # Long description can be separated from the short description with
        # one or more blank lines. Let's skip those.
        while trimmed and not trimmed[0]:
            trimmed.pop(0)

        # All lines are concatenated with a space character in between. Blank
        # lines are paragraph separators, they are converted to a \n instead.
        self.__long_descr = trimmed.pop(0)
        for descr_line in trimmed:
            if not descr_line:
                # Empty line, convert to \n
                self.__long_descr += '\n'
            else:
                if self.__long_descr[-1:] == '\n':
                    # Non-empty line, first line of a new paragraph
                    self.__long_descr += descr_line
                else:
                    # Non-empty line, continuation of previous line
                    self.__long_descr += ' ' + descr_line

        # Variable initialization
        self._kpi = None
        self._remotes = {}

        return

    def short_descr(self):
        """Return the short description of the test.

        The short description is the first non-empty line of the docstring of
        the test class.

        Returns:
            str. The short description of the test.
        """
        return self.__short_descr

    def long_descr(self):
        """Return the long description of the test.

        The long description is all text after the first line of the docstring.
        Lines are concatenated with a space character in between, empty lines
        are converted to newlines.

        Returns:
            str. The long description of the test.
        """
        return self.__long_descr

    def get_remote(self, remote_name):
        """Return remote object for remote_name.

        This method returns an object of type remote_system that corresponds to
        the remote with name remote_name defined in the config file.

        Returns:
            remote_system. An object representing the requested remote.
        """
        if remote_name in self._remotes:
            return self._remotes[remote_name]

        if remote_name == "sut":
            self._remotes[remote_name] = remote_system(config.getOption('sutUser'),
                    config.getOption('sutIp'), config.getOption('sutDpdkDir'),
                    config.getOption('sutDpdkTgt'),
                    config.getOption('sutProxDir'))
        elif remote_name == "tester":
            self._remotes[remote_name] = remote_system(config.getOption('testerUser'),
                    config.getOption('testerIp'), config.getOption('testerDpdkDir'),
                    config.getOption('testerDpdkTgt'),
                    config.getOption('testerProxDir'))
        else:
            raise NameError("The remote with name '" + remote_name + "' is not defined in the config file")

        return self._remotes[remote_name]


    def kpi(self):
        """Return the Key Performance Indicator (KPI) for the test.

        Returns:
            str. The KPI for the test.
        """
        return self._kpi if self._kpi else '***Not measured***'

    @abc.abstractproperty
    def update_kpi(self, result):
        """Update the Key Performance Indicator (KPI) with the test results.
        """
        return

    def setup_class(self):
        """Perform actions that need to happen once, before all tests are run.

        This method may be overridden by the test classes.

        Possible uses are: call setup_remotes(), one-time copy of configuration
        files to remote, ...
        """
        logging.warning("No actions for test class setup specified. If this is intentional, override setup_class() in the test with 'pass' in the body, to prevent this warning.")

    def teardown_class(self):
        """Perform actions that need to happen after all tests are run.

        This method may be overridden by the test classes.

        Possible uses are: cleanup of remote files, call teardown_remotes(), ...
        """
        logging.warning("No actions for test class teardown specified. If this is intentional, override teardown_class() in the test with 'pass' in the body, to prevent this warning.")


    def setup_test(self, **kwargs):
        """Perform actions that need to happen before a test is run.

        This method may be overridden by specific test cases.

        Args:
            **kwargs: To be defined by the test implementation
        """
        pass

    def teardown_test(self, **kwargs):
        """Perform actions that need to happen after a test has run.

        This method may be overridden by specific test cases.

        Args:
            **kwargs: To be defined by the test implementation
        """
        pass

    @abc.abstractmethod
    def run_all_tests(self):
        """Run all the tests in the script.

        What "all tests" means, depends on what kind of test is implemented.
        Some possibilities are: iterate over a list of packet sizes and execute
        a single test case with those, run all test functions defined in the
        class, ...

        Subclasses must implement the behavior that is expected for the kind of
        test they represent.

        Returns:
            [{...}]. An array of dictionaries with all the test parameters,
                results and optionally other data that is needed to generate a
                report.
                This array will be consumed by generate_report().
        """
        return

    @abc.abstractmethod
    def generate_report(self, results, prefix, dir):
        """Generate the report for the provided results.

        The generated report must be in reStructuredText format and will be
        included verbatim in the full report.

        The provided prefix is a unique identifier, containing only
        alphanumerics and underscores. It can be used as a filename prefix,
        rST internal reference prefix, ...
        This way tests can create auxiliary files like graphs, ... without any
        risk of overwriting auxiliary files generated by other tests.

        The rST text may contain headings. The adornments to use for headings
        are, in order: +, ^, ".

        Args:
            results ([{...}]): An array of dictionaries, as returned by
                run_all_tests()
            prefix (str): a unique identifier for this test, which can be used
                to prefix filenames, link id's, ...
            dir (str): directory name where all auxiliary files must be placed

        Returns:
            str. The report for the provided results in reStructuredText format.
        """
        pass
