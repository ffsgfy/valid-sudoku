from kivy import properties
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.animation import AnimationTransition

from common import AnimatedBoundedNumericProperty, FboLayout


class Message(FboLayout, AnchorLayout):
    text = properties.StringProperty()
    outline_color = properties.ColorProperty()
    background_color = properties.ColorProperty()
    background_dim = properties.BoundedNumericProperty(0.0, min=0.0, max=1.0)
    outline_thickness = properties.BoundedNumericProperty(0.0, min=0.0)
    corner_radius = properties.BoundedNumericProperty(0.0, min=0.0)
    alpha = AnimatedBoundedNumericProperty(
        0.0, min=0.0, max=1.0, duration="animation_duration", transition=AnimationTransition.in_out_sine
    )

    state = properties.BooleanProperty(False)
    window = properties.ObjectProperty(None, rebind=True, allownone=True)
    animation_duration = properties.BoundedNumericProperty(0.0, min=0.0)

    def __init__(self, **kwargs):
        super(Message, self).__init__(**kwargs)

        self._touch_started_inside = None
        self.bind(center=self.align_center, size=self.align_center)

    def open(self, *args, **kwargs):
        if self.state:
            return

        self.state = True
        self.window = Window
        self.window.add_widget(self)
        self.window.bind(on_resize=self.align_center, on_keyboard=self.on_keyboard)

        self.alpha = 1.0
        self.center = Window.center

    def dismiss(self, *_args, **kwargs):
        if not self.state:
            return

        self.alpha = 0.0
        if self.animation_duration > 0.0:
            Clock.schedule_once(self.remove_self, self.animation_duration)
        else:
            self.remove_self()

    def align_center(self, *args):
        if self.state:
            self.center = self.window.center

    def on_keyboard(self, window, key, *args):
        if self.state:
            if key == 27:  # <Esc>
                self.dismiss()
                return True

    def remove_self(self, *args):
        if not self.state:
            return

        self.window.unbind(on_resize=self.align_center, on_keyboard=self.on_keyboard)
        self.window.remove_widget(self)
        self.window = None
        self.state = False

    def on_motion(self, event_type, event):
        super(Message, self).on_motion(event_type, event)

        return True

    def on_touch_down(self, touch):
        self._touch_started_inside = self.collide_point(*touch.pos)
        if self._touch_started_inside:
            super(Message, self).on_touch_down(touch)

        return True

    def on_touch_move(self, touch):
        if self._touch_started_inside:
            super(Message, self).on_touch_move(touch)

        return True

    def on_touch_up(self, touch):
        if self._touch_started_inside is False:
            self.dismiss()
        else:
            super(Message, self).on_touch_up(touch)

        self._touch_started_inside = None
        return True

