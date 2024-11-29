from systems.commands.index import CommandMixin
from utility.filesystem import load_file, save_yaml

import re


class PublisherAgentCommandMixin(CommandMixin("publisher_agent")):

    def exec(self):
        input_channel = "agent:publish"

        self.save_component_embeddings()

        for package in self.listen(input_channel):
            try:
                self.data("Processing publishing request", package.sender)
                response = self.profile(self._publish_component, package.message)
                if response.result:
                    self.send(package.sender, response.result)

            except Exception as e:
                self.send(input_channel, package.message, package.sender)
                raise e

            self.send(
                f"{input_channel}:stats",
                {
                    "data_dir": self.data_dir,
                    "message": package.message,
                    "time": response.time,
                    "memory": response.memory,
                },
            )

    def _publish_component(self, message):
        query = message["fields"]["user-query"]
        component_info = None

        components = self.search_components(
            query, sentence_limit=sentence_limit, min_score=0.3
        )
        if components:
            component_info = {
                "type": self.data_dir,
                "name": components[0]["name"],
                "score": components[0]["score"],
            }
            self.update_max_component_score(component_info["score"])

        normalized_score = (
            component_info["score"] / self.max_component_score if component_info else 0
        )

        if True:  # normalized_score <= self.max_component_generation_score:
            component = self.generate_component(
                query, message["portal_name"], message["fields"]["search-project"]
            )
            component_info = {
                "type": self.data_dir,
                "name": self.save_component(component),
                "score": 0,
            }
        return component_info
