import sys
from elastic_logger.cli import main

# Python main entry point when run directly as
# a python module. This just passes command
# line parameters to the main() function
# in cli.py

if __name__ == "__main__":
    main(sys.argv[1:])
