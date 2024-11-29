from systems.plugins.index import BaseProvider


class Provider(BaseProvider("qdrant_collection", "web_component")):

    def _get_index_fields(self):
        return {"type": "keyword", "name": "keyword", "topics": "keyword"}

    def _get_component_id_filters(self, type=None, name=None):
        from qdrant_client import models

        filters = []

        if type:
            filters.append(self._get_query_id_condition("type", type))
        if name:
            filters.append(self._get_query_id_condition("name", name))

        return models.Filter(must=filters) if filters else None

    def count(self, type=None, name=None):
        return self._get_count_query(self._get_component_id_filters(type, name))

    def exists(self, type=None, name=None):
        return self._check_exists(self._get_component_id_filters(type, name))

    def get(
        self,
        type=None,
        name=None,
        fields=None,
        include_vectors=False,
    ):
        return self._run_query(
            self._get_component_id_filters(type, name),
            fields=fields,
            include_vectors=include_vectors,
        )

    def store(self, type, name, text, embedding, topics):
        return self.request_upsert(
            collection_name=self.name,
            points=[
                self._get_record(
                    text,
                    embedding,
                    type=type,
                    name=name,
                    topics=topics,
                )
            ],
        )

    def remove(self, type=None, name=None):
        return self.request_delete(
            collection_name=self.name,
            points_selector=self._get_component_id_filters(type, name),
        )
