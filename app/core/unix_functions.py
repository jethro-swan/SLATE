import grp
import pwd
import os
import sys
import shutil
from pathlib import Path

# https://stackoverflow.com/questions/927866/
#   how-to-get-the-owner-and-group-of-a-folder-with-python-on-a-linux-machine
# https://stackoverflow.com/questions/5994840/
#   how-to-change-the-user-and-group-permissions-for-a-directory-by-name
# https://docs.python.org/3/library/shutil.html

#from logging import log_event


#------------------------------------------------------------------------------
# Log an event:
#
#def log_event(category, summary, details):
#    if category not in set(["access",
#                            "activity",
#                            "auth",
#                            "debug",
#                            "entity_history",
#                            "error",
#                            "tests"]):
#        return False
#    timestamp = datetime.datetime.now().strftime(LOG_DATETIME_FMT)
#    with open(NESTS_LOGS + "/" + category + ".log", "a") as log_file:
#        log_file.write(timestamp + "\t" + summary + "\n")
#        log_file.write(details + "\n")

#------------------------------------------------------------------------------


# Create a directory with mode specified:
def create_dir(dirpath, mode):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath, mode)

def create_file(filename):
    Path(filename).touch()
    # TO DO: Extend to set perms, owner, etc.

# Create hard link:
#def hard_link(src, dst):
#    os.link(src, dst)

# Create symlink:
def sym_link(symlink, target):
    try:
        os.symlink(target, symlink)
    except OSError:
        if os.path.exists(symlink):
            print("Symlink created but throws spurious error.")
            log_event("debug", "Symlink created but throws spurious error.")
        else:
            print("Symlink not created.")
            log_event("debug", "Symlink not created.")
        pass

# NB, this is a fudge to get around the problem that the message
#   "FileExistsError: [Errno 17] File exists:"
# always occurs, no matter how the symlink is created. This is very obviously a
# bug in Python 3 that no-one seems to be attempting to address.

#    Path(symlink).symlink_to(target)
#def sym_link(symlink, target):
#    os.symlink(target, symlink)

# Remove hard link:
#os.unlink(path)

# Get UID for file or directory:
def get_uid(path):
    #stat_info = os.stat(path)
    #uid = stat_info.st_uid
    #return uid
    return os.stat(path).st_uid

# Get GID for file or directory:
def get_gid(path):
    #stat_info = os.stat(path)
    #gid = stat_info.st_gid
    #return gid
    return os.stat(path).st_gid

# Get owner name of file or directory:
def get_user(path):
    #stat_info = os.stat(path)
    #uid = stat_info.st_uid
    #user = pwd.getpwuid(uid)[0]
    #return user
    return  pwd.getpwuid(os.stat(path).st_uid)[0]

# Get group name of file or directory:
def get_path(path):
    #stat_info = os.stat(path)
    #gid = stat_info.st_gid
    #group = grp.getgrgid(gid)[0]
    #return group
    return grp.getgrgid(os.stat(path).st_gid)[0]

# Get UID of user:
def get_user_uid(user_name):
    #uid = pwd.getpwnam(user_name).pw_uid
    return pwd.getpwnam(user_name).pw_uid

# Get GID of group:
def get_group_gid(group_name):
    #gid = grp.getgrnam(group_name).gr_gid
    return grp.getgrnam(group_name).gr_gid

# Set owner and group:
def set_owner_group(path, owner, group):
    os.chown(path, uid, gid)

# Set owner:
def set_owner(path, owner):
    shutil.chown(path, user=owner, group=None)

# Set group:
def set_group(path, ugroup):
    shutil.chown(path, user=None, group=ugroup)

# Copy file or directory with metadata but without following symlinks:
def fcopy(src_path, dest_path):
    newpath = shutil.copy2(src_path, dest_path, follow_symlinks=False)
    if newpath == dest_path:
        return(newpath)
    else:
        return("")
    # Returns empty string if unsuccessful


# Copy file or directory with metadata and following symlinks:
def fcopysl(src_path, dest_path):
    shutil.copy2(src_path, dest_path, follow_symlinks=True)
#    shutil.copy2(src_path, dest_path, *, follow_symlinks=True)

# Copy a directory tree without symlinks:
def treecopy(src_path, dest_path):
    shutil.copytree(src_path, dest_path,
                    symlinks=False,
                    ignore_dangling_symlinks=False,
                    dirs_exist_ok=True)
#    shutil.copytree(src_path, dest_path,
#                    symlinks=False,
#                    ignore=None,
#                    copy_function=copy2,
#                    ignore_dangling_symlinks=False,
#                    dirs_exist_ok=False)

# Copy a directory treee with symlinks:
def treecopysl(src_path, dest_path):
    shutil.copytree(src_path, dest_path,
                    symlinks=True,
                    ignore_dangling_symlinks=False,
                    dirs_exist_ok=True)

# Remove a directory tree:
def remove_tree(path):
    shutil.rmtree(path, ignore_errors=False, onerror=None)

# Move a directory tree:
def move_tree(path):
    shutil.move(src, dst, copy_function=copy2)

# Disc usage:
def disc_usage(path):
    shutil.disk_usage(path)

# Get file/directory permissions:
def get_perms_octal(path):
    return(oct(os.stat(filename).st_mode)[-3:])

# Set file/directory permissions:
def set_perms_octal(path, mask):
    os.chmod(path, mask)

# Get file size:
def get_file_size(path):
    return(oct(os.stat(path).st_size))
