from django.conf import settings

from systems.commands.index import CommandMixin
from utility.data import load_yaml
from utility.git import Git

import re


class PublisherCommandMixin(CommandMixin('publisher')):

  def sync_interface(self):
    is_repository = Git.check(settings.MANAGER.publisher_interface)

    if settings.INTERFACE_REPO_REMOTE:
      if not is_repository:
        repository = Git.clone(
          settings.INTERFACE_REPO_REMOTE,
          settings.MANAGER.publisher_interface,
          reference = settings.INTERFACE_REPO_REFERENCE,
          **self._git_auth()
        )
        self.success("Initialized interface repository from remote")
      else:
        repository = Git(
            settings.MANAGER.publisher_interface,
            user = self.active_user,
            **self._git_auth()
        )
        repository.set_remote('origin', settings.INTERFACE_REPO_REMOTE)
        repository.pull(
            remote = 'origin',
            branch = settings.INTERFACE_REPO_REFERENCE
        )
        self.success("Updated interface repository from remote")

  def _git_auth(self):
    return {
      'username': settings.INTERFACE_REPO_USER,
      'password': settings.INTERFACE_REPO_PASSWORD,
      'public_key': settings.INTERFACE_REPO_PUBLIC_KEY,
      'private_key': settings.INTERFACE_REPO_PRIVATE_KEY
    }


  def generate_data(self, project_id, prompt, max_sections = 5, sentence_limit = 50, retries = 3):
    summary = self.generate_project_summary(
        self._team_project.retrieve_by_id(project_id),
        prompt,
        use_default_format = True,
        output_format = 'Generate the response in YAML between [yaml] and [/yaml] tags.',
        output_endings = ['[/yaml]'],
        max_sections = max_sections,
        sentence_limit = sentence_limit
    )
    yaml_data = re.search('\[yaml\](.*)\[/yaml\]', summary.text, re.DOTALL)
    if not yaml_data:
        if retries > 0:
            return self.generate_data(
                project_id,
                prompt,
                max_sections = max_sections,
                sentence_limit = sentence_limit,
                retries = (retries - 1)
            )
        return None

    return load_yaml(yaml_data.group(1).strip())
