from kivy import app, properties
from kivy.clock import Clock
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.event import EventDispatcher

from common import AnimatedColorProperty, AnimatedBoundedNumericProperty
from message import Message
from colorscheme import Colorscheme, colorschemes
import vsext


class AppState(EventDispatcher):
    colorscheme = properties.StringProperty("black")
    difficulty = properties.StringProperty("")
    solution = properties.ListProperty(None, allownone=True)
    board = properties.ListProperty(None, allownone=True)
    timer = properties.NumericProperty(0.0)
    mistakes = properties.NumericProperty(0)
    assist = properties.BooleanProperty(False)

    def load_config(self, config):
        self.colorscheme = config.get("state", "colorscheme")
        self.difficulty = config.get("state", "difficulty")
        self.solution = vsext.decode_state(config.get("state", "solution"))
        self.board = vsext.decode_state(config.get("state", "board"))
        self.timer = config.getint("state", "timer")
        self.mistakes = config.getint("state", "mistakes")
        self.assist = config.getboolean("state", "assist")

    def dump_config(self, config):
        config.set("state", "colorscheme", self.colorscheme)
        config.set("state", "difficulty", self.difficulty)
        config.set("state", "solution", "" if self.solution is None else vsext.encode_state(self.solution))
        config.set("state", "board", "" if self.board is None else vsext.encode_state(self.board))
        config.set("state", "timer", int(self.timer))
        config.set("state", "mistakes", self.mistakes)
        config.set("state", "assist", self.assist)
        config.write()


class App(app.App):
    colors = properties.ObjectProperty(Colorscheme(), rebind=True)
    state = properties.ObjectProperty(AppState(), rebind=True)
    alpha = AnimatedBoundedNumericProperty(0.0, min=0.0, max=1.0, duration=1.0)

    def __init__(self):
        super(App, self).__init__()

        self.screen_manager = None
        self.screen_stack = []

        def timer_callback(dt):
            self.state.timer += dt

        self.solver = vsext.Solver()
        self.difficulties = {
            "easy": (0, vsext.score_step * 2),
            "normal": (vsext.score_step * 2, vsext.score_step * 5),
            "hard": (vsext.score_step * 5, -1)
        }
        self.pregenerated = {key: None for key in self.difficulties.keys()}
        self.pregenerator = Clock.schedule_interval(self.pregenerate, 0.05)
        self.timer = Clock.create_trigger(timer_callback, 0.1, True)

    @property
    def name(self):
        return "validsudoku"

    def create_settings(self):
        pass

    def open_settings(self, *args):
        pass

    def set_colorscheme(self, name, animate=True):
        if name not in colorschemes:
            return

        self.state.colorscheme = name
        AnimatedColorProperty.duration_override = 0.0
        duration = self.colors.animation_duration if animate else 0.0
        target = colorschemes[name]

        for key, prop in self.colors.properties().items():
            if isinstance(prop, AnimatedColorProperty):
                prop.duration_override = duration
                setattr(self.colors, key, getattr(target, key))

        Clock.schedule_once(lambda dt: setattr(AnimatedColorProperty, "duration_override", None), duration)

    def switch_screen(self, screen):
        self.screen_stack.append(self.screen_manager.current)
        self.screen_manager.transition.direction = "left"
        self.screen_manager.current = screen

    def switch_back(self):
        if len(self.screen_stack) == 0:
            return

        self.screen_manager.transition.direction = "right"
        self.screen_manager.current = self.screen_stack.pop()

    def send_message(self, text):
        view = Message(text=text)
        view.open()

    def pregenerate(self, *args):
        if None not in self.pregenerated.values():
            self.pregenerator.cancel()
            return

        board, score = self.solver.generate_once()
        for key, (score_min, score_max) in self.difficulties.items():
            if self.pregenerated[key] is not None:
                continue

            if (score_min <= score) and ((score <= score_max) or (score_max < 0)):
                self.pregenerated[key] = board
                break

    def start_game(self, board):
        solutions = self.solver.solve(board, False, 2)
        if len(solutions) == 0:
            self.send_message("Game state has no solution")
            return
        elif len(solutions) > 1:
            self.send_message("Game state has multiple solutions")
            return

        self.state.solution = solutions[0][0]
        self.state.board = board
        self.state.timer = 0
        self.state.mistakes = 0
        self.screen_manager.get_screen("game").select(None)
        self.switch_screen("game")

    def start_random_game(self, difficulty):
        key = difficulty.lower()
        if key not in self.difficulties:
            return

        if self.pregenerated[key] is None:
            score_min, score_max = self.difficulties[key]
            board = self.solver.generate(score_min, score_max, 200)[0]
        else:
            board = self.pregenerated[key]
            self.pregenerated[key] = None

        self.pregenerator()
        self.state.difficulty = difficulty
        self.start_game(board)

    def start_imported_game(self):
        text = Clipboard.paste()
        board = vsext.decode_state(text.strip())
        if board is None:
            self.send_message("No valid game state in clipboard")
            return

        self.state.difficulty = ""
        self.start_game(board)

    def export_board(self):
        if self.state.board is None:
            return

        Clipboard.copy(vsext.encode_state(self.state.board))
        self.send_message("Game state copied to clipboard")

    def on_keyboard(self, window, key, *args):
        if key == 27:  # <Esc> & the back button on mobile
            if len(self.screen_stack) > 0:
                self.switch_back()
            else:
                self.stop()

            return True

    def on_start(self):
        self.state.load_config(self.config)
        self.set_colorscheme(self.state.colorscheme, animate=False)
        self.alpha = 1.0

        Window.bind(on_keyboard=self.on_keyboard)

    def on_pause(self):
        self.state.dump_config(self.config)
        return True

    def on_stop(self):
        self.state.dump_config(self.config)

    def build_config(self, config):
        config.setdefaults("state", {
            "colorscheme": "black",
            "difficulty": "",
            "solution": "",
            "board": "",
            "timer": 0,
            "mistakes": 0,
            "assist": False
        })

    def build(self):
        self.title = "Valid Sudoku"
        self.use_kivy_settings = False
        self.screen_manager = Builder.load_file("main.kv")
        self.screen_manager.transition.duration = 0.2
        return self.screen_manager


if __name__ == "__main__":
    App().run()

