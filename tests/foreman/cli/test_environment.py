# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment  CLI
"""

from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.environment import Environment
from robottelo.common.helpers import generate_string
from robottelo.cli.factory import make_environment
from robottelo.test import MetaCLITestCase


class TestEnvironment(MetaCLITestCase):

    factory = make_environment
    factory_obj = Environment

    POSITIVE_CREATE_DATA = (
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10)},
        {'name': generate_string("numeric", 10)},
    )

    POSITIVE_UPDATE_DATA = (
        ({'name': generate_string("alpha", 10)},
         {'new-name': generate_string("alpha", 10)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("alphanumeric", 10)}),
        ({'name': generate_string("numeric", 10)},
         {'new-name': generate_string("numeric", 10)}),
    )

    NEGATIVE_UPDATE_DATA = (
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("alphanumeric", 300)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("latin1", 10)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("utf8", 10)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': generate_string("html", 6)}),
        ({'name': generate_string("alphanumeric", 10)},
         {'new-name': ""}),
    )

    POSITIVE_DELETE_DATA = (
        {'name': generate_string("alpha", 10)},
        {'name': generate_string("alphanumeric", 10)},
        {'name': generate_string("numeric", 10)},
    )

    def test_info(self):
        """
        @Feature: Environment - Info
        @Test: Test Environment Info
        @Assert: Environment Info is displayed
        """
        name = generate_string("alpha", 10)
        Environment().create({'name': name})
        result = Environment().info({'name': name})

        self.assertTrue(result.return_code == 0,
                        "Environment info - retcode")

        self.assertEquals(result.stdout['name'], name,
                          "Environment info - stdout contains 'Name'")

    def test_list(self):
        """
        @Feature: Environment - List
        @Test: Test Environment List
        @Assert: Environment List is displayed
        """
        name = generate_string("alpha", 10)
        Environment().create({'name': name})
        result = Environment().list({'search': name})
        self.assertTrue(len(result.stdout) == 1,
                        "Environment list - stdout contains 'Name'")

    def test_delete(self):
        """
        @Test: Delete the environment
        @Feature: Environment - Delete
        @Assert: Environment Delete is displayed
        """

        name = generate_string("alphanumeric", 10)
        try:
            make_environment({'name': name})
        except CLIFactoryError as err:
            self.fail(err)

        result = Environment().delete({'name': name})
        self.assertEqual(result.return_code, 0, "Deletion failed")
        self.assertEqual(
            len(result.stderr), 0, "There should not be an error here")

        result = Environment().info({'name': name})
        self.assertNotEqual(
            result.return_code, 0, "Environment should be deleted")
        self.assertGreater(len(result.stderr), 0,
                           "There should be an exception here")
