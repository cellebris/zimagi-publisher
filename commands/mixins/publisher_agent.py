from django.conf import settings

from systems.commands.index import CommandMixin
from utility.filesystem import load_file
from utility.data import load_yaml


class PublisherAgentCommandMixin(CommandMixin('publisher_agent')):

    def exec(self):
        input_channel = 'agent:publish'

        for package in self.listen(input_channel):
            try:
                self.data('Processing publishing request', package.sender)
                response = self.profile(self._publish_component, package.message)
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

    def _publish_component(self, message):
        instructions = load_file(f"{self.data_dir}/README.md")

        print(self.data_dir)
        print(message['project_id'])
        print(message['topic'])
        print(instructions)

        #
        # Return most relevant component
        # If no relevant components then generate component
        #

        #
        # Prompt should combine:
        #
        # 1. instructions
        # 2. topic
        #
        return self.generate_data(
            message['project_id'],
            f"Generate a web component for '{message['topic']}' using the following instructions: {instructions}",
            max_sections = message.get('max_sections', 5),
            sentence_limit = message.get('sentence_limit', 50)
        )