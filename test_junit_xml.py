# -*- coding: UTF-8 -*-
from __future__ import with_statement
import unittest
import os
import tempfile
import textwrap
from xml.dom import minidom
import codecs

from six import u, PY2

from junit_xml import (TestCase, TestSuite)


def serialize_and_read(test_suites, to_file=False, prettyprint=False, encoding=None):
    """writes the test suite to an XML string and then re-reads it using minidom,
       returning => (test suite element, list of test case elements)"""
    try:
        iter(test_suites)
    except TypeError:
        test_suites = [test_suites]

    if to_file:
        fd, filename = tempfile.mkstemp(text=True)
        os.close(fd)
        with codecs.open(filename, mode='w', encoding=encoding) as f:
            TestSuite.to_file(f, test_suites, prettyprint=prettyprint, encoding=encoding)
        print("Serialized XML to temp file [%s]" % filename)
        xmldoc = minidom.parse(filename)
        os.remove(filename)
    else:
        xml_string = TestSuite.to_xml_string(
            test_suites, prettyprint=prettyprint, encoding=encoding)
        if PY2:
            assert isinstance(xml_string, unicode)
        print("Serialized XML to string:\n%s" % xml_string)
        if encoding:
            xml_string = xml_string.encode(encoding)
        xmldoc = minidom.parseString(xml_string)

    def remove_blanks(node):
        for x in node.childNodes:
            if x.nodeType == minidom.Node.TEXT_NODE:
                if x.nodeValue:
                    x.nodeValue = x.nodeValue.strip()
            elif x.nodeType == minidom.Node.ELEMENT_NODE:
                remove_blanks(x)
    remove_blanks(xmldoc)
    xmldoc.normalize()

    ret = []
    suites = xmldoc.getElementsByTagName("testsuites")[0]
    for suite in suites.getElementsByTagName("testsuite"):
        cases = suite.getElementsByTagName("testcase")
        ret.append((suite, cases))
    return ret


class TestSuiteTests(unittest.TestCase):
    def test_single_suite_single_test_case(self):
        try:
            (ts, tcs) = serialize_and_read(
                TestSuite('test', TestCase('Test1')), to_file=True)[0]
            self.fail("This should've raised an exeception")  # pragma: nocover
        except Exception as exc:
            self.assertEqual(
                str(exc), 'test_cases must be a list of test cases')

    def test_single_suite_no_test_cases(self):
        properties = {'foo': 'bar'}
        package = 'mypackage'
        timestamp = 1398382805

        (ts, tcs) = serialize_and_read(
            TestSuite(
                'test',
                [],
                hostname='localhost',
                id=1,
                properties=properties,
                package=package,
                timestamp=timestamp
            ),
            to_file=True,
            prettyprint=True
        )[0]
        self.assertEqual(ts.tagName, 'testsuite')
        self.assertEqual(ts.attributes['package'].value, package)
        self.assertEqual(ts.attributes['timestamp'].value, str(timestamp))
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['name'].value,
            'foo')
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['value'].value,
            'bar')

    def test_single_suite_no_test_cases_utf8_encoded(self):
        properties = {'foo': 'bar'}
        package = u('mypäckage').encode('utf-8')
        timestamp = 1398382805

        (ts, tcs) = serialize_and_read(
            TestSuite(
                u('testä').encode('utf-8'),
                [],
                hostname='localhost',
                id=1,
                properties=properties,
                package=package,
                timestamp=timestamp
            ),
            to_file=True,
            encoding='utf-8',
            prettyprint=True
        )[0]
        self.assertEqual(ts.tagName, 'testsuite')
        self.assertEqual(ts.attributes['package'].value.encode('utf-8'), package)
        self.assertEqual(ts.attributes['timestamp'].value, str(timestamp))
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['name'].value,
            'foo')
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['value'].value,
            'bar')


    def test_single_suite_no_test_cases_utf8(self):
        properties = {'foö': 'bär'}
        package = 'mypäckage'
        timestamp = 1398382805

        test_suite = TestSuite(
                'äöü',
                [],
                hostname='löcalhost',
                id='äöü',
                properties=properties,
                package=package,
                timestamp=timestamp
            )
        (ts, tcs) = serialize_and_read(
            test_suite,
            to_file=True,
            prettyprint=True,
            encoding='utf-8'
        )[0]
        self.assertEqual(ts.tagName, 'testsuite')
        self.assertEqual(ts.attributes['package'].value.encode('utf-8'), package)
        self.assertEqual(ts.attributes['timestamp'].value, str(timestamp))
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['name'].value.encode('utf-8'),
            'foö')
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['value'].value.encode('utf-8'),
            'bär')


    def test_single_suite_no_test_cases_unicode(self):
        properties = {'foö'.decode('utf-8'): 'bär'.decode('utf-8')}
        package = 'mypäckage'.decode('utf-8')
        timestamp = 1398382805

        (ts, tcs) = serialize_and_read(
            TestSuite(
                'äöü'.decode('utf-8'),
                [],
                hostname='löcalhost'.decode('utf-8'),
                id='äöü'.decode('utf-8'),
                properties=properties,
                package=package,
                timestamp=timestamp
            ),
            to_file=True,
            prettyprint=True,
            encoding='utf-8'
        )[0]
        self.assertEqual(ts.tagName, 'testsuite')
        self.assertEqual(ts.attributes['package'].value, package)
        self.assertEqual(ts.attributes['timestamp'].value, str(timestamp))
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['name'].value,
            'foö'.decode('utf-8'))
        self.assertEqual(
            ts.childNodes[0].childNodes[0].attributes['value'].value,
            'bär'.decode('utf-8'))

    def test_single_suite_to_file(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test', [TestCase('Test1')]), to_file=True)[0]
        verify_test_case(self, tcs[0], {'name': 'Test1'})

    def test_single_suite_to_file_prettyprint(self):
        (ts, tcs) = serialize_and_read(TestSuite(
            'test', [TestCase('Test1')]), to_file=True, prettyprint=True)[0]
        verify_test_case(self, tcs[0], {'name': 'Test1'})

    def test_single_suite_prettyprint(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test', [TestCase('Test1')]),
            to_file=False, prettyprint=True)[0]
        verify_test_case(self, tcs[0], {'name': 'Test1'})

    def test_single_suite_to_file_no_prettyprint(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test', [TestCase('Test1')]),
            to_file=True, prettyprint=False)[0]
        verify_test_case(self, tcs[0], {'name': 'Test1'})

    def test_multiple_suites_to_file(self):
        tss = [TestSuite('suite1', [TestCase('Test1')]),
               TestSuite('suite2', [TestCase('Test2')])]
        suites = serialize_and_read(tss, to_file=True)

        self.assertEqual('suite1', suites[0][0].attributes['name'].value)
        verify_test_case(self, suites[0][1][0], {'name': 'Test1'})

        self.assertEqual('suite2', suites[1][0].attributes['name'].value)
        verify_test_case(self, suites[1][1][0], {'name': 'Test2'})

    def test_multiple_suites_to_string(self):
        tss = [TestSuite('suite1', [TestCase('Test1')]),
               TestSuite('suite2', [TestCase('Test2')])]
        suites = serialize_and_read(tss)

        self.assertEqual('suite1', suites[0][0].attributes['name'].value)
        verify_test_case(self, suites[0][1][0], {'name': 'Test1'})

        self.assertEqual('suite2', suites[1][0].attributes['name'].value)
        verify_test_case(self, suites[1][1][0], {'name': 'Test2'})

    def test_attribute_time(self):
        tss = [TestSuite('suite1',
               [TestCase('Test1', 'some.class.name', 123.345),
                TestCase('Test2', 'some2.class.name', 123.345)]),
               TestSuite('suite2', [TestCase('Test2')])]
        suites = serialize_and_read(tss)

        self.assertEqual('suite1', suites[0][0].attributes['name'].value)
        self.assertEqual('246.69', suites[0][0].attributes['time'].value)

        self.assertEqual('suite2', suites[1][0].attributes['name'].value)
        # here the time in testsuite is "0" even there is no attribute time for
        # testcase
        self.assertEqual('0', suites[1][0].attributes['time'].value)

        # @todo: add more tests for the other attributes and properties

    def test_to_xml_string(self):
        test_suites = [TestSuite('suite1', [TestCase('Test1')]),
                       TestSuite('suite2', [TestCase('Test2')])]
        xml_string = TestSuite.to_xml_string(test_suites)
        if PY2:
            self.assertTrue(isinstance(xml_string, unicode))
        expected_xml_string = textwrap.dedent("""
            <?xml version="1.0" ?>
            <testsuites errors="0" failures="0" skipped="0" tests="2" time="0.0">
            \t<testsuite errors="0" failures="0" name="suite1" skipped="0" tests="1" time="0">
            \t\t<testcase name="Test1"/>
            \t</testsuite>
            \t<testsuite errors="0" failures="0" name="suite2" skipped="0" tests="1" time="0">
            \t\t<testcase name="Test2"/>
            \t</testsuite>
            </testsuites>
        """.strip("\n"))  # NOQA
        self.assertEqual(xml_string, expected_xml_string)

    def test_to_xml_string_test_suites_not_a_list(self):
        test_suites = TestSuite('suite1', [TestCase('Test1')])

        try:
            TestSuite.to_xml_string(test_suites)
        except Exception as exc:
            self.assertEqual(
                str(exc), 'test_suites must be a list of test suites')


class TestCaseTests(unittest.TestCase):
    def test_init(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test', [TestCase('Test1')]))[0]
        verify_test_case(self, tcs[0], {'name': 'Test1'})

    def test_init_classname(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test', [TestCase('Test1', 'some.class.name')]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Test1', 'classname': 'some.class.name'})

    def test_init_classname_time(self):
        (ts, tcs) = serialize_and_read(
            TestSuite('test',
                      [TestCase('Test1', 'some.class.name', 123.345)]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Test1', 'classname': 'some.class.name',
                           'time': ("%f" % 123.345)})

    def test_init_stderr(self):
        (ts, tcs) = serialize_and_read(
            TestSuite(
                'test', [TestCase('Test1', 'some.class.name', 123.345,
                                  stderr='I am stderr!')]))[0]
        verify_test_case(
            self, tcs[0],
            {'name': 'Test1', 'classname': 'some.class.name',
             'time': ("%f" % 123.345)}, stderr='I am stderr!')

    def test_init_stdout_stderr(self):
        (ts, tcs) = serialize_and_read(
            TestSuite(
                'test', [TestCase(
                    'Test1', 'some.class.name', 123.345, 'I am stdout!',
                    'I am stderr!')]))[0]
        verify_test_case(
            self, tcs[0],
            {'name': 'Test1', 'classname': 'some.class.name',
             'time': ("%f" % 123.345)},
            stdout='I am stdout!', stderr='I am stderr!')

    def test_init_failure_message(self):
        tc = TestCase('Failure-Message')
        tc.add_failure_info("failure message")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Failure-Message'},
            failure_message="failure message")

    def test_init_failure_output(self):
        tc = TestCase('Failure-Output')
        tc.add_failure_info(output="I failed!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Failure-Output'},
            failure_output="I failed!")

    def test_init_failure(self):
        tc = TestCase('Failure-Message-and-Output')
        tc.add_failure_info("failure message", "I failed!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Failure-Message-and-Output'},
            failure_message="failure message", failure_output="I failed!")

    def test_init_error_message(self):
        tc = TestCase('Error-Message')
        tc.add_error_info("error message")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Error-Message'},
            error_message="error message")

    def test_init_error_output(self):
        tc = TestCase('Error-Output')
        tc.add_error_info(output="I errored!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Error-Output'}, error_output="I errored!")

    def test_init_error(self):
        tc = TestCase('Error-Message-and-Output')
        tc.add_error_info("error message", "I errored!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Error-Message-and-Output'},
            error_message="error message", error_output="I errored!")

    def test_init_skipped_message(self):
        tc = TestCase('Skipped-Message')
        tc.add_skipped_info("skipped message")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Skipped-Message'},
            skipped_message="skipped message")

    def test_init_skipped_output(self):
        tc = TestCase('Skipped-Output')
        tc.add_skipped_info(output="I skipped!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Skipped-Output'},
            skipped_output="I skipped!")

    def test_init_skipped_err_output(self):
        tc = TestCase('Skipped-Output')
        tc.add_skipped_info(output="I skipped!")
        tc.add_error_info(output="I skipped with an error!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0],
            {'name': 'Skipped-Output'},
            skipped_output="I skipped!",
            error_output="I skipped with an error!")

    def test_init_skipped(self):
        tc = TestCase('Skipped-Message-and-Output')
        tc.add_skipped_info("skipped message", "I skipped!")
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Skipped-Message-and-Output'},
            skipped_message="skipped message", skipped_output="I skipped!")

    def test_init_legal_unicode_char(self):
        tc = TestCase('Failure-Message')
        tc.add_failure_info(
            u("failure message with legal unicode char: [\x22]"))
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Failure-Message'}, failure_message=u(
                "failure message with legal unicode char: [\x22]"))

    def test_init_illegal_unicode_char(self):
        tc = TestCase('Failure-Message')
        tc.add_failure_info(
            u("failure message with illegal unicode char: [\x02]"))
        (ts, tcs) = serialize_and_read(TestSuite('test', [tc]))[0]
        verify_test_case(
            self, tcs[0], {'name': 'Failure-Message'}, failure_message=u(
                "failure message with illegal unicode char: []"))

    def test_init_utf8(self):
        tc = TestCase('Test äöü', 'some.class.name.äöü', 123.345, 'I am stdöüt!', 'I am stdärr!')
        tc.add_skipped_info(message='Skipped äöü', output="I skippäd!")
        tc.add_error_info(message='Skipped error äöü', output="I skippäd with an error!")
        test_suite = TestSuite('Test UTF-8', [tc])
        (ts, tcs) = serialize_and_read(test_suite, encoding='utf-8')[0]
        verify_test_case(self, tcs[0], {'name': 'Test äöü'.decode('utf-8'),
                                        'classname': 'some.class.name.äöü'.decode('utf-8'),
                                        'time': ("%f" % 123.345)},
                        stdout='I am stdöüt!'.decode('utf-8'), stderr='I am stdärr!'.decode('utf-8'),
                        skipped_message='Skipped äöü'.decode('utf-8'),
                        skipped_output="I skippäd!".decode('utf-8'),
                        error_message='Skipped error äöü'.decode('utf-8'),
                        error_output="I skippäd with an error!".decode('utf-8'))

    def test_init_unicode(self):
        tc = TestCase('Test äöü'.decode('utf-8'), 'some.class.name.äöü'.decode('utf-8'), 123.345,
                      'I am stdöüt!'.decode('utf-8'), 'I am stdärr!'.decode('utf-8'))
        tc.add_skipped_info(message='Skipped äöü'.decode('utf-8'),
                            output="I skippäd!".decode('utf-8'))
        tc.add_error_info(message='Skipped error äöü'.decode('utf-8'),
                          output="I skippäd with an error!".decode('utf-8'))

        (ts, tcs) = serialize_and_read(TestSuite('Test Unicode',
                                                 [tc]))[0]
        verify_test_case(self, tcs[0], {'name': 'Test äöü'.decode('utf-8'),
                                        'classname': 'some.class.name.äöü'.decode('utf-8'),
                                        'time': ("%f" % 123.345)},
                        stdout='I am stdöüt!'.decode('utf-8'), stderr='I am stdärr!'.decode('utf-8'),
                        skipped_message='Skipped äöü'.decode('utf-8'),
                        skipped_output="I skippäd!".decode('utf-8'),
                        error_message='Skipped error äöü'.decode('utf-8'),
                        error_output="I skippäd with an error!".decode('utf-8'))


def verify_test_case(tc, test_case_element, expected_attributes,
                     error_message=None, error_output=None,
                     failure_message=None, failure_output=None,
                     skipped_message=None, skipped_output=None,
                     stdout=None, stderr=None):
    for k, v in expected_attributes.items():
        tc.assertEqual(v, test_case_element.attributes[k].value)

    for k in test_case_element.attributes.keys():
        tc.assertTrue(k in expected_attributes.keys())

        if stderr:
            tc.assertEqual(
                stderr, test_case_element.getElementsByTagName(
                    'system-err')[0].firstChild.nodeValue.strip())
        if stdout:
            tc.assertEqual(
                stdout, test_case_element.getElementsByTagName(
                    'system-out')[0].firstChild.nodeValue.strip())

        errors = test_case_element.getElementsByTagName('error')
        if error_message or error_output:
            tc.assertTrue(len(errors) > 0)
        else:
            tc.assertEqual(0, len(errors))

        if error_message:
            tc.assertEqual(
                error_message, errors[0].attributes['message'].value)

        if error_output:
            tc.assertEqual(
                error_output, errors[0].firstChild.nodeValue.strip())

        failures = test_case_element.getElementsByTagName('failure')
        if failure_message or failure_output:
            tc.assertTrue(len(failures) > 0)
        else:
            tc.assertEqual(0, len(failures))

        if failure_message:
            tc.assertEqual(
                failure_message, failures[0].attributes['message'].value)

        if failure_output:
            tc.assertEqual(
                failure_output, failures[0].firstChild.nodeValue.strip())

        skipped = test_case_element.getElementsByTagName('skipped')
        if skipped_message or skipped_output:
            tc.assertTrue(len(skipped) > 0)
        else:
            tc.assertEqual(0, len(skipped))

if __name__ == '__main__':
    unittest.main()
