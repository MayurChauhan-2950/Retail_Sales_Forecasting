"""Shared chart style: one palette, readable fonts, clean axes."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import FIGS

BLUE, ORANGE, RED, GREEN, GREY, PURPLE = "#2a6fb0", "#e67e22", "#c0392b", "#2e8b57", "#7f8c8d", "#7d5ba6"
PALETTE = [BLUE, ORANGE, GREEN, RED, PURPLE, GREY]
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": .25, "figure.dpi": 100, "font.size": 11, "axes.titlesize": 13,
                     "axes.titleweight": "bold", "axes.labelsize": 11,
                     "axes.prop_cycle": matplotlib.cycler(color=PALETTE)})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, dpi=130)
    plt.close(fig)
    print(f"  figure saved: {name}")
