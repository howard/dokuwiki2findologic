from fnmatch import fnmatch
import hashlib


class Role(object):
    """
    DokuWiki user role. Allows checking for visibility and generating a
    usergroup hash.
    """

    def __init__(self, name, salt, permission_file_lines):
        """
        :param name: Name of the role.
        :param salt: Appended to the name of the role when generating a
            usergroup hash.
        :param permission_file_lines: Lines of DokuWiki's acl.auth.php file.
        """
        self.name = name
        self.rules = []
        self.__generate_hash(salt)
        self.__parse_permissions(permission_file_lines)

    def __generate_hash(self, salt):
        """
        :param salt: Appended to the name of the role when generating a
            usergroup hash.
        :return: The hashed usergroup as a lowercase hex digest.
        """
        salted_name = (self.name + salt).encode('utf-8')
        self.usergroup_hash = hashlib.sha512(salted_name).hexdigest()

    def __parse_permissions(self, permission_file_lines):
        """
        Reads all access rules from the permissions that affect the role. They
        are stored in sequence, so they can be applied to page paths in
        Role.can_access().

        :param permission_file_lines: Lines of DokuWiki's acl.auth.php file.
        """
        for line in permission_file_lines:
            parts = line.split('\t')
            # Skip non-standard lines.
            if len(parts) != 3:
                continue
            pattern, role, permission = parts
            # Remove leading '@' from role name and parse permission digit.
            role = role[1:]
            permission = int(permission)
            # Skip rules that don't apply to this role.
            if role != self.name and role != 'ALL':
                continue
            # Save the rule for matching it later.
            self.rules.append({
                'pattern': pattern,
                'permission': permission
            })

    def can_access(self, page_path):
        """
        Checks if users with this role can access the page specified by its
        path. To achieve that, the ACL rules whose patterns match the path are
        applied in sequence. Whichever permission is applied last, is used.

        :param page_path: Path to the check for which accessiblity should be
            checked.
        :return: Accessibility of the page.
        """
        permission = 1
        for rule in self.rules:
            if fnmatch(page_path, rule['pattern']):
                permission = rule['permission']
        return permission > 0


def parse_role_names(users_lines):
    """
    Extracts and sanitizes the available role names from the user configuration.

    :param users_lines: List of the user configuration's lines.
    :return: The set containing all available role names.
    """
    roles = set()
    for line in users_lines:
        parts = line.split(':')
        # Skip non-standard lines.
        if len(parts) != 5:
            continue
        roles_string = parts[-1]
        for role in roles_string.split(','):
            roles.add(role.strip())
    return roles


def discover_roles(dokuwiki_path, usergroup_hash_salt):
    """
    Reads DokuWiki ACL and user configuration and constructs role objects based
    on the available roles.

    :param dokuwiki_path: Path to the DokuWiki base directory.
    :param usergroup_hash_salt: Salt that is appended to the usergroup name
        before hashing it. Must be a string.
    :return: List of role objects for all available roles.
    """
    with open(dokuwiki_path + '/conf/users.auth.php', 'r') as users_file:
        role_names = parse_role_names(users_file.readlines())
    with open(dokuwiki_path + '/conf/acl.auth.php', 'r') as acl_file:
        permission_file_lines = acl_file.readlines()
    return [Role(role_name, usergroup_hash_salt, permission_file_lines)
            for role_name in role_names]
