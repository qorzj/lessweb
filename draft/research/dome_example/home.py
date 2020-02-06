from lessweb.plugin.dome import Div, Kit, Button, Module, FlexRow, FlexItem, Link, TextInput, TextArea


def endpoint():
    return [
        Div('Hello lessweb'),
        FlexRow(
            FlexItem('( A )'), FlexItem('( B )'), FlexItem('( C )'),
        ),
        FlexRow(
            FlexItem(Button('( F )', onclick="home_action.kit.goto('http://lessweb.org')", primary=True)), FlexItem(Link('( G )', 'http://lessweb.org')),
        ),
        TextInput('姓名', id='input_name'),
        TextArea('简介', id='input_intro'),
        FlexRow('', id='flex_append'),
        Button('Click Me', onclick="home_action.submit()"),
        Module(from_='home', import_='Action()', as_='home_action'),
    ]


class Action:
    def __init__(self):
        self.kit = Kit()
        self.name_div = self.kit.select('#input_name')
        self.intro_div = self.kit.select('#input_intro')
        self.append_div = self.kit.select('#flex_append')

    def append(self, data):
        flex_item = FlexItem(data.reply)
        self.append_div.append(flex_item.dumps())

    def submit(self):
        data = {'name': self.name_div.val(), 'intro': self.intro_div.val()}
        self.kit.ajax(method='POST', url='/upper', data=data, onsuccess=self.append)
