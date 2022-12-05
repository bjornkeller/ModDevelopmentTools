
import os
import sys
import shutil

shutil.make_archive('repository-update', 'zip', os.path.abspath(sys.argv[1]))
