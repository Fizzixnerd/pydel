#! /usr/bin/python

# This script shouldn't be dependant on the version of python, as long
# as it's at least, like, 2.6 or something like that.  Will work with
# python3.

# February 24ish, 2012 (1.0):
#     * initial version
# February 27, 2012 (1.0.1):
#     * changed version info
#     * removed "copyright" notice
# September 13, 2012:
#     * Fixed some spelling errors, etc.
#     * Began work on undeletion framework

import argparse
import logging
import os
import shutil
import sys

version = "1.0.1"
trash_folder = os.path.expanduser(os.getenv("TRASH",
                                            default="~/.local/share/Trash/files/"))

class DelError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg.__repr__()

class TrashDoesNotExistError(DelError):

    def __init__(self, msg):
        DelError.__init__(self, msg)

class TrashIsNotFolderError(DelError):

    def __init__(self, msg):
        DelError.__init__(self, msg)
    
class FileNotFoundError(DelError):

    def __init__(self, msg):
        DelError.__init__(self, msg)

class FilenameConflictError(DelError):

    def __init__(self, msg):
        DelError.__init__(self, msg)

def init_parser():
    """Return a parser that is set up with the appropriate options for
    del.py."""

    # TODO: Refactor this, subclassing argparse.ArgumentParser instead
    # of having this function.

    parser = argparse.ArgumentParser(description="Moves files to the TRASH.")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite files with identical names already present in the TRASH. Default behavior is to append a number to the end of the filename before moving it to the trash.")
    parser.add_argument("-c", "--complain", action="store_true",
                        help="Skip and print a complaint to stderr if a file with identical name is already present in the TRASH; raises exception if -b is present.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Display helpful messages. Useful when used interactively.")
    parser.add_argument("-vv", "--debug", "--very-verbose", action="store_true",
                        help="Display debugging information.")
    parser.add_argument("-b", "--brittle", action="store_true",
                        help="Immediately raise an exception and exit on any error.")
    parser.add_argument("--version", action="store_true",
                        help="Print name and version info and then exit.")
    parser.add_argument("-t", "--trash-folder", action="store",
                        nargs=1, default=trash_folder,
                        help="Specify the TRASH folder, where del should move trash to. Defaults to %s." % (trash_folder))
    parser.add_argument("files", metavar="FILE", nargs="+", action="store",
                        help="Path(s) to the FILE(S) which you wish to move to the TRASH.")

    return parser

def trash_is_okay(trash_path):
    """Raise appropriate exceptions if there are problems with the
    filepath referenced by trash_path. Returns True if everything is
    a-okay."""

    if not os.path.exists(trash_path):
        msg = "trash folder '%s' does not exist." % (trash_path)
        logging.critical(msg)
        raise TrashDoesNotExistError("ERROR: " + msg)
    elif not os.path.isdir(trash_path):
        msg = "trash folder '%s' is not a folder." % (trash_path)
        logging.critical(msg)
        raise TrashIsNotFolderError("ERROR: " + msg)
    else:
        return True

def resolve_name_conflict(filepath, parsed_args):
    """Resolve a conflict with a file of the same name already
    existing in the trash, according to the flags in
    parsed_args. Default behavior is to append an integer to the end
    of filename to uniquify it"""

    filename = os.path.basename(filepath)
    msg = "A file with the name '%s' already exists in the trash." % \
          (filename)

    if parsed_args.complain:
        logging.warning(msg + " Skipping.")
        if parsed_args.brittle:
            raise FilenameConflictError("ERROR: " + msg)
    elif parsed_args.overwrite:
        logging.info(msg + " Overwriting.")
        problem_filepath = os.path.join(parsed_args.trash_folder, filename)
        shutil.rmtree(problem_filepath)
        logging.debug("%s has been removed." % (problem_filepath))
        shutil.move(filepath, parsed_args.trash_folder)
        logging.debug("%s has been moved to the trash." % (filepath))
    else:
        # Default behavior; append an integer to filename to uniquify
        # it in the TRASH folder, then move file to TRASH as the new
        # name.
        logging.info(msg)
        ii = 0
        new_filename = filename + str(ii)
        while os.path.exists(os.path.join(parsed_args.trash_folder,
                                          new_filename)):
            ii += 1
            new_filename = filename + str(ii)
        # Now new_filename is unique in the trash .
        logging.info("Moving %s to trash as %s" % (filepath, new_filename))
        unique_destination_path = os.path.join(parsed_args.trash_folder,
                                               new_filename)
        shutil.move(filepath, unique_destination_path)
        logging.debug("%s has been moved to %s." % \
                      (filepath, unique_destination_path))

def get_logging_level(parsed_args):
    """Return the appropriate logging level, given the commandline
    arguments parsed by init_parser.parse_args()."""

    # Default logging level is WARNING
    logging_level = logging.WARNING
    if parsed_args.verbose:
        logging_level = logging.INFO
    if parsed_args.debug:
        logging_level = logging.DEBUG

    return logging_level

if __name__ == "__main__":

    # HACK: Check to see if --version is in the args given.  parser
    # complains if there are no files given along with --version, so I
    # have to check directly.
    if "--version" in sys.argv:
        version_info = "del.py version %s\nLovingly crafted in 2012 by Matt Walker <matt.g.d.walker@gmail.com>\nLicensed under the GNU GPLv2 as published by the Free Software Foundation." % (version)
        print (version_info)
        exit (0)

    # Initialize the parser and logger.
    parsed_args = init_parser().parse_args()
    logging.basicConfig(level=get_logging_level(parsed_args))
    # logging.exit_code keeps track to see if there were any errors
    logging.exit_code = 0
    logging.debug("The parsed_args Namespace is the following: %s" % \
                  (parsed_args.__repr__()))

    # Make sure trash_folder actually exist and is a folder.
    if trash_is_okay(parsed_args.trash_folder):
        logging.debug("Trash folder is okay.")

    for filepath in parsed_args.files:
        logging.debug("Now operating on: %s" % (filepath))
        # TODO: should refactor this: should be if os.path.exists: do
        # stuff and having non-existence as the else clause.
        if not os.path.exists(filepath):
            msg = "The file '%s' does not exist." % (filepath)
            logging.error(msg)
            # note that there was an error; set logging.exit_code = 1
            logging.exit_code = 1
            if parsed_args.brittle:
                raise FileNotFoundError(msg)
        else: # filepath exists
            filename = os.path.basename(filepath)
            if os.path.exists(os.path.join(parsed_args.trash_folder, filename)):
                # filename already exists in the trash as well
                resolve_name_conflict(filepath, parsed_args)
            else: # filename doesn't exist in the trash
                shutil.move(filepath, parsed_args.trash_folder)
                logging.debug("moved %s to trash." % (filepath))

    # zero if everything was peachy; nonzero otherwise
    exit (logging.exit_code)
