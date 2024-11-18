from systems.commands.index import Agent
from utility.filesystem import load_file


class Assistant(Agent('assistant')):

    def exec(self):
        input_channel = 'agent:publish'

        for package in self.listen(input_channel):
            try:
                self.data('Processing assistance request', package.sender)
                response = self.profile(self._process_assistant, package.message)
                self.send(package.sender, response.result)

            except Exception as e:
                self.send(input_channel, package.message, package.sender)
                raise e

            self.send(f"{input_channel}:stats", {
                'data_dir': self.data_dir,
                'message': package.message,
                'time': response.time,
                'memory': response.memory
            })

    def _process_assistant(self, message):
        project_id = message['project_id']
        topic = message['topic']

        instructions = load_file(f"{self.data_dir}/README.md")

        print(self.data_dir)
        print(project_id)
        print(topic)
        print(instructions)

        return {}
