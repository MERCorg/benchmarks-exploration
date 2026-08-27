"""Generate the benchmarks-exploration tool-comparison scatter plot.

This is a concrete instantiation of the generic plotting interface in
``create_plot.py`` (the scatter-plot counterpart of
``create_table_exploration.py``). It produces a scatter plot that compares two
tools on the same metric, with one point per benchmark case:

    y-axis: merc-lps time (s)
       |                          .
       |                      .
       |                  .   <- points above the dashed y = x line are
       |              .          cases where merc-lps is slower than lps2lts
       |          .
       |      .
       |  .
       +-------------------------- x-axis: lps2lts time (s)

A dashed ``y = x`` reference line makes it easy to read which tool wins each
case: points below the line favour the y-axis tool, points above favour the
x-axis tool. The output is dependency-free pgfplots/TikZ LaTeX.
"""

import argparse
import sys
from pathlib import Path

from merc import (
    AGGREGATORS,
    METRIC_LABELS,
    PlotSeries,
    build_comparison_points,
    render_pgfplots_scatter,
)

DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "exploration_scatter.tex"


def tool_select(tool: str, threads: int, caching: str):
    """Build a record filter for one tool / thread count / caching mode."""
    return lambda record: (
        record.get("_tool") == tool
        and int(record.get("threads", 1)) == threads
        and record.get("caching") == caching
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the benchmarks-exploration tool-comparison scatter plot."
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE,
                        help="NDJSON results for the base lps2lts build.")
    parser.add_argument("--merc", type=Path, default=DEFAULT_MERC,
                        help="NDJSON results for merc-lps (single thread).")
    parser.add_argument("--x-tool", choices=TOOL_ORDER, default="lps2lts",
                        help="Tool plotted on the x-axis (default: lps2lts).")
    parser.add_argument("--y-tool", choices=TOOL_ORDER, default="merc-lps",
                        help="Tool plotted on the y-axis (default: merc-lps).")
    parser.add_argument("--metric", choices=sorted(METRIC_LABELS), default="time",
                        help="Metric compared on both axes (default: time).")
    parser.add_argument("--threads", type=int, default=1,
                        help="Thread count to compare at (default: 1)")
    parser.add_argument("--caching", default="local",
                        help="Caching mode to compare (default: local).")
    parser.add_argument("--aggregate", choices=sorted(AGGREGATORS), default="mean",
                        help="How to combine values across benchmark runs.")
    parser.add_argument("--linear", dest="log", action="store_false",
                        help="Use linear axes instead of the default logarithmic axes.")
    parser.add_argument("--no-diagonal", dest="diagonal", action="store_false",
                        help="Omit the y = x reference line.")
    parser.add_argument("--fragment", dest="standalone", action="store_false",
                        help="Emit only the tikzpicture fragment instead of a standalone document.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to the generated scatter plot.")
    args = parser.parse_args()

    records = load_tagged(args.base, args.merc)

    x_select = tool_select(args.x_tool, args.threads, args.caching)
    y_select = tool_select(args.y_tool, args.threads, args.caching)
    points = build_comparison_points(
        records, x_select, y_select, metric=args.metric, aggregate=AGGREGATORS[args.aggregate]
    )

    metric_label = METRIC_LABELS[args.metric]
    series = [
        PlotSeries(
            label=f"{args.y_tool} vs {args.x_tool}",
            points=points,
            mark="*",
            color="blue",
        )
    ]

    render_pgfplots_scatter(
        args.output,
        series,
        x_label=f"{args.x_tool} {metric_label}",
        y_label=f"{args.y_tool} {metric_label}",
        log_x=args.log,
        log_y=args.log,
        diagonal=args.diagonal,
        standalone=args.standalone,
    )
    print(
        f"Scatter plot written to {args.output} "
        f"({args.y_tool} vs {args.x_tool}, metric: {args.metric}, "
        f"{len(points)} cases, aggregate: {args.aggregate})"
    )


if __name__ == "__main__":
    main()
