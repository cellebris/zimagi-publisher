from systems.commands.index import CommandMixin
from utility.data import get_identifier
from utility.topics import TopicModel
from utility.crawler import WebCrawler


class TeamMediaCollectorCommandMixin(CommandMixin("team_media_collector")):

    def save_media_collection(self, event, portal_name):
        topic_parser = TopicModel()
        team = self._team.qs.get(portal_name=portal_name, external_id=event.team_id)
        media_collection = self.save_instance(
            self._team_media_collection,
            None,
            {
                "team": team,
                "external_id": event.id,
                "name": event.name,
                "description": event.description,
                "access_teams": event.access_teams or [],
            },
        )
        media_index = {}

        for media_hash in media_collection.team_media.values_list("hash", flat=True):
            media_index[media_hash] = True

        def save_media(file_info):
            media_index.pop(file_info["hash"], None)

            media = self._team_media.filter(
                team_media_collection=media_collection,
                external_id=file_info["id"],
            )
            if not media:
                content = self.parse_file_content(portal_name, "media", file_info["id"])
                media = self.save_instance(
                    self._team_media,
                    None,
                    {
                        "team_media_collection_id": media_collection.id,
                        "external_id": file_info["id"],
                        "type": "file",
                        "name": file_info["name"],
                        "description": file_info["description"],
                        "hash": file_info["hash"],
                        "content": content,
                        "sentences": (
                            self.parse_sentences(
                                file_info["description"], validate=False
                            )
                            if file_info["description"]
                            else []
                        ),
                    },
                )
                if self._store_media_topics(media, topic_parser):
                    self.data(
                        "Media {} topics".format(self.key_color(media.id)),
                        media.topics,
                    )

                self._store_media_embeddings(media, topic_parser)
            else:
                media = media.first()
                media.name = file_info["name"]
                media.description = file_info["description"]
                media.save()

                if media.hash != file_info["hash"]:
                    media.content = self.parse_file_content(
                        portal_name, "media", file_info["id"]
                    )
                    media.sentences = (
                        self.parse_sentences(media.description, validate=False)
                        if media.description
                        else []
                    )
                    media.save()

                    if self._store_media_topics(media, topic_parser):
                        self.data(
                            "Media {} topics".format(self.key_color(media.id)),
                            media.topics,
                        )

                    self._store_media_embeddings(media, topic_parser)

        def save_media_bookmark(bookmark_info):
            content = self.parse_file_content(
                portal_name, "media_bookmark", bookmark_info["id"]
            )
            if not content:
                return

            hash_value = get_identifier(content)
            media_index.pop(hash_value, None)

            media = self._team_media.filter(
                team_media_collection=media_collection,
                external_id=bookmark_info["id"],
            )
            if not media:
                media = self.save_instance(
                    self._team_media,
                    None,
                    {
                        "team_media_collection_id": media_collection.id,
                        "external_id": bookmark_info["id"],
                        "type": "bookmark",
                        "name": bookmark_info["url"],
                        "description": bookmark_info["description"],
                        "hash": hash_value,
                        "content": content,
                        "sentences": (
                            self.parse_sentences(
                                bookmark_info["description"], validate=False
                            )
                            if bookmark_info["description"]
                            else []
                        ),
                    },
                )
                if self._store_media_topics(media, topic_parser):
                    self.data(
                        "Bookmark {} topics".format(self.key_color(media.id)),
                        media.topics,
                    )

                self._store_media_embeddings(media, topic_parser)
            else:
                media = media.first()
                media.name = bookmark_info["url"]
                media.description = bookmark_info["description"]
                media.sentences = (
                    self.parse_sentences(media.description, validate=False)
                    if media.description
                    else []
                )
                media.save()

                if media.hash != hash_value:
                    media.content = content
                    media.save()

                if self._store_media_topics(media, topic_parser):
                    self.data(
                        "Bookmark {} topics".format(self.key_color(media.id)),
                        media.topics,
                    )

                self._store_media_embeddings(media, topic_parser)

        self.run_list(event.get("files", []), save_media)
        self.run_list(event.get("bookmarks", []), save_media_bookmark)
        if media_index:
            for media in self._team_media.filter(
                team_media_collection=media_collection,
                hash__in=list(media_index.keys()),
            ):
                self._remove_media_embeddings(media)
                media.delete()

        self._publish_media_update_time(event, portal_name)
        return media_collection

    def delete_media_collection(self, event, portal_name):
        for collection in self._team_media_collection.filter(
            team__portal_name=portal_name,
            team__external_id=event.team_id,
            external_id=event.id,
        ):
            for media in collection.team_media.all():
                self._remove_media_embeddings(media)
            collection.delete()

    def _store_media_embeddings(self, media, topic_parser):
        qdrant = self.qdrant("team_media")
        self._remove_media_embeddings(media)

        if media.description:
            data = self.generate_text_embeddings(media.description)
            if data:
                for sentence_index, sentence in enumerate(data.sentences):
                    qdrant.store(
                        media.team_media_collection.team.id,
                        media.team_media_collection.id,
                        media.id,
                        sentence,
                        data.embeddings[sentence_index],
                        topic_parser.parse(sentence),
                        float(sentence_index),
                    )

    def _remove_media_embeddings(self, media):
        qdrant = self.qdrant("team_media")
        qdrant.remove(media_id=media.id)

    def _store_media_topics(self, media, topic_parser):
        if (not media.topics) and media.sentences:
            media.topics = topic_parser.get_index(*media.sentences)
            media.save()
            return True
        return False

    def _publish_media_update_time(self, event, portal_name):
        self.portal_update(
            portal_name, "media_collection", id=event.id, processed_time=self.time.now
        )
