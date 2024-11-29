from systems.commands.index import Command


class FormEmbedding(Command("portal.event.form_embedding")):

    def exec(self):
        self.data(
            "Processing form embedding request {} from {}".format(
                self.event_id, self.portal
            ),
            self.event_fields,
        )
        self.event_wrapper(self._generate_form_embedding)

    def _generate_form_embedding(self, event):
        if event.operation != "delete":
            search = self.generate_text_embeddings(event.text, validate=False)
            if search:
                self.portal_update(
                    self.portal,
                    "embedding",
                    event.id,
                    embeddings=search.embeddings,
                )
                self.send(
                    "agent:form_embeddings:generate",
                    {
                        **event.export(),
                        "portal_name": self.portal,
                        "embeddings": search.embeddings,
                    },
                )
            self.success("Successfully generated form embedding: {}".format(event.id))
