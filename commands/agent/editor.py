from systems.commands.index import Agent
from utility.filesystem import load_file


class Editor(Agent("editor")):

    def exec(self):
        input_channel = "agent:form_submissions:update"

        for package in self.listen(input_channel, state_key="publisher_editor"):
            if package.message["name"] == "user-search" and not package.message["page"]:
                try:
                    self.data("Processing user query", package.sender)
                    response = self.profile(self._edit_page, package.message)

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

    def _edit_page(self, message):
        instructions = load_file(f"{self.data_path}/README.md")
        portal_name = message["portal_name"]
        project_id = message["fields"]["search-project"]
        query = message["fields"]["user-query"]

        for metadata in self.collect(
            "agent:publish", message, timeout=180, quantity=10
        ):
            print("---------------------")
            print(metadata)
