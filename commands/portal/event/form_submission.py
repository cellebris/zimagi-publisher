from systems.commands.index import Command


class FormSubmission(Command('portal.event.form_submission')):

    def exec(self):
        self.data("Processing form submission {} from {}".format(self.event_id, self.portal), self.event_fields)
        self.event_wrapper(self._update_form_submission)

    def _update_form_submission(self, event):
        if event.operation == 'delete':
            self._form_submission.filter(
                portal_name = self.portal,
                external_id = event.id
            ).delete()

            self.send('agent:form_submissions:delete', event.export())
            self.success("Successfully deleted form submission: {}".format(event.id))
        else:
            self.save_instance(self._form_submission, None, {
                'portal_name': self.portal,
                'external_id': event.id,
                'name': event.name,
                'fields': event.fields,
            })
            self.send('agent:form_submissions:update', event.export())
            self.success("Successfully updated form submission: {}".format(event.id))
