"""Enhancement algorithms package"""

from .clahe import apply as clahe_apply
from .ifg import enhance as ifg_enhance

__all__ = ["clahe_apply", "ifg_enhance"]
