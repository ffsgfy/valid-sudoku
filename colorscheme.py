from kivy.properties import BoundedNumericProperty
from kivy.event import EventDispatcher
from kivy.utils import get_color_from_hex

from common import AnimatedColorProperty


class Colorscheme(EventDispatcher):
    foreground_0 = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))
    foreground_1 = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))
    background_0 = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))
    background_1 = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))
    warning = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))
    error = AnimatedColorProperty((0.0, 0.0, 0.0, 1.0))

    animation_duration = BoundedNumericProperty(0.2, min=0.0)


colorschemes = {
    "white": Colorscheme(
        foreground_0=get_color_from_hex("#000000"),
        foreground_1=get_color_from_hex("#B1B1B1"),
        background_0=get_color_from_hex("#FFFFFF"),
        background_1=get_color_from_hex("#E5E5E5"),
        warning=get_color_from_hex("#FFEA2E"),
        error=get_color_from_hex("#CC2936")
    ),
    "beige": Colorscheme(
        foreground_0=get_color_from_hex("#222222"),
        foreground_1=get_color_from_hex("#9A8C98"),
        background_0=get_color_from_hex("#F2E9E4"),
        background_1=get_color_from_hex("#D8C4C0"),
        warning=get_color_from_hex("#F5E12C"),
        error=get_color_from_hex("#D12F0F")
    ),
    "green": Colorscheme(
        foreground_0=get_color_from_hex("#DAD7CD"),
        foreground_1=get_color_from_hex("#6F8572"),
        background_0=get_color_from_hex("#344E41"),
        background_1=get_color_from_hex("#416252"),
        warning=get_color_from_hex("#EFB73D"),
        error=get_color_from_hex("#CD381D")
    ),
    "blue": Colorscheme(
        foreground_0=get_color_from_hex("#E0E1DD"),
        foreground_1=get_color_from_hex("#384057"),
        background_0=get_color_from_hex("#0D1B2A"),
        background_1=get_color_from_hex("#1B263B"),
        warning=get_color_from_hex("#FACD52"),
        error=get_color_from_hex("#B43034")
    ),
    "black": Colorscheme(
        foreground_0=get_color_from_hex("#FFFFFF"),
        foreground_1=get_color_from_hex("#555555"),
        background_0=get_color_from_hex("#000000"),
        background_1=get_color_from_hex("#1F1F1F"),
        warning=get_color_from_hex("#F5CC00"),
        error=get_color_from_hex("#DB0F0F")
    )
}

