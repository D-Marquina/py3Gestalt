import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ObjectProperty


kivy.require('1.0.1')


class Py3GestaltGUI(BoxLayout):
    interface_lt = ObjectProperty(BoxLayout())
    interface_lt_lb = ObjectProperty(Label())
    btn1 = ObjectProperty(Button())
    btn2 = ObjectProperty(Button())


class Py3GestaltGUIApp(App):
    title = StringProperty("Gestalt Framework for Python 3")

    def build(self):
        self.load_kv('gui.kv')
        return Py3GestaltGUI()


if __name__ == '__main__':
    Py3GestaltGUIApp().run()
