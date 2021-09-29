FIG_BG_COLOR = "#0B1629"
AX_BG_COLOR = "#0D1A31"
AX_LABEL_COLOR = "#41646C"

TICKS_COLOR = "#61848C"

DEFAULT_LINE_COLOR = "#19444D"

RED = "#A30606"
GREEN = "#035C0C"
BLUE = "#164ACD"


def set_axes_style(axes):
    for ax in axes:
        ax.patch.set_facecolor(AX_BG_COLOR)
        ax.spines["top"].set_color(TICKS_COLOR)
        ax.spines["bottom"].set_color(TICKS_COLOR)
        ax.spines["left"].set_color(TICKS_COLOR)
        ax.spines["right"].set_color(TICKS_COLOR)
        ax.tick_params(colors=TICKS_COLOR)
        ax.xaxis.label.set_color(AX_LABEL_COLOR)
        ax.yaxis.label.set_color(AX_LABEL_COLOR)


def set_plot_style(fig, axes):
    fig.patch.set_facecolor(FIG_BG_COLOR)
    set_axes_style(axes)
