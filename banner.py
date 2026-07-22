BANNER_RAW = r"""
      WebFastRecon            Author AdilsonSiqueira

            ██╗    ██╗███████╗██████╗
            ██║    ██║██╔════╝██╔══██╗
            ██║ █╗ ██║█████╗  ██████╔╝
            ██║███╗██║██╔══╝  ██╔══██╗
            ╚███╔███╔╝██║     ██║  ██║
            ╚══╝╚══╝ ╚═╝     ╚═╝  ╚═╝

"""


def _interpolate(start, end, t):
   return int(start + (end - start) * t)


def gradient_text(text, start_rgb=(20, 120, 240), end_rgb=(240, 200, 20)):
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
   lines = [line.rstrip('\n') for line in BANNER_RAW.splitlines() if line.strip()]
   colored_lines = []
   for idx, line in enumerate(lines):
      # slightly shift color per line
      shift = idx / max(1, len(lines) - 1)
      start = (20, 120, 240)
      end = (240, 200, 20)
      # blend start/end by shift to vary per line
      s = (int(start[0] * (1 - shift)), int(start[1] * (1 - shift)), int(start[2] * (1 - shift)))
      e = (int(end[0] * (1 - shift) + start[0] * shift), int(end[1] * (1 - shift) + start[1] * shift), int(end[2] * (1 - shift) + start[2] * shift))
      colored_lines.append(gradient_text(line, s, e))
   return '\n'.join(colored_lines) + '\n'

