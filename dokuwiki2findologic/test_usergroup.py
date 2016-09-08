import unittest

import dokuwiki2findologic.usergroup as usergroup


class TestUsergroupHashing(unittest.TestCase):
    def test_hash_is_salted_sha512(self):
        salt = 'test'
        role = 'coconuts'
        # Reference hash was generated manually to avoid test and live code
        # being essentially the same.
        expected_hash = 'efbc4c71dae37f053f0a370cd59144730b0248ef283f5fe081' + \
                        'e4eab97292db69cb72348447910a0ae772c5653a79bbb01440' + \
                        'b7bcdfd6213247660699aec85eb8'
        role = usergroup.Role(role, salt, [])
        self.assertEqual(expected_hash, role.usergroup_hash)

    def test_roles_are_discovered(self):
        role_lines = [
            'user:MD5password:Real Name:email:groups,comma,separated',
            'user:MD5password:Real Name:email:some,more,groups',
            'user:MD5password:Real Name:email:just_one'
        ]
        expected_roles = {
            'groups', 'comma', 'separated', 'some', 'more', 'just_one'
        }
        actual_roles = usergroup.parse_role_names(role_lines)
        self.assertEqual(expected_roles, actual_roles)
