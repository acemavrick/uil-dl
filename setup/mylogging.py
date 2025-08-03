import logging
from pathlib import Path
# from colorama import Fore, Style
# from colorama import init as colorama_init

# # Initialize colorama for cross-platform color support
# colorama_init()

# class ColoredFormatter(logging.Formatter):
#     """Custom formatter that adds colors to log levels."""
#     COLORS = {
#         'DEBUG': Fore.BLUE,
#         'INFO': Fore.GREEN,
#         'WARNING': Fore.YELLOW,
#         'ERROR': Fore.RED,
#         'CRITICAL': Fore.RED + Style.BRIGHT
#     }

#     def format(self, record):
#         original_levelname = record.levelname
#         if original_levelname in self.COLORS:
#             colored_levelname = f"{self.COLORS[original_levelname]}{original_levelname}{Style.RESET_ALL}"
#             # Colorize levelname and message for logging output.
#             # This approach avoids complex Formatter method overrides by temporarily
#             # modifying record fields before passing to the base class format method.
#             colored_msg = f"{self.COLORS[original_levelname]}{record.msg}{Style.RESET_ALL}"
            
#             # Store original msg, colorize the record's msg field for the current formatter pass
#             original_msg = record.msg
#             record.msg = colored_msg
#             record.levelname = colored_levelname # Colorize levelname for the formatter
            
#             formatted_log = super().format(record)
            
#             # Restore original for other handlers / sanity
#             record.levelname = original_levelname
#             record.msg = original_msg
#             return formatted_log
            
#         return super().format(record)

# configure initial colored console logging
def _setup_console_logger():
    # clear any existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler()
    # console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

_setup_console_logger()
LOGGER = logging.getLogger(__name__)

# configure logging to file (switches from console to file-only)
def setup_logging(data_path: Path):
    global LOGGER
    
    # remove all existing handlers (console) and add file handler only
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    file_handler = logging.FileHandler(
        filename=data_path / "uil-dl.log",
        mode="a",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)

    LOGGER.info("Setup new log session")

