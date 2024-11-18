from systems.commands.index import Command


class Publish(Command('publish')):

  def exec(self):
    self.data('Topic', self.topic, 'topic')
    self.sync_interface()

    # Generate web page YAML objects for web page as a dictionary
    # 1. Generate header
    #    1. Generate banner
    #    2. Generate stats
    #    3. Generate note
    # 2. Generate components
    #    1. Determine components and ordering
    #    2. Generate component
    # 3. Generate footer
    #    1. Generate FAQ
    # 4. Generate navigation
    #    1. Generate path
    #    2. Generate menu

    components = {
      'header': self.generate_component('header',
        title = 'statement',
        subtitle = 'statement',
        banner = {
          'title': 'statement',
          'subtitle': 'statement'
        },
        note = {
          'subject': 'statement',
          'statement': 'statement',
          'icon': 'icon'
        }
      ),
      'components': self.generate_components(),
      'footer': self.generate_component('footer',
        title = 'statement',
        subtitle = 'statement',
        faq = {
          'title': 'statement',
          'subtitle': 'statement',
          'items': [{
            'title': 'statement',
            'description': 'text'
          }, 12]
        }
      )
    }
    self.data('Components', components, 'components')


  def generate_component(self, topic, **fields):
    component = {}

    for field, info in fields.items():
      name = f"{topic} {field}"

      if isinstance(info, dict):
        component[field] = self.generate_component(name, **info)
      elif isinstance(info, (list, tuple)):
        component[field] = self.generate_component_list(
          name,
          info[1] if len(info) > 1 else 0,
          **info[0]
        )
      elif info in ['statement', 'text', 'quantity', 'icon']:
        component[field] = getattr(self, f"generate_{info}")(name)
      else:
        raise Exception(f"Component field processor {field} not found")

    return component

  def generate_component_list(self, topic, quantity, **fields):
    components = []
    if quantity > 0:
      for index in range(quantity):
        components.append(self.generate_component(topic, **fields))
    return components


  def generate_components(self):
    return []


  def generate_statement(self, topic):
    return self.generate_data(
        '189c564271672e406e5ae8e5115cf59ec3c1bf5993c78700c1354b8c5056bccd',
        f"Generate a single sentence meant for a {topic} statement of a knowledge center webpage about: {self.topic}",
        max_sections = 5,
        sentence_limit = 50
    )

  def generate_text(self, topic):
    return self.generate_data(
        '189c564271672e406e5ae8e5115cf59ec3c1bf5993c78700c1354b8c5056bccd',
        f"Generate a single paragraph meant for a {topic} overview of a knowledge center webpage about: {self.topic}",
        max_sections = 10,
        sentence_limit = 100
    )

  def generate_icon(self, topic):
    return self.generate_data(
        '189c564271672e406e5ae8e5115cf59ec3c1bf5993c78700c1354b8c5056bccd',
        f"Generate a single valid tabler icon meant for a {topic} icon of a knowledge center webpage about: {self.topic}",
        max_sections = 3,
        sentence_limit = 10
    )
