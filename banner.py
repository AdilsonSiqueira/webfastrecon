BANNER_RAW = r"""
__        __     _     ____  _           _
\ \      / /__ _| |__ / ___|| |__   __ _| |_
 \ \ /\ / / _ \ | '_ \\___ \| '_ \ / _` | __|
  \ V  V /  __/ | |_) |___) | | | | (_| | |_
   \_/\_/ \___|_|_.__/|____/|_| |_|\__,_|\__|

CMSPathFinder
"""


def _interpolate(start, end, t):
   return int(start + (end - start) * t)


def gradient_text(text, start_rgb=(0, 120, 40), end_rgb=(160, 120, 10)):
   """Return `text` with per-character truecolor gradient from start_rgb to end_rgb."""
   chars = list(text)
   n = max(1, len(chars))
   out = []
   for i, ch in enumerate(chars):
      t = i / (n - 1) if n > 1 else 0
      r = _interpolate(start_rgb[0], end_rgb[0], t)
      g = _interpolate(start_rgb[1], end_rgb[1], t)
      b = _interpolate(start_rgb[2], end_rgb[2], t)
      out.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
   out.append("\x1b[0m")
   return ''.join(out)


def get_banner(colored=True):
   if not colored:
      return BANNER_RAW
   # apply gradient line-by-line for better visual
   lines = BANNER_RAW.splitlines(True)
   colored_lines = []
   for idx, line in enumerate(lines):
      # slightly shift color per line
      shift = idx / max(1, len(lines) - 1)
      start = (0, 100, 20)
      end = (160, 120, 10)
      # blend start/end by shift to vary per line
      s = (int(start[0] * (1 - shift)), int(start[1] * (1 - shift)), int(start[2] * (1 - shift)))
      e = (int(end[0] * (1 - shift) + start[0] * shift), int(end[1] * (1 - shift) + start[1] * shift), int(end[2] * (1 - shift) + start[2] * shift))
      colored_lines.append(gradient_text(line, s, e))
   return ''.join(colored_lines)

