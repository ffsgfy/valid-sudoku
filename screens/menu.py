from kivy import properties
from kivy.animation import Animation, AnimationTransition
from kivy.uix.screenmanager import Screen


class MenuScreen(Screen):
    animation_duration = properties.BoundedNumericProperty(0.0, min=0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.animation_transition_size = AnimationTransition.in_out_quad
        self.animation_transition_opacity_in = AnimationTransition.in_cubic
        self.animation_transition_opacity_out = AnimationTransition.out_cubic

    def toggle_submenu(self, state):
        submenu = self.ids.submenu

        if state:
            if self.animation_duration > 0.0:
                Animation.cancel_all(submenu)

                animation = Animation(
                    opacity=1.0,
                    duration=self.animation_duration / 2,
                    transition=self.animation_transition_opacity_in
                )
                animation &= Animation(
                    size_fraction=1.0,
                    duration=self.animation_duration,
                    transition=self.animation_transition_size
                )
                animation.bind(on_complete=lambda *args: setattr(submenu, "disabled", False))
                animation.start(submenu)
            else:
                submenu.size_fraction = 1.0
                submenu.opacity = 1.0
                submenu.disabled = False
        else:
            submenu.disabled = True

            if self.animation_duration > 0.0:
                Animation.cancel_all(submenu)

                animation = Animation(duration=self.animation_duration / 2)
                animation += Animation(
                    opacity=0.0,
                    duration=self.animation_duration / 2,
                    transition=self.animation_transition_opacity_out
                )
                animation &= Animation(
                    size_fraction=0.0,
                    duration=self.animation_duration,
                    transition=self.animation_transition_size
                )
                animation.start(submenu)
            else:
                submenu.size_fraction = 0.0
                submenu.opacity = 0.0


__all__ = ["MenuScreen"]

