#include <stdlib.h>
#include <stdint.h>

#ifndef NO_STB_VORBIS
/* #define STB_VORBIS_NO_PUSHDATA_API  */   /*  needed by miniaudio decoding logic  */
#define STB_VORBIS_HEADER_ONLY
#include "miniaudio/stb_vorbis.c"
#endif


#define DR_FLAC_IMPLEMENTATION
#define DR_FLAC_NO_OGG
#include "miniaudio/dr_flac.h"

#define DR_MP3_IMPLEMENTATION
#include "miniaudio/dr_mp3.h"

#define DR_WAV_IMPLEMENTATION
#include "miniaudio/dr_wav.h"

#define MINIAUDIO_IMPLEMENTATION
/* #define MA_NO_DECODING */
/* #define MA_NO_AAUDIO */
/* #define MA_NO_OPENSL */
/* #define MA_NO_JACK */
#define MA_NO_WEBAUDIO
#include "miniaudio/miniaudio.h"


#ifndef NO_STB_VORBIS
#undef STB_VORBIS_HEADER_ONLY		/* this time, do include vorbis implementation */
#include "miniaudio/stb_vorbis.c"
#endif


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
