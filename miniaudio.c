/*
note: miniaudio itself is a single-header-file library,
and all definitions and code is already included in the
build_ffi_module bootstrap c module code
*/


#include <stdlib.h>
#include <stdint.h>

#include "miniaudio/stb_vorbis.c"


#ifdef _WIN32
int setenv(const char *name, const char *value, int overwrite)
{
    int errcode = 0;
    if(!overwrite) {
        size_t envsize = 0;
        errcode = getenv_s(&envsize, NULL, 0, name);
        if(errcode || envsize) return errcode;
    }
    return _putenv_s(name, value);
}
#endif

void init_miniaudio(void) {

    /*
    Currently, no specific init is needed. For older version of miniaudio, we had this:

    This is needed to avoid a huge multi second delay when using PulseAudio (without the minreq value patch)
    It seems to be related to the pa_buffer_attr->minreq value
    See https://freedesktop.org/software/pulseaudio/doxygen/structpa__buffer__attr.html#acdbe30979a50075479ee46c56cc724ee
    and https://github.com/pulseaudio/pulseaudio/blob/4e3a080d7699732be9c522be9a96d851f97fbf11/src/pulse/stream.c#L989

    setenv("PULSE_LATENCY_MSEC", "100", 0);
    */
}


/* Nothing more to do here; all the decoder source is in their own single source/include file */
