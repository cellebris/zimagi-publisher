from systems.commands.index import Agent
from utility.filesystem import load_file


class Editor(Agent('editor')):

    def exec(self):
        input_channel = 'agent:form_submissions:update'

        for package in self.listen(input_channel, state_key = 'publisher_editor'):
            print(package)
            print(package.message)

            if package.message['name'] == 'user-search':
                try:
                    self.data('Processing user query', package.sender)
                    response = self.profile(self._edit_page, package.message)

                except Exception as e:
                    self.send(input_channel, package.message, package.sender)
                    raise e

                self.send(f"{input_channel}:stats", {
                    'data_dir': self.data_dir,
                    'message': package.message,
                    'time': response.time,
                    'memory': response.memory
                })

    def _edit_page(self, message):
        instructions = load_file(f"{self.data_dir}/README.md")

        print(self.data_dir)
        print(message)
        print(instructions)

        for metadata in self.collect('agent:publish', message, timeout = 60, quantity = 10):
            print(metadata)
