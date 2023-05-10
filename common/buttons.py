from kivy import properties
from kivy.uix import behaviors
from kivy.animation import AnimationTransition
from kivy.uix.widget import Widget

from .utils import AnimatedColorProperty


class SimpleButton(behaviors.ButtonBehavior, Widget):
    down = properties.BooleanProperty(False)

    foreground_color = AnimatedColorProperty(duration="animation_duration", transition="animation_transition")
    background_color = AnimatedColorProperty(duration="animation_duration", transition="animation_transition")

    corner_radius = properties.BoundedNumericProperty(0.0, min=0.0)
    animation_duration = properties.BoundedNumericProperty(0.0, min=0.0)
    animation_transition = properties.ObjectProperty(AnimationTransition.in_out_sine)


class OutlineButton(SimpleButton):
    outline_color = AnimatedColorProperty(duration="animation_duration", transition="animation_transition")
    outline_thickness = properties.BoundedNumericProperty(0.0, min=0.0)


class TogglingButton(behaviors.ToggleButtonBehavior, Widget):
    pass


__all__ = ["SimpleButton", "OutlineButton", "TogglingButton"]

