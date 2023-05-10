import math

from kivy import properties
from kivy.uix.widget import Widget
from kivy.uix.layout import Layout
from kivy.animation import Animation, AnimationTransition
from kivy.graphics.context_instructions import PushMatrix, PopMatrix, Translate, Scale
from kivy.graphics.fbo import Fbo


class LineStub(Widget):
    color = properties.ColorProperty()
    thickness = properties.NumericProperty(1.0)


class TouchPassthrough(Widget):
    def on_touch_down(self, touch):
        if self.disabled:
            return False

        return super(TouchPassthrough, self).on_touch_down(touch)


class ProxyWidget(Widget):
    proxy_child = properties.AliasProperty(
        lambda self: self.children[0] if len(self.children) > 0 else self.dummy,
        rebind=True, bind=["children"]
    )

    def __init__(self, **kwargs):
        super(ProxyWidget, self).__init__(**kwargs)

        self.dummy = Widget(size=(0.0, 0.0), size_hint=(None, None))


class ProxyDummy(ProxyWidget):
    proxy_count = properties.BoundedNumericProperty(0, min=0)
    dummies = properties.ObjectProperty([])

    def __init__(self, **kwargs):
        super(ProxyDummy, self).__init__(**kwargs)

        self.dummies = []

    def on_proxy_count(self, widget, value):
        self.dummies = [Widget() for _ in range(value)]


class ProxyLayout(Layout):
    proxy_widgets = properties.ListProperty([])

    def __init__(self, **kwargs):
        super(ProxyLayout, self).__init__(**kwargs)

        def callback(widget, value):
            if self.parent is not None:
                self.parent._trigger_layout()

        self._trigger_parent = callback

    def add_widget(self, widget, *args, **kwargs):
        if isinstance(widget, ProxyWidget):
            widget.fbind("size", self._trigger_parent)
            widget.fbind("size_hint", self._trigger_parent)
            widget.fbind("size_hint_min", self._trigger_parent)
            widget.fbind("size_hint_max", self._trigger_parent)
            self.proxy_widgets.append(widget)

            if isinstance(widget, ProxyDummy):
                return

        super(ProxyLayout, self).add_widget(widget, *args, **kwargs)

    def remove_widget(self, widget, *args, **kwargs):
        if isinstance(widget, ProxyWidget):
            widget.funbind("size", self._trigger_parent)
            widget.funbind("size_hint", self._trigger_parent)
            widget.funbind("size_hint_min", self._trigger_parent)
            widget.funbind("size_hint_max", self._trigger_parent)
            self.proxy_widgets.remove(widget)

            if isinstance(widget, ProxyDummy):
                return

        super(ProxyLayout, self).remove_widget(widget, *args, **kwargs)

    def do_layout(self, *largs):
        real_children = self.children
        fake_children = []
        proxy_children = []
        pointers = []

        for i, child in enumerate(self.children):
            if isinstance(child, ProxyLayout) and (len(child.proxy_widgets) > 0):
                proxy_children.clear()
                for proxy_child in reversed(child.proxy_widgets):
                    if isinstance(proxy_child, ProxyDummy):
                        size = proxy_child.size
                        size_hint = proxy_child.size_hint
                        size_hint_min = proxy_child.size_hint_min
                        size_hint_max = proxy_child.size_hint_max
                        pos_hint = proxy_child.pos_hint

                        for dummy in proxy_child.dummies:
                            dummy.size = size
                            dummy.size_hint = size_hint
                            dummy.size_hint_min = size_hint_min
                            dummy.size_hint_max = size_hint_max
                            dummy.pos_hint = pos_hint
                            proxy_children.append(dummy)
                    else:
                        proxy_children.append(proxy_child)

                pointers.append((i, len(fake_children), len(proxy_children)))
                fake_children.extend(proxy_children)
            elif isinstance(child, ProxyWidget):
                if not isinstance(child, ProxyDummy):
                    fake_children.append(child.proxy_child)
            else:
                fake_children.append(child)

        self.funbind("children", self._trigger_layout)
        self.children = fake_children
        super(ProxyLayout, self).do_layout(*largs)
        self.children = real_children
        self.fbind("children", self._trigger_layout)

        for i, j, count in pointers:
            min_x, min_y = math.inf, math.inf
            max_x, max_y = -math.inf, -math.inf

            for k in range(count):
                child = fake_children[j + k]
                x0, y0 = child.x, child.y
                x1, y1 = x0 + child.width, y0 + child.height
                min_x, min_y = min(min_x, x0), min(min_y, y0)
                max_x, max_y = max(max_x, x1), max(max_y, y1)

            child = real_children[i]
            child.pos = (min_x, min_y)
            child.size = (max_x - min_x, max_y - min_y)


class AnimatedProperty(properties.Property):
    duration_override = None

    def __init__(self, *args, duration=0.0, transition=AnimationTransition.linear, **kwargs):
        super(AnimatedProperty, self).__init__(*args, **kwargs)

        self.duration = duration
        self.transition = transition
        self.dummies = {}  # {id(instance): dummy}

    def __set__(self, instance, value):
        if value == self.get(instance):
            self.set(instance, value)
            return

        if self.duration_override is not None:
            duration = self.duration_override
        elif isinstance(self.duration, str):
            duration = getattr(instance, self.duration)
        else:
            duration = self.duration

        if duration <= 0.0:
            self.set(instance, value)
            return

        if isinstance(self.transition, str):
            transition = getattr(instance, self.transition)
        else:
            transition = self.transition

        iid = id(instance)
        if iid in self.dummies:
            dummy = self.dummies[iid]
            Animation.cancel_all(dummy)
        else:
            dummy = Widget()
            dummy.create_property(self.name)
            self.set(dummy, self.get(instance))
            self.dummies[iid] = dummy

        def on_progress(*args):
            self.set(instance, self.get(dummy))

        def on_complete(*args):
            del self.dummies[iid]

        animation = Animation(duration=duration, transition=transition)
        animation.animated_properties[self.name] = value
        animation.bind(on_progress=on_progress, on_complete=on_complete)
        animation.start(dummy)


class AnimatedColorProperty(AnimatedProperty, properties.ColorProperty):
    pass


class AnimatedNumericProperty(AnimatedProperty, properties.NumericProperty):
    pass


class AnimatedBoundedNumericProperty(AnimatedProperty, properties.BoundedNumericProperty):
    pass


class FboLayout(Layout):
    fbo_texture = properties.ObjectProperty(None)
    fbo_size = properties.ListProperty([1.0, 1.0])

    def __init__(self, **kwargs):
        self.fbo = Fbo(size=self.fbo_size)
        self.fbo.add_reload_observer(self.update_fbo)
        self.fbo_translate = Translate()

        super(FboLayout, self).__init__(**kwargs)

    def on_pos(self, widget, value):
        self.clear_fbo()
        self.fbo_translate.xy = (-math.floor(self.x), -math.floor(self.y))

    def on_size(self, widget, value):
        old_width, old_height = self.fbo_size
        new_width, new_height = math.ceil(self.width + 1.0), math.ceil(self.height + 1.0)

        if (old_width < new_width) or (old_height < new_height):
            self.fbo_size = (max(old_width, new_width), max(old_height, new_height))
            self.fbo.size = self.fbo_size
            self.fbo_texture = self.fbo.texture
            self.update_fbo()
        else:
            self.clear_fbo()

    def on_children(self, widget, value):
        self.update_fbo()

    def clear_fbo(self):
        self.fbo.bind()
        self.fbo.clear_buffer()
        self.fbo.release()

    def update_fbo(self, *args):
        self.clear_fbo()
        self.canvas.clear()
        self.fbo.clear()
        self.fbo.add(PushMatrix())
        self.fbo.add(self.fbo_translate)

        for child in reversed(self.children):
            self.fbo.add(child.canvas)

        self.fbo.add(PopMatrix())
        self.canvas.add(self.fbo)


__all__ = [
    "LineStub", "TouchPassthrough", "ProxyWidget", "ProxyDummy", "ProxyLayout",
    "AnimatedProperty", "AnimatedColorProperty", "AnimatedNumericProperty", "AnimatedBoundedNumericProperty",
    "FboLayout"
]

