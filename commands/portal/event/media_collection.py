from systems.commands.index import Command


class MediaCollection(Command("portal.event.media_collection")):

    def exec(self):
        self.data(
            "Processing media collection update {} from {}".format(
                self.event_id, self.portal
            ),
            self.event_fields,
        )
        self.event_wrapper(self._update_media_collection)

    def _update_media_collection(self, event):
        if event.operation == "delete":
            self.delete_media_collection(event, self.portal)
            self.send("agent:media:delete", event.export())
            self.success("Successfully deleted media collection: {}".format(event.id))
        else:
            self.save_media_collection(event, self.portal)
            self.send("agent:media:update", event.export())
            self.success("Updated media collection".format(event.id))
