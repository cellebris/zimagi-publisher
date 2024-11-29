from django.conf import settings

from systems.commands.index import CommandMixin
from utility.data import load_yaml
from utility.filesystem import load_file, save_yaml
from utility.git import Git
from utility.topics import TopicModel

from bs4 import BeautifulSoup
import os
import re


class PublisherCommandMixin(CommandMixin("publisher")):

    @property
    def data_path(self):
        return f"{settings.MANAGER.publisher_interface}/{self.data_dir}"

    @property
    def max_component_generation_score(self):
        return self.get_config("publisher_max_component_generation_score", 0.75)

    @property
    def max_component_score(self):
        return self.get_state("publisher_max_component_score", 0)

    def update_max_component_score(self, value):
        def save_max_value():
            self.set_state(
                "publisher_max_component_score",
                max(value, self.max_component_score),
            )

        self.run_exclusive("publisher_max_component_score", save_max_value)

    def sync_interface(self):
        is_repository = Git.check(settings.MANAGER.publisher_interface)

        if settings.INTERFACE_REPO_REMOTE:
            if not is_repository:
                repository = Git.clone(
                    settings.INTERFACE_REPO_REMOTE,
                    settings.MANAGER.publisher_interface,
                    reference=settings.INTERFACE_REPO_REFERENCE,
                    **self._git_auth(),
                )
                self.success("Initialized interface repository from remote")
            else:
                repository = Git(
                    settings.MANAGER.publisher_interface,
                    user=self.active_user,
                    **self._git_auth(),
                )
                repository.set_remote("origin", settings.INTERFACE_REPO_REMOTE)
                repository.pull(
                    remote="origin", branch=settings.INTERFACE_REPO_REFERENCE
                )
                self.success("Updated interface repository from remote")

    def _git_auth(self):
        return {
            "username": settings.INTERFACE_REPO_USER,
            "password": settings.INTERFACE_REPO_PASSWORD,
            "public_key": settings.INTERFACE_REPO_PUBLIC_KEY,
            "private_key": settings.INTERFACE_REPO_PRIVATE_KEY,
        }

    def generate_data(
        self,
        portal_name,
        project_id,
        prompt,
        max_sections=5,
        sentence_limit=50,
        retries=0,
    ):
        summary = self.generate_project_summary(
            self._team_project.retrieve(project_id, team__portal_name=portal_name),
            prompt,
            use_default_format=False,
            output_format="Generate the data object in YAML format like the following examples and end the response with the [end] tag.",
            output_endings=["[end]"],
            max_sections=max_sections,
            sentence_limit=sentence_limit,
        )
        yaml_data = re.search("(.*)\[end\]", summary.text, re.DOTALL)
        if not yaml_data:
            if retries > 0:
                return self.generate_data(
                    portal_name,
                    project_id,
                    prompt,
                    max_sections=max_sections,
                    sentence_limit=sentence_limit,
                    retries=(retries - 1),
                )
            return None
        return load_yaml(yaml_data.group(1).strip())

    def generate_component(self, query, portal_name, project_id):
        instructions = load_file(f"{self.data_path}/README.md")
        examples = self.get_component_examples(query, count=3)

        component_prompt = [
            "Generate a web component data card for the query or topic: '{}'".format(
                query
            ),
            "Adhere to the following instructions written in markdown when creating the data card:\n\n{}".format(
                instructions
            ),
            "Use the following YAML data cards as examples when generating a new data card:\n\nFirst data card example:\n\n{}".format(
                "\n\nNext data card example:\n\n".join(examples)
            ),
        ]
        return self.generate_data(
            portal_name,
            project_id,
            "\n\n".join(component_prompt),
            sentence_limit=50,
            max_sections=5,
        )

    def generate_path(self, component, retries=3):
        component_statements = self._collect_component_statements(component)
        path_name = None
        index = 0

        while not path_name:
            summary = self.generate_summary(
                "The following are examples of current path names for data components:\n\n{}".format(
                    ",\n".join(self.get_component_names())
                ),
                provider="mixtral_7bx8",
                prompt="Generate a single path name that does not exist in the example list consisting only of alpha-numeric characters, underscores, and forward slashes  that focuses on effective categorization to represent the following component information:\n\n{}".format(
                    "\n\n".join(component_statements)
                ),
                output_format="Answer with only the path name and place the path name between [start] and [end] tags",
                endings=["[end]", ".", "!"],
                retries=1,
                temperature=0.1,
                top_p=0.9,
                repetition_penalty=0.9,
            )

            path_name = re.search("\[start\](.*)\[end\]", summary.text)
            if path_name:
                path_name = path_name.group(1).strip()
            elif index < retries:
                index += 1
            else:
                break

        return path_name

    def save_component(self, component):
        path_name = self.generate_path(component, retries=3)
        if path_name:
            save_yaml("{}/{}.yaml".format(self.data_path, path_name), component)
        return path_name

    def search_components(self, search_text, sentence_limit=50, min_score=0.3):
        topic_parser = TopicModel()
        search_topics = topic_parser.parse(search_text)
        scores = {}
        components = []

        search = self.generate_text_embeddings(search_text, validate=False)
        sentence_rankings = self.search_embeddings(
            "web_component",
            search.embeddings,
            limit=sentence_limit,
            fields=["name", "topics"],
            filter_field="type",
            filter_ids=self.data_dir,
            min_score=min_score,
        )
        for index, ranking in enumerate(sentence_rankings):
            for ranking_index, sentence_info in enumerate(ranking):
                sentence = sentence_info.payload["sentence"].strip()
                type = sentence_info.payload["type"]
                name = sentence_info.payload["name"]
                topic_score = topic_parser.get_topic_score(
                    search_topics, sentence_info.payload["topics"]
                )

                if self.debug:
                    self.data(f"{type} {name}: {sentence}", sentence_info.score)

                if name not in scores:
                    scores[name] = {"count": 0, "score": 0}

                scores[name]["count"] += 1
                scores[name]["score"] += (1 + topic_score) * sentence_info.score

        for name, score_info in sorted(
            scores.items(), key=lambda x: x[1]["score"], reverse=True
        ):
            components.append({"name": name, "score": score_info["score"]})

        return components

    def get_component_examples(self, search_text, count=3, sentence_limit=50):
        components = []
        for component in self.search_components(
            search_text, sentence_limit=sentence_limit, min_score=0
        ):
            components.append(
                load_file(os.path.join(self.data_path, component["name"] + ".yaml"))
            )
            if len(components) == count:
                break

        return components

    def get_component_names(self):
        names = []

        def parse_directories(base_path):
            for file in os.listdir(base_path):
                path = os.path.join(base_path, file)
                if os.path.isdir(path):
                    yield from parse_directories(path)
                elif path.endswith(".yaml"):
                    yield path

        for component_file in parse_directories(self.data_path):
            names.append(
                component_file.replace("{}/".format(self.data_path), "").replace(
                    ".yaml", ""
                )
            )
        return names

    def save_component_embeddings(self):
        topic_parser = TopicModel()

        def parse_directories(base_path):
            for file in os.listdir(base_path):
                path = os.path.join(base_path, file)
                if os.path.isdir(path):
                    yield from parse_directories(path)
                elif path.endswith(".yaml"):
                    yield path

        for component_file in parse_directories(self.data_path):
            name = component_file.replace("{}/".format(self.data_path), "").replace(
                ".yaml", ""
            )
            component = load_yaml(load_file(component_file))
            self._store_component_embeddings(name, component, topic_parser)

    def save_component_embedding(self, name, component):
        self._store_component_embeddings(name, component)

    def _store_component_embeddings(self, name, component, topic_parser=None):
        statements = self._collect_component_statements(component)

        if not topic_parser:
            topic_parser = TopicModel()

        self._remove_component_embeddings(name)
        if statements:
            qdrant = self.qdrant("web_component")
            for statement in statements:
                data = self.generate_text_embeddings(statement, validate=False)
                if data:
                    for sentence_index, sentence in enumerate(data.sentences):
                        qdrant.store(
                            self.data_dir,
                            name,
                            sentence,
                            data.embeddings[sentence_index],
                            topic_parser.parse(sentence),
                        )

    def _remove_component_embeddings(self, name=None):
        qdrant = self.qdrant("web_component")
        qdrant.remove(type=self.data_dir, name=name)

    def _collect_component_statements(self, component, min_words=4):
        statements = []
        for key, value in component.items():
            if isinstance(value, dict):
                for sub_statement in self._collect_component_statements(
                    value, min_words
                ):
                    statements.append(sub_statement)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    for sub_statement in self._collect_component_statements(
                        item, min_words
                    ):
                        statements.append(sub_statement)
            elif (
                isinstance(value, str)
                and len(re.split(r"\s+", value.strip())) >= min_words
            ):
                soup = BeautifulSoup(value, features="html.parser")
                statements.append(soup.get_text())
        return statements
