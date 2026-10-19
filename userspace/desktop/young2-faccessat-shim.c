/*
 * young2-faccessat-shim.c
 * LD_PRELOAD shim for the Samsung Galaxy Young 2 (kernel 3.10.17, musl).
 *
 * PROBLEM (proven by strace in documentation/2026-09-23_17-55_fix-xfce-applications-menu):
 *   GLib >= 2.86 g_local_file_query_exists() calls faccessat(..., AT_EACCESS|AT_SYMLINK_NOFOLLOW).
 *   musl translates any faccessat() call carrying flags into the faccessat2 syscall.
 *   faccessat2 requires Linux >= 5.8; kernel 3.10.17 returns ENOSYS; musl then maps
 *   ENOSYS to EINVAL for flag!=0 calls. GLib's EINVAL branch:
 *       g_critical("g_local_file_query_exists: faccessat doesn't support supplied flags");
 *       return FALSE;   <-- "file does not exist"
 *   Garcon builds the Xfce menu through GIO; every existence check for a .desktop or
 *   .directory file returns FALSE, so the Applications menu (and appfinder) is EMPTY.
 *
 * FIX: override faccessat() in every Xfce process and implement the flags semantics
 *   without faccessat2:
 *     - flag == 0                      -> forward to real faccessat (fine on 3.10)
 *     - flag & ~AT_SYMLINK_NOFOLLOW    -> EINVAL (unchanged semantics)
 *     - AT_SYMLINK_NOFOLLOW + F_OK     -> fstatat(AT_SYMLINK_NOFOLLOW) on the path
 *     - AT_SYMLINK_NOFOLLOW + R/W/X    -> fstatat, then R_OK/W_OK/X_OK against euid
 *   This is exact for the AT_EACCESS case in this environment: every Xfce process
 *   runs as root, so real vs effective uid/gid are equal and AT_EACCESS is a no-op.
 *
 * Build (host): python -m ziglang cc -target arm-linux-musleabihf -shared -fPIC
 *               -O2 -o young2-faccessat-shim.so young2-faccessat-shim.c
 */

#define _GNU_SOURCE
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <dlfcn.h>
#include <string.h>

typedef int (*faccessat_fn_t)(int, const char *, int, int);

static faccessat_fn_t real_faccessat;

static int check_access_bits(mode_t st_mode, int amode)
{
    /* euid == 0: everything except the X bit on non-executable files */
    if (amode & R_OK) {
        if (!(st_mode & (S_IRUSR | S_IRGRP | S_IROTH))) { errno = EACCES; return -1; }
    }
    if (amode & W_OK) {
        if (!(st_mode & (S_IWUSR | S_IWGRP | S_IWOTH))) { errno = EACCES; return -1; }
    }
    if (amode & X_OK) {
        if (!(st_mode & (S_IXUSR | S_IXGRP | S_IXOTH))) { errno = EACCES; return -1; }
    }
    return 0;
}

int faccessat(int dirfd, const char *pathname, int mode, int flags)
{
    if (!real_faccessat) {
        real_faccessat = (faccessat_fn_t)dlsym(RTLD_NEXT, "faccessat");
        if (!real_faccessat) {
            errno = ENOSYS;
            return -1;
        }
    }

    if (flags & ~(AT_SYMLINK_NOFOLLOW | AT_EACCESS)) {
        /* A flag we cannot emulate: preserve musl's EINVAL answer. */
        errno = EINVAL;
        return -1;
    }

    if (flags & AT_SYMLINK_NOFOLLOW) {
        /* Implement F_OK/R_OK/W_OK/X_OK via fstatat(AT_SYMLINK_NOFOLLOW).
         * AT_EACCESS is equivalent to the real-uid check here because every
         * process on this device runs as root (euid == uid). If that ever
         * stops holding, bail with musl's EINVAL rather than lie. */
        if (getuid() != geteuid() || getgid() != getegid()) {
            errno = EINVAL;
            return -1;
        }
        struct stat st;
        if (fstatat(dirfd, pathname, &st, AT_SYMLINK_NOFOLLOW) != 0)
            return -1; /* errno set by fstatat (ENOENT etc.) */
        return check_access_bits(st.st_mode, mode);
    }

    /* flags == 0, or AT_EACCESS only: with euid==uid musl's own flag==0
     * path gives the identical answer, without the faccessat2 probe. */
    if (flags == AT_EACCESS &&
        (getuid() != geteuid() || getgid() != getegid())) {
        errno = EINVAL;
        return -1;
    }
    return real_faccessat(dirfd, pathname, mode, 0);
}
