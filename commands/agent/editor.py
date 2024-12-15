from sklearn.metrics.pairwise import cosine_similarity

from systems.commands.index import Agent
from utility.filesystem import load_file

import re
import numpy


class Editor(Agent("editor")):

    def exec(self):
        for package in self.listen(
            self.publish_channel, state_key=self.publish_channel_key
        ):
            if package.message["name"] == "user-search" and not package.message["page"]:
                try:
                    self.data("Processing user query", package.sender)
                    response = self.profile(self._edit_page, package.message)

                except Exception as e:
                    self.send(self.publish_channel, package.message, package.sender)
                    raise e

                self.send(
                    f"{self.publish_channel}:stats",
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
        query = message["fields"]["user-query"]
        nav_path = None

        matches = re.search(r"^\/([a-z]+)\s+([^:]+)\s*:\s*(.+)$", query)
        if matches:
            command = matches.group(1)
            parameters = matches.group(2)
            message["fields"]["user-query"] = matches.group(3)

            if command == "page":
                nav_path = parameters
                message["nav_path"] = nav_path

        component_queries = []
        query_embeddings = []
        for project in self.search_projects(
            message["portal_name"], message["fields"]["user-query"]
        ):
            for query in self.generate_queries(
                message["fields"]["user-query"], message["portal_name"], project.id
            ):
                query_info = self.generate_text_embeddings(query, validate=False)
                component_queries.extend(query_info.sentences)
                query_embeddings.extend(query_info.embeddings)

        similarity_matrix = list(cosine_similarity(numpy.array(query_embeddings)))
        remove_indexes = []

        print(similarity_matrix)
        for index, query in enumerate(component_queries):
            print(f"{index}: {query}")

        for index, scores in enumerate(similarity_matrix):
            scores = list(scores)

            if scores[0] < 1 and scores[0] >= 0.9:
                similarity_matrix.pop(index)
                remove_indexes.append(index)
            else:
                for inner_index, score in enumerate(scores):
                    if score < 1 and score >= 0.9:
                        scores.pop(inner_index)
                        remove_indexes.append(inner_index)

                similarity_matrix[index] = scores

        publish_jobs = [
            {"channel": "agent:publish", "query": message["fields"]["user-query"]},
            {
                "channel": "agent:publish_component",
                "query": message["fields"]["user-query"],
            },
        ]
        for query in component_queries:
            publish_jobs.append({"channel": "agent:publish_component", "query": query})

        print(publish_jobs)

        for index, query in enumerate(component_queries):
            print(f"{index}: {query}")

        for scores in similarity_matrix:
            print(scores)

        exit()
        for component_info in self.collect(
            "agent:publish", message, timeout=180, quantity=10
        ):
            print("---------------------")
            print(component_info)
