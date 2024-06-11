from arcade import Sprite

from charm.lib.components import Component, ComponentManager

class SubComponent(Sprite, Component):
    ...

cm = ComponentManager()
c = SubComponent()
cm.register(c)
cm.on_update(1/60)
cm.on_resize(100, 100)
cm.draw()



