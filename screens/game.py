import random

from kivy import app, properties
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from common import AnimatedNumericProperty, AnimatedBoundedNumericProperty, ProxyLayout, OutlineButton
import vsext


class GridCell(OutlineButton, AnchorLayout):
    index = properties.NumericProperty(0)
    screen = properties.ObjectProperty(None, rebind=True)

    is_selected = properties.BooleanProperty(False)
    is_warning = properties.BooleanProperty(False)
    is_error = properties.BooleanProperty(False)

    text = properties.StringProperty("")
    text_scale = AnimatedNumericProperty(1.0, duration="animation_duration")
    text_scale_pop = properties.NumericProperty(1.0)
    text_opacity = AnimatedBoundedNumericProperty(1.0, min=0.0, max=1.0, duration="animation_duration")

    def on_release(self):
        if self.screen is not None:
            self.screen.select(self.index)

    def set_text(self, text):
        if self.text == text:
            return

        # Not animated
        GridCell.text_scale.set(self, self.text_scale_pop)
        GridCell.text_opacity.set(self, 0.0 if len(text) > 0 else 1.0)

        # Animated
        self.text_scale = 1.0
        self.text_opacity = 1.0 if len(text) > 0 else 0.0

        if (len(text) == 0) and (self.animation_duration > 0.0):
            Clock.schedule_once(lambda dt: setattr(self, "text", text), self.animation_duration)
        else:
            self.text = text


class GridBlock(ProxyLayout, BoxLayout):
    cell_hint = properties.NumericProperty(1.0)
    cell_hint_min = properties.NumericProperty(0.0)

    spacing_hint = properties.NumericProperty(1.0)
    spacing_hint_min = properties.NumericProperty(0.0)
    spacing_hint_max = properties.NumericProperty(1.0, allownone=True)

    background_color = properties.ColorProperty()
    corner_radius = properties.BoundedNumericProperty(0.0, min=0.0)


class PanelAction(OutlineButton, Label):
    screen = properties.ObjectProperty(None, rebind=True)


class GameScreen(Screen):
    selection = properties.NumericProperty(None, allownone=True)
    selection_mask = properties.NumericProperty(0)  # possible values in selected cell

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cells = [None] * 81
        self.app = None

    def on_kv_post(self, base_widget):
        self.app = app.App.get_running_app()

        cell_counter = 0
        for child in self.walk(restrict=True):
            if isinstance(child, GridCell):
                outer = cell_counter // 9
                inner = cell_counter % 9
                index = (outer // 3 * 3 + inner // 3) * 9 + (outer % 3 * 3 + inner % 3)

                self.cells[index] = child
                child.index = index
                child.screen = self

                cell_counter += 1
            elif isinstance(child, PanelAction):
                child.screen = self

    def on_enter(self):
        self.ids.assist.state = "down" if self.app.state.assist else "normal"
        self.app.timer()
        self.refresh()

    def on_leave(self):
        self.app.timer.cancel()

    def refresh(self):
        conflicts = vsext.list_conflicts(self.app.state.board)
        finished = True

        for index, cell in enumerate(self.cells):
            mask = self.app.state.board[index]
            mask_ref = self.app.state.solution[index]
            finished = finished and (mask == mask_ref)
            cell.set_text(str(vsext.decode_mask(mask) + 1).replace("0", ""))
            cell.is_warning = (vsext.bit_count(mask) == 1) and (mask != mask_ref)
            cell.is_error = index in conflicts

        if finished:
            self.app.timer.cancel()

    def hint(self):
        if self.selection is None:
            options = [i for i, mask in enumerate(self.app.state.board) if vsext.bit_count(mask) != 1]
            if len(options) == 0:
                return

            index = random.choice(options)
        else:
            index = self.selection

        self.cells[index].text = ""  # force the animation
        self.app.state.board[index] = self.app.state.solution[index]
        self.refresh()

    def put(self, mask):
        if self.selection is None:
            return

        cell = self.cells[self.selection]
        cell.text = ""  # force the animation

        self.app.state.board[self.selection] = mask
        self.refresh()

        if cell.is_error or (cell.is_warning and self.app.state.assist):
            self.app.state.mistakes += 1

    def select(self, index):
        if self.selection is not None:
            self.cells[self.selection].is_selected = False

        if (index is not None) and (index != self.selection):
            self.cells[index].is_selected = True
            self.selection = index
            self.selection_mask = vsext.list_candidates(self.app.state.board, index)
        else:
            self.selection = None
            self.selection_mask = 0

