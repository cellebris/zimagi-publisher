from systems.plugins.index import BaseProvider


class Provider(BaseProvider("qdrant_collection", "team_media")):

    def _get_index_fields(self):
        return {
            "team_id": "keyword",
            "collection_id": "keyword",
            "media_id": "keyword",
            "topics": "keyword",
        }

    def _get_media_id_filters(self, team_id=None, collection_id=None, media_id=None):
        from qdrant_client import models

        filters = []

        if team_id:
            filters.append(self._get_query_id_condition("team_id", team_id))
        if collection_id:
            filters.append(self._get_query_id_condition("collection_id", collection_id))
        if media_id:
            filters.append(self._get_query_id_condition("media_id", media_id))

        return models.Filter(must=filters) if filters else None

    def count(self, team_id=None, collection_id=None, media_id=None):
        return self._get_count_query(
            self._get_media_id_filters(team_id, collection_id, media_id)
        )

    def exists(self, team_id=None, collection_id=None, media_id=None):
        return self._check_exists(
            self._get_media_id_filters(team_id, collection_id, media_id)
        )

    def get(
        self,
        team_id=None,
        collection_id=None,
        media_id=None,
        fields=None,
        include_vectors=False,
    ):
        return self._run_query(
            self._get_media_id_filters(team_id, collection_id, media_id),
            fields=fields,
            include_vectors=include_vectors,
        )

    def store(self, team_id, collection_id, media_id, sentence, embedding, topics):
        return self.request_upsert(
            collection_name=self.name,
            points=[
                self._get_record(
                    sentence,
                    embedding,
                    team_id=team_id,
                    collection_id=collection_id,
                    media_id=media_id,
                    topics=topics,
                )
            ],
        )

    def remove(self, team_id=None, collection_id=None, media_id=None):
        return self.request_delete(
            collection_name=self.name,
            points_selector=self._get_media_id_filters(
                team_id, collection_id, media_id
            ),
        )
