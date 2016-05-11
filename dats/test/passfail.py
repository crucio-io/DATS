#
# Dataplane Automated Testing System
#
# Copyright (c) 2015-2016, Intel Corporation.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
The interface for pass/fail tests, like functional tests for PROX.

This abstract base class defines the common properties and methods for tests
that yield a pass/fail result.
"""

import abc
import time
import logging
import inspect
import sys
import os.path as path

import dats.test.base
import dats.rstgen as rst


class PassFail(dats.test.base.TestBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Initialize the test object.
        """
        super(PassFail, self).__init__()
        self._kpi = dict(success=0, total=0)
        self._results = []

    def update_kpi(self, results):
        logging.debug('update_kpi called with result %s', results)
        logging.debug('KPI before: %s', self._kpi)

        for result in results:
            self._kpi['total'] += 1

            if result['result']:
                self._kpi['success'] += 1

        logging.debug('KPI after: %s', self._kpi)

    def kpi(self):
        return "{}/{} succeeded".format(self._kpi['success'], self._kpi['total'])

    def run_all_tests(self):
        """Run all methods marked with the @passfailtest decorator.

        Returns:
            [{...}]. An array with a dict per test.
        """
        # Get all members that are instances of the passfailtest class. These
        # members are the ones decorated with @passfailtest.
        test_methods = inspect.getmembers(self, inspect.ismethod)
        test_methods = filter(lambda kv: 'is_test' in kv[1].__func__.__dict__.keys(), test_methods)
        logging.debug("test_methods: %s", test_methods)

        for test in test_methods:
            name, method = test
            logging.info("Running test %s", name)

            self._results.append(dict(name=name, descr=method.__doc__, results=[]))

            if method.__func__.__dict__['setup'] is not None:
                method.__func__.__dict__['setup'](self)

            method()

            if method.__func__.__dict__['teardown'] is not None:
                method.__func__.__dict__['teardown'](self)

            self.update_kpi(self._results[-1]['results'])

        return self._results


    def generate_report(self, results, prefix, dir):
        # Generate table
        table = [['Test name', 'Result', 'Description']]
        for result in results:
            table.append([result['name'], '\ ', result['descr']])

            for test in result['results']:
                table.append(['\ ', 'Pass' if test['result'] else ':problematic:`Fail`', test['msg']])

        # Generate reStructuredText report
        report = ''
        report += rst.simple_table(table)

        return report


    ## Assertions
    # Pass if bool(cond) is True
    def ok(self, cond, msg = None):
        self._add_result('ok', bool(cond) == True, msg)

    # Pass if a == b
    def equal(self, a, b, msg = None):
        self._add_result('equal', a == b, msg)

    # Pass if a and b compare equal
    def cmp(self, a, b, msg = None):
        self._add_result('cmp', cmp(a, b) == 0, msg)

    # Pass if a != b
    def notEqual(self, a, b, msg = None):
        self._add_result('notEqual', a != b, msg)

    # Pass if bool(cond) is True
    def isTrue(self, cond, msg = None):
        self._add_result('isTrue', bool(cond) == True, msg)

    # Pass if bool(cond) is False
    def isFalse(self, cond, msg = None):
        self._add_result('isFalse', bool(cond) == False, msg)


    ## Helper methods
    def _add_result(self, assertion, result, msg):
        logging.verbose("- (%s) assertion: %s", 'pass' if result else 'FAIL', msg)
        # Retrieve test source for debugging and diagnostic information. The
        # caller frame of interest is 2 up: once for the assertion that called
        # _add_result() and once for the call to the assertion itself.
        caller = sys._getframe(2)
        lineno = caller.f_lineno

        # inspect.getsourcelines(...) returns an list of source lines, and the
        # line number of the start of the source line.
        # lineno retrieved above is used to pick the source line that called
        # one of the assertions.
        # Leading and trailing whitespace is stripped.
        source = inspect.getsourcelines(caller)
        source = source[0][lineno - source[1]]
        source = source.strip()

        self._results[-1]['results'].append(dict(
            assertion=assertion,
            result=result,
            msg=msg,
            lineno=caller.f_lineno,
            filename=path.splitext(path.basename(caller.f_code.co_filename))[0],
            stmt=source,
        ))


def passfailtest(f=None, setup=None, teardown=None):
    """Decorator to mark functions that execute pass/fail tests.

    Only methods marked with this decorator will be executed during a test run.

    The assert functions keep track of the result and the name of the
    assertion, so a proper report can be generated.

    If any of the setup or teardown parameters are specified, the methods
    that are provided will be called respectively before and after the test
    method itself.
    The parameters must be methods that don't take any arguments. They will be
    called with self as the only argument.
    """
    logging.debug("@passfailfunc called: f=%s, setup=%s, teardown=%s", f, setup, teardown)

    def make_test(f):
        logging.trace("Wrapping test %s with setup and teardown", f.__name__)

        f.__dict__.update(is_test=True, setup=setup, teardown=teardown)
        return f

    if f:
        return make_test(f)
    else:
        return make_test
