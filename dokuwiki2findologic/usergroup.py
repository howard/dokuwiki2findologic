from fnmatch import fnmatch
import hashlib


class Role(object):
    def __init__(self, name, salt, permission_file_lines):
        self.name = name
        self.restricted_patterns = []
        self.__generate_hash(salt)
        self.__parse_permissions(permission_file_lines)

    def __generate_hash(self, salt):
        salted_name = (self.name + salt).encode('utf-8')
        self.usergroup_hash = hashlib.sha512(salted_name).hexdigest()

    def __parse_permissions(self, permission_file_lines):
        for line in permission_file_lines:
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            pattern, role, permission = parts
            # Remove leading '@' from role name and parse permission digit.
            role = role[1:]
            permission = int(permission)
            # TODO: Figure out how to translate ACL rules into something usable.

    def can_access(self, page_path):
        for restricted_pattern in self.restricted_patterns:
            if fnmatch(page_path, restricted_pattern):
                return False
        return True


def parse_role_names(users_lines):
    roles = set()
    for line in users_lines:
        roles_string = line.split(':')[-1]
        for role in roles_string.split(','):
            roles.add(role)
    return roles


def discover_roles(dokuwiki_path, usergroup_hash_salt):
    with open(dokuwiki_path + '/conf/users.auth.php', 'r') as users_file:
        role_names = parse_role_names(users_file.readlines())
    with open(dokuwiki_path + '/conf/acl.auth.php', 'r') as acl_file:
        permission_file_lines = acl_file.readlines()
    return [Role(role_name, usergroup_hash_salt, permission_file_lines)
            for role_name in role_names]
