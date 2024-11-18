from django.conf import settings

from settings.config import Config

#
# Interface path
#
# Usage: directory = settings.MANAGER.publisher_interface
#
settings.PROJECT_PATH_MAP['publisher_interface'] = {
  'directory': 'interface',
  'backup': False
}

#
# Interface Repository Configurations
#
INTERFACE_REPO_REMOTE = Config.string('ZIMAGI_INTERFACE_REPO_REMOTE', None)
INTERFACE_REPO_REFERENCE = Config.string('ZIMAGI_INTERFACE_REPO_REFERENCE', 'main')

INTERFACE_REPO_USER = Config.string('ZIMAGI_INTERFACE_REPO_USER', None)
INTERFACE_REPO_PASSWORD = Config.string('ZIMAGI_INTERFACE_REPO_PASSWORD', None)
INTERFACE_REPO_PUBLIC_KEY = Config.string('ZIMAGI_INTERFACE_REPO_PUBLIC_KEY', None)
INTERFACE_REPO_PRIVATE_KEY = Config.string('ZIMAGI_INTERFACE_REPO_PRIVATE_KEY', None)
