# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


"""
Test class for Host Group UI
"""

from ddt import ddt
from ddt import data as ddt_data
from robottelo.common.decorators import data, skip_if_bug_open
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_loc, make_hostgroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Hostgroup(UITestCase):
    """
    Implements HostGroup tests from UI
    """

    org_name = None
    loc_name = None

    def setUp(self):
        super(Hostgroup, self).setUp()
        #  Make sure to use the Class' org_name instance
        if (Hostgroup.org_name is None and Hostgroup.loc_name is None):
            Hostgroup.org_name = generate_string("alpha", 8)
            Hostgroup.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Hostgroup.org_name)
                make_loc(session, name=Hostgroup.loc_name)

    @data(*generate_strings_list(len1=4))
    def test_create_hostgroup(self, name):
        """
        @Test: Create new hostgroup
        @Feature: Hostgroup - Positive Create
        @Assert: Hostgroup is created
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))

    @skip_if_bug_open('bugzilla', 1121755)
    @skip_if_bug_open('bugzilla', 1131416)
    @data(*generate_strings_list(len1=4))
    def test_delete_hostgroup(self, name):
        """
        @Test: Delete a hostgroup
        @Feature: Hostgroup - Positive Delete
        @Assert: Hostgroup is deleted
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            self.hostgroup.delete(name, really=True)
            self.assertIsNone(self.hostgroup.search(name))

    @skip_if_bug_open('bugzilla', 1121755)
    @data({u'name': generate_string('alpha', 10),
           u'new_name': generate_string('alpha', 10)},
          {u'name': generate_string('latin1', 10),
           u'new_name': generate_string('latin1', 10)},
          {u'name': generate_string('numeric', 10),
           u'new_name': generate_string('numeric', 10)},
          {u'name': generate_string('html', 10),
           u'new_name': generate_string('html', 10)},
          {u'name': generate_string('utf8', 10),
           u'new_name': generate_string('utf8', 10)},
          {u'name': generate_string('alphanumeric', 255),
           u'new_name': generate_string('alphanumeric', 255)})
    def test_update_hostgroup(self, test_data):
        """
        @Test: Update hostgroup with a new name
        @Feature: Hostgroup - Positive Update
        @Assert: Hostgroup is updated
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=test_data['name'])
            self.assertIsNotNone(self.hostgroup.search(test_data['name']))
            self.hostgroup.update(test_data['name'],
                                  new_name=test_data['new_name'])
            self.assertIsNotNone(self.hostgroup.search(test_data['new_name']))

    @data(*generate_strings_list(len1=256))
    def test_negative_create_hostgroup_1(self, name):
        """
        @Test: Create new hostgroup with 256 chars in name
        @Feature: Hostgroup - Negative Create
        @Assert: Hostgroup is not created
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))
            self.assertIsNone(self.hostgroup.search(name))

    @data(*generate_strings_list(len1=6))
    def test_negative_create_hostgroup_2(self, name):
        """
        @Test: Create new hostgroup with same name
        @Feature: Hostgroup - Negative Create
        @Assert: Hostgroup is not created
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))

    @ddt_data({u'name': ""},
              {u'name': "  "})
    def test_negative_create_hostgroup_3(self, test_data):
        """
        @Test: Create new hostgroup with whitespaces in name
        @Feature: Hostgroup - Negative Create
        @Assert: Hostgroup is not created
        """

        with Session(self.browser) as session:
            make_hostgroup(session, name=test_data['name'])
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators["name_haserror"]))
