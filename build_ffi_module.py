"""
Python interface to the miniaudio library (https://github.com/dr-soft/miniaudio)

This module uses CFFI to create the glue code but also to actually compile the decoders in one go!

Sound formats supported: wav, mp3, flac, ogg vorbis

Author: Irmen de Jong (irmen@razorvine.net)
Software license: "MIT software license". See http://opensource.org/licenses/MIT
"""


import os
import subprocess
import shlex
from cffi import FFI

miniaudio_include_dir = os.getcwd()

vorbis_defs = """

/********************** stb_vorbis ******************************/

enum STBVorbisError
{
   VORBIS__no_error,

   VORBIS_need_more_data=1,             // not a real error

   VORBIS_invalid_api_mixing,           // can't mix API modes
   VORBIS_outofmem,                     // not enough memory
   VORBIS_feature_not_supported,        // uses floor 0
   VORBIS_too_many_channels,            // STB_VORBIS_MAX_CHANNELS is too small
   VORBIS_file_open_failure,            // fopen() failed
   VORBIS_seek_without_length,          // can't seek in unknown-length file

   VORBIS_unexpected_eof=10,            // file is truncated?
   VORBIS_seek_invalid,                 // seek past EOF

   // decoding errors (corrupt/invalid stream) -- you probably
   // don't care about the exact details of these

   // vorbis errors:
   VORBIS_invalid_setup=20,
   VORBIS_invalid_stream,

   // ogg errors:
   VORBIS_missing_capture_pattern=30,
   VORBIS_invalid_stream_structure_version,
   VORBIS_continued_packet_flag_invalid,
   VORBIS_incorrect_stream_serial_number,
   VORBIS_invalid_first_page,
   VORBIS_bad_packet_type,
   VORBIS_cant_find_last_page,
   VORBIS_seek_failed,
   VORBIS_ogg_skeleton_not_supported
};


typedef struct stb_vorbis stb_vorbis;

typedef struct
{
   unsigned int sample_rate;
   int channels;

   unsigned int setup_memory_required;
   unsigned int setup_temp_memory_required;
   unsigned int temp_memory_required;

   int max_frame_size;
} stb_vorbis_info;

typedef struct
{
   char *vendor;

   int comment_list_length;
   char **comment_list;
} stb_vorbis_comment;

typedef struct
{
   char *alloc_buffer;
   int   alloc_buffer_length_in_bytes;
} stb_vorbis_alloc;


stb_vorbis_info stb_vorbis_get_info(stb_vorbis *f);
stb_vorbis_comment stb_vorbis_get_comment(stb_vorbis *f);
int stb_vorbis_get_error(stb_vorbis *f);
void stb_vorbis_close(stb_vorbis *f);
int stb_vorbis_get_sample_offset(stb_vorbis *f);
unsigned int stb_vorbis_get_file_offset(stb_vorbis *f);

int stb_vorbis_decode_filename(const char *filename, int *channels, int *sample_rate, short **output);
int stb_vorbis_decode_memory(const unsigned char *mem, int len, int *channels, int *sample_rate, short **output);

stb_vorbis * stb_vorbis_open_memory(const unsigned char *data, int len, int *error, const stb_vorbis_alloc *alloc_buffer);
stb_vorbis * stb_vorbis_open_filename(const char *filename, int *error, const stb_vorbis_alloc *alloc_buffer);

int stb_vorbis_seek_frame(stb_vorbis *f, unsigned int sample_number);
int stb_vorbis_seek(stb_vorbis *f, unsigned int sample_number);
int stb_vorbis_seek_start(stb_vorbis *f);

unsigned int stb_vorbis_stream_length_in_samples(stb_vorbis *f);
float        stb_vorbis_stream_length_in_seconds(stb_vorbis *f);

int stb_vorbis_get_frame_short_interleaved(stb_vorbis *f, int num_c, short *buffer, int num_shorts);
int stb_vorbis_get_frame_short            (stb_vorbis *f, int num_c, short **buffer, int num_samples);
int stb_vorbis_get_samples_float_interleaved(stb_vorbis *f, int channels, float *buffer, int num_floats);
int stb_vorbis_get_samples_float(stb_vorbis *f, int channels, float **buffer, int num_samples);
int stb_vorbis_get_samples_short_interleaved(stb_vorbis *f, int channels, short *buffer, int num_shorts);
int stb_vorbis_get_samples_short(stb_vorbis *f, int channels, short **buffer, int num_samples);

"""

miniaudio_defs = """

/********************** dr_flac ******************************/

typedef   signed char           drflac_int8;
typedef unsigned char           drflac_uint8;
typedef   signed short          drflac_int16;
typedef unsigned short          drflac_uint16;
typedef   signed int            drflac_int32;
typedef unsigned int            drflac_uint32;
typedef   signed long long      drflac_int64;
typedef unsigned long long      drflac_uint64;
typedef drflac_uint8            drflac_bool8;
typedef drflac_uint32           drflac_bool32;

typedef struct
{
    drflac_uint32 sampleRate;
    drflac_uint8 channels;
    drflac_uint8 bitsPerSample;
    drflac_uint16 maxBlockSizeInPCMFrames;
    drflac_uint64 totalPCMFrameCount;

    ... ;

} drflac;

typedef struct {
    ... ;
} drflac_allocation_callbacks;


void drflac_close(drflac* pFlac);
drflac_uint64 drflac_read_pcm_frames_s32(drflac* pFlac, drflac_uint64 framesToRead, drflac_int32* pBufferOut);
drflac_uint64 drflac_read_pcm_frames_s16(drflac* pFlac, drflac_uint64 framesToRead, drflac_int16* pBufferOut);
drflac_uint64 drflac_read_pcm_frames_f32(drflac* pFlac, drflac_uint64 framesToRead, float* pBufferOut);
drflac_bool32 drflac_seek_to_pcm_frame(drflac* pFlac, drflac_uint64 pcmFrameIndex);
drflac* drflac_open_file(const char* filename, const drflac_allocation_callbacks* pAllocationCallbacks);
drflac* drflac_open_memory(const void* data, size_t dataSize, const drflac_allocation_callbacks* pAllocationCallbacks);
drflac_int32* drflac_open_file_and_read_pcm_frames_s32(const char* filename, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
drflac_int16* drflac_open_file_and_read_pcm_frames_s16(const char* filename, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
float* drflac_open_file_and_read_pcm_frames_f32(const char* filename, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
drflac_int32* drflac_open_memory_and_read_pcm_frames_s32(const void* data, size_t dataSize, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
drflac_int16* drflac_open_memory_and_read_pcm_frames_s16(const void* data, size_t dataSize, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
float* drflac_open_memory_and_read_pcm_frames_f32(const void* data, size_t dataSize, unsigned int* channels, unsigned int* sampleRate, drflac_uint64* totalPCMFrameCount, const drflac_allocation_callbacks* pAllocationCallbacks);
void drflac_free(void* p, const drflac_allocation_callbacks* pAllocationCallbacks);


/********************** dr_mp3 **********************************/

typedef   signed char           drmp3_int8;
typedef unsigned char           drmp3_uint8;
typedef   signed short          drmp3_int16;
typedef unsigned short          drmp3_uint16;
typedef   signed int            drmp3_int32;
typedef unsigned int            drmp3_uint32;
typedef   signed long long  drmp3_int64;
typedef unsigned long long  drmp3_uint64;
typedef drmp3_uint8      drmp3_bool8;
typedef drmp3_uint32     drmp3_bool32;


typedef struct
{
    drmp3_uint32 channels;
    drmp3_uint32 sampleRate;
} drmp3_config;

typedef struct
{
    drmp3_uint32 channels;
    drmp3_uint32 sampleRate;
    ...;
} drmp3;

typedef struct {
    ...;
} drmp3_allocation_callbacks;

drmp3_bool32 drmp3_init_memory(drmp3* pMP3, const void* pData, size_t dataSize, const drmp3_allocation_callbacks* pAllocationCallbacks);
drmp3_bool32 drmp3_init_file(drmp3* pMP3, const char* filePath, const drmp3_allocation_callbacks* pAllocationCallbacks);
void drmp3_uninit(drmp3* pMP3);

drmp3_uint64 drmp3_read_pcm_frames_f32(drmp3* pMP3, drmp3_uint64 framesToRead, float* pBufferOut);
drmp3_uint64 drmp3_read_pcm_frames_s16(drmp3* pMP3, drmp3_uint64 framesToRead, drmp3_int16* pBufferOut);
drmp3_bool32 drmp3_seek_to_pcm_frame(drmp3* pMP3, drmp3_uint64 frameIndex);
drmp3_uint64 drmp3_get_pcm_frame_count(drmp3* pMP3);
drmp3_uint64 drmp3_get_mp3_frame_count(drmp3* pMP3);
drmp3_bool32 drmp3_get_mp3_and_pcm_frame_count(drmp3* pMP3, drmp3_uint64* pMP3FrameCount, drmp3_uint64* pPCMFrameCount);

float* drmp3_open_memory_and_read_pcm_frames_f32(const void* pData, size_t dataSize, drmp3_config* pConfig, drmp3_uint64* pTotalFrameCount, const drmp3_allocation_callbacks* pAllocationCallbacks);
drmp3_int16* drmp3_open_memory_and_read_pcm_frames_s16(const void* pData, size_t dataSize, drmp3_config* pConfig, drmp3_uint64* pTotalFrameCount, const drmp3_allocation_callbacks* pAllocationCallbacks);
float* drmp3_open_file_and_read_pcm_frames_f32(const char* filePath, drmp3_config* pConfig, drmp3_uint64* pTotalFrameCount, const drmp3_allocation_callbacks* pAllocationCallbacks);
drmp3_int16* drmp3_open_file_and_read_pcm_frames_s16(const char* filePath, drmp3_config* pConfig, drmp3_uint64* pTotalFrameCount, const drmp3_allocation_callbacks* pAllocationCallbacks);
void drmp3_free(void* p, const drmp3_allocation_callbacks* pAllocationCallbacks);



/********************** dr_wav **********************************/

/* Common data formats. */
#define DR_WAVE_FORMAT_PCM          0x1
#define DR_WAVE_FORMAT_ADPCM        0x2
#define DR_WAVE_FORMAT_IEEE_FLOAT   0x3
#define DR_WAVE_FORMAT_ALAW         0x6
#define DR_WAVE_FORMAT_MULAW        0x7
#define DR_WAVE_FORMAT_DVI_ADPCM    0x11
#define DR_WAVE_FORMAT_EXTENSIBLE   0xFFFE

typedef   signed char           drwav_int8;
typedef unsigned char           drwav_uint8;
typedef   signed short          drwav_int16;
typedef unsigned short          drwav_uint16;
typedef   signed int            drwav_int32;
typedef unsigned int            drwav_uint32;
typedef   signed long long  drwav_int64;
typedef unsigned long long  drwav_uint64;
typedef drwav_uint8             drwav_bool8;
typedef drwav_uint32            drwav_bool32;


typedef struct
{
    drwav_uint32 sampleRate;
    drwav_uint16 channels;
    drwav_uint16 bitsPerSample;
    drwav_uint16 translatedFormatTag;
    drwav_uint64 totalPCMFrameCount;

    ...;

} drwav;

typedef enum
{
    drwav_container_riff,
    drwav_container_w64
} drwav_container;

typedef struct
{
    drwav_container container;  /* RIFF, W64. */
    drwav_uint32 format;        /* DR_WAVE_FORMAT_* */
    drwav_uint32 channels;
    drwav_uint32 sampleRate;
    drwav_uint32 bitsPerSample;
} drwav_data_format;

typedef struct {
    ...;
} drwav_allocation_callbacks;

drwav_bool32 drwav_init_file(drwav* pWav, const char* filename, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_memory(drwav* pWav, const void* data, size_t dataSize, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_int32 drwav_uninit(drwav* pWav);
void drwav_free(void* p, const drwav_allocation_callbacks* pAllocationCallbacks);

drwav_bool32 drwav_init_file_write(drwav* pWav, const char* filename, const drwav_data_format* pFormat, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_file_write_sequential(drwav* pWav, const char* filename, const drwav_data_format* pFormat, drwav_uint64 totalSampleCount, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_file_write_sequential_pcm_frames(drwav* pWav, const char* filename, const drwav_data_format* pFormat, drwav_uint64 totalPCMFrameCount, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_memory_write(drwav* pWav, void** ppData, size_t* pDataSize, const drwav_data_format* pFormat, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_memory_write_sequential(drwav* pWav, void** ppData, size_t* pDataSize, const drwav_data_format* pFormat, drwav_uint64 totalSampleCount, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_bool32 drwav_init_memory_write_sequential_pcm_frames(drwav* pWav, void** ppData, size_t* pDataSize, const drwav_data_format* pFormat, drwav_uint64 totalPCMFrameCount, const drwav_allocation_callbacks* pAllocationCallbacks);


drwav_uint64 drwav_read_pcm_frames(drwav* pWav, drwav_uint64 framesToRead, void* pBufferOut);
drwav_uint64 drwav_write_pcm_frames(drwav* pWav, drwav_uint64 framesToWrite, const void* pData);
drwav_bool32 drwav_seek_to_pcm_frame(drwav* pWav, drwav_uint64 targetFrameIndex);
drwav_uint64 drwav_read_pcm_frames_s16(drwav* pWav, drwav_uint64 framesToRead, drwav_int16* pBufferOut);
drwav_uint64 drwav_read_pcm_frames_f32(drwav* pWav, drwav_uint64 framesToRead, float* pBufferOut);
drwav_uint64 drwav_read_pcm_frames_s32(drwav* pWav, drwav_uint64 framesToRead, drwav_int32* pBufferOut);

drwav_int16* drwav_open_file_and_read_pcm_frames_s16(const char* filename, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);
float* drwav_open_file_and_read_pcm_frames_f32(const char* filename, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_int32* drwav_open_file_and_read_pcm_frames_s32(const char* filename, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);

drwav_int16* drwav_open_memory_and_read_pcm_frames_s16(const void* data, size_t dataSize, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);
float* drwav_open_memory_and_read_pcm_frames_f32(const void* data, size_t dataSize, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);
drwav_int32* drwav_open_memory_and_read_pcm_frames_s32(const void* data, size_t dataSize, unsigned int* channelsOut, unsigned int* sampleRateOut, drwav_uint64* totalFrameCountOut, const drwav_allocation_callbacks* pAllocationCallbacks);



typedef enum
{
    MA_SUCCESS                        =  0,
    MA_ERROR                          = -1,  /* A generic error. */
    MA_INVALID_ARGS                   = -2,
    MA_INVALID_OPERATION              = -3,
    MA_OUT_OF_MEMORY                  = -4,
    MA_OUT_OF_RANGE                   = -5,
    MA_ACCESS_DENIED                  = -6,
    MA_DOES_NOT_EXIST                 = -7,
    MA_ALREADY_EXISTS                 = -8,
    MA_TOO_MANY_OPEN_FILES            = -9,
    MA_INVALID_FILE                   = -10,
    MA_TOO_BIG                        = -11,
    MA_PATH_TOO_LONG                  = -12,
    MA_NAME_TOO_LONG                  = -13,
    MA_NOT_DIRECTORY                  = -14,
    MA_IS_DIRECTORY                   = -15,
    MA_DIRECTORY_NOT_EMPTY            = -16,
    MA_AT_END                         = -17,
    MA_NO_SPACE                       = -18,
    MA_BUSY                           = -19,
    MA_IO_ERROR                       = -20,
    MA_INTERRUPT                      = -21,
    MA_UNAVAILABLE                    = -22,
    MA_ALREADY_IN_USE                 = -23,
    MA_BAD_ADDRESS                    = -24,
    MA_BAD_SEEK                       = -25,
    MA_BAD_PIPE                       = -26,
    MA_DEADLOCK                       = -27,
    MA_TOO_MANY_LINKS                 = -28,
    MA_NOT_IMPLEMENTED                = -29,
    MA_NO_MESSAGE                     = -30,
    MA_BAD_MESSAGE                    = -31,
    MA_NO_DATA_AVAILABLE              = -32,
    MA_INVALID_DATA                   = -33,
    MA_TIMEOUT                        = -34,
    MA_NO_NETWORK                     = -35,
    MA_NOT_UNIQUE                     = -36,
    MA_NOT_SOCKET                     = -37,
    MA_NO_ADDRESS                     = -38,
    MA_BAD_PROTOCOL                   = -39,
    MA_PROTOCOL_UNAVAILABLE           = -40,
    MA_PROTOCOL_NOT_SUPPORTED         = -41,
    MA_PROTOCOL_FAMILY_NOT_SUPPORTED  = -42,
    MA_ADDRESS_FAMILY_NOT_SUPPORTED   = -43,
    MA_SOCKET_NOT_SUPPORTED           = -44,
    MA_CONNECTION_RESET               = -45,
    MA_ALREADY_CONNECTED              = -46,
    MA_NOT_CONNECTED                  = -47,
    MA_CONNECTION_REFUSED             = -48,
    MA_NO_HOST                        = -49,
    MA_IN_PROGRESS                    = -50,
    MA_CANCELLED                      = -51,
    MA_MEMORY_ALREADY_MAPPED          = -52,

    /* General miniaudio-specific errors. */
    MA_FORMAT_NOT_SUPPORTED           = -100,
    MA_DEVICE_TYPE_NOT_SUPPORTED      = -101,
    MA_SHARE_MODE_NOT_SUPPORTED       = -102,
    MA_NO_BACKEND                     = -103,
    MA_NO_DEVICE                      = -104,
    MA_API_NOT_FOUND                  = -105,
    MA_INVALID_DEVICE_CONFIG          = -106,
    MA_LOOP                           = -107,

    /* State errors. */
    MA_DEVICE_NOT_INITIALIZED         = -200,
    MA_DEVICE_ALREADY_INITIALIZED     = -201,
    MA_DEVICE_NOT_STARTED             = -202,
    MA_DEVICE_NOT_STOPPED             = -203,

    /* Operation errors. */
    MA_FAILED_TO_INIT_BACKEND         = -300,
    MA_FAILED_TO_OPEN_BACKEND_DEVICE  = -301,
    MA_FAILED_TO_START_BACKEND_DEVICE = -302,
    MA_FAILED_TO_STOP_BACKEND_DEVICE  = -303
} ma_result; 


#define MA_MIN_CHANNELS                                1
#define MA_MAX_CHANNELS                                254


typedef enum
{
    ma_backend_wasapi,
    ma_backend_dsound,
    ma_backend_winmm,
    ma_backend_coreaudio,
    ma_backend_sndio,
    ma_backend_audio4,
    ma_backend_oss,
    ma_backend_pulseaudio,
    ma_backend_alsa,
    ma_backend_jack,
    ma_backend_aaudio,
    ma_backend_opensl,
    ma_backend_webaudio,
    ma_backend_custom,  /* <-- Custom backend, with callbacks defined by the context config. */
    ma_backend_null     /* <-- Must always be the last item. Lowest priority, and used as the terminator for backend enumeration. */
} ma_backend;

typedef   signed char           ma_int8;
typedef unsigned char           ma_uint8;
typedef   signed short          ma_int16;
typedef unsigned short          ma_uint16;
typedef   signed int            ma_int32;
typedef unsigned int            ma_uint32;
typedef   signed long long  ma_int64;
typedef unsigned long long  ma_uint64;
typedef ma_uint64           ma_uintptr;
typedef ma_uint8    ma_bool8;
typedef ma_uint32   ma_bool32;


typedef enum
{
    ma_dither_mode_none = 0,
    ma_dither_mode_rectangle,
    ma_dither_mode_triangle
} ma_dither_mode;


typedef enum
{
    ma_format_unknown = 0,     /* Mainly used for indicating an error, but also used as the default for the output format for decoders. */
    ma_format_u8      = 1,
    ma_format_s16     = 2,     /* Seems to be the most widely supported format. */
    ma_format_s24     = 3,     /* Tightly packed. 3 bytes per sample. */
    ma_format_s32     = 4,
    ma_format_f32     = 5,
    ma_format_count
} ma_format;


typedef enum
{
    ma_channel_mix_mode_rectangular = 0,   /* Simple averaging based on the plane(s) the channel is sitting on. */
    ma_channel_mix_mode_simple,            /* Drop excess channels; zeroed out extra channels. */
    ma_channel_mix_mode_custom_weights,    /* Use custom weights specified in ma_channel_router_config. */
    ma_channel_mix_mode_default = ma_channel_mix_mode_rectangular
} ma_channel_mix_mode;

typedef enum
{
    ma_standard_channel_map_microsoft,
    ma_standard_channel_map_alsa,
    ma_standard_channel_map_rfc3551,   /* Based off AIFF. */
    ma_standard_channel_map_flac,
    ma_standard_channel_map_vorbis,
    ma_standard_channel_map_sound4,    /* FreeBSD's sound(4). */
    ma_standard_channel_map_sndio,     /* www.sndio.org/tips.html */
    ma_standard_channel_map_webaudio = ma_standard_channel_map_flac, /* https://webaudio.github.io/web-audio-api/#ChannelOrdering. Only 1, 2, 4 and 6 channels are defined, but can fill in the gaps with logical assumptions. */
    ma_standard_channel_map_default = ma_standard_channel_map_microsoft
} ma_standard_channel_map;


typedef enum
{
    ma_thread_priority_idle     = -5,
    ma_thread_priority_lowest   = -4,
    ma_thread_priority_low      = -3,
    ma_thread_priority_normal   = -2,
    ma_thread_priority_high     = -1,
    ma_thread_priority_highest  =  0,
    ma_thread_priority_realtime =  1,
    ma_thread_priority_default  =  0
} ma_thread_priority;


typedef enum
{
    ma_device_type_playback = 1,
    ma_device_type_capture  = 2,
    ma_device_type_duplex   = 3,
    ma_device_type_loopback = 4
} ma_device_type;

typedef enum
{
    ma_device_state_uninitialized = 0,
    ma_device_state_stopped       = 1,  /* The device's default state after initialization. */
    ma_device_state_started       = 2,  /* The device is started and is requesting and/or delivering audio data. */
    ma_device_state_starting      = 3,  /* Transitioning from a stopped state to started. */
    ma_device_state_stopping      = 4   /* Transitioning from a started state to stopped. */
} ma_device_state;

typedef enum
{
    ma_encoding_format_unknown = 0,
    ma_encoding_format_wav,
    ma_encoding_format_flac,
    ma_encoding_format_mp3,
    ma_encoding_format_vorbis
} ma_encoding_format;

typedef enum
{
    ma_share_mode_shared = 0,
    ma_share_mode_exclusive
} ma_share_mode;

typedef enum
{
    ma_wasapi_usage_default = 0,
    ma_wasapi_usage_games,
    ma_wasapi_usage_pro_audio,
} ma_wasapi_usage;

typedef enum
{
    ma_seek_origin_start,
    ma_seek_origin_current
} ma_seek_origin;

typedef union ma_device_id {
    ...;
} ma_device_id;
typedef struct ma_context {
    ma_backend backend;
    ...;
} ma_context;

typedef struct ma_context ma_context;
typedef struct ma_device ma_device;

typedef enum
{
    ma_device_notification_type_started,
    ma_device_notification_type_stopped,
    ma_device_notification_type_rerouted,
    ma_device_notification_type_interruption_began,
    ma_device_notification_type_interruption_ended
} ma_device_notification_type;

typedef struct
{
    ma_device* pDevice;
    ma_device_notification_type type;
    union
    {
        struct
        {
            int _unused;
        } started;
        struct
        {
            int _unused;
        } stopped;
        struct
        {
            int _unused;
        } rerouted;
        struct
        {
            int _unused;
        } interruption;
    } data;
} ma_device_notification;


typedef ma_uint8 ma_channel;
typedef struct ma_device ma_device;
typedef struct ma_decoder ma_decoder;

typedef ma_result (* ma_decoder_read_proc)(ma_decoder* pDecoder, void* pBufferOut, size_t bytesToRead, size_t* pBytesRead);         /* Returns the number of bytes read. */
typedef ma_result (* ma_decoder_seek_proc)(ma_decoder* pDecoder, ma_int64 byteOffset, ma_seek_origin origin);
typedef ma_result (* ma_decoder_tell_proc)(ma_decoder* pDecoder, ma_int64* pCursor);
typedef void (* ma_device_data_proc)(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
typedef void (* ma_stop_proc)(ma_device* pDevice);  /* DEPRECATED. Use ma_device_notification_proc instead. */
typedef void (* ma_device_notification_proc)(const ma_device_notification* pNotification);


struct ma_device {

    ma_context* pContext;
    ma_device_type type;
    ma_uint32 sampleRate;
    volatile ma_device_state state;        /* The state of the device is variable and can change at any time on any thread. Must be used atomically. */
    void* pUserData;                        /* Application defined data. */
    volatile float masterVolumeFactor;     /* Linear 0..1. Can be read and written simultaneously by different threads. Must be used atomically. */
    ...;
    
};


typedef struct
{
    /* Basic info. This is the only information guaranteed to be filled in during device enumeration. */
    ma_device_id id;
    char name[256];
    ma_bool32 isDefault;

    ma_uint32 nativeDataFormatCount;
    struct
    {
        ma_format format;       /* Sample format. If set to ma_format_unknown, all sample formats are supported. */
        ma_uint32 channels;     /* If set to 0, all channels are supported. */
        ma_uint32 sampleRate;   /* If set to 0, all sample rates are supported. */
        ma_uint32 flags;        /* A combination of MA_DATA_FORMAT_FLAG_* flags. */
    } nativeDataFormats[64];
} ma_device_info;


typedef struct
{

    ma_device_type deviceType;
    ma_uint32 sampleRate;
    ma_uint32 periodSizeInFrames;
    ma_uint32 periodSizeInMilliseconds;
    ma_uint32 periods;
    ma_device_data_proc dataCallback;
    ma_device_notification_proc notificationCallback;
    ma_stop_proc stopCallback;
    void* pUserData;
    
    struct
    {
        const ma_device_id* pDeviceID;
        ma_format format;
        ma_uint32 channels;
        ma_channel* pChannelMap;
        ma_channel_mix_mode channelMixMode;
        ma_bool32 calculateLFEFromSpatialChannels;  /* When an output LFE channel is present, but no input LFE, set to true to set the output LFE to the average of all spatial channels (LR, FR, etc.). Ignored when an input LFE is present. */
        ma_share_mode shareMode;
    } playback;
    struct
    {
        const ma_device_id* pDeviceID;
        ma_format format;
        ma_uint32 channels;
        ma_channel* pChannelMap;
        ma_channel_mix_mode channelMixMode;
        ma_bool32 calculateLFEFromSpatialChannels;  /* When an output LFE channel is present, but no input LFE, set to true to set the output LFE to the average of all spatial channels (LR, FR, etc.). Ignored when an input LFE is present. */
        ma_share_mode shareMode;
    } capture;

    struct
    {
        ma_wasapi_usage usage;              /* When configured, uses Avrt APIs to set the thread characteristics. */
        ma_bool8 noAutoConvertSRC;          /* When set to true, disables the use of AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM. */
        ma_bool8 noDefaultQualitySRC;       /* When set to true, disables the use of AUDCLNT_STREAMFLAGS_SRC_DEFAULT_QUALITY. */
        ma_bool8 noAutoStreamRouting;       /* Disables automatic stream routing. */
        ma_bool8 noHardwareOffloading;      /* Disables WASAPI's hardware offloading feature. */
        ma_uint32 loopbackProcessID;        /* The process ID to include or exclude for loopback mode. Set to 0 to capture audio from all processes. Ignored when an explicit device ID is specified. */
        ma_bool8 loopbackProcessExclude;    /* When set to true, excludes the process specified by loopbackProcessID. By default, the process will be included. */
    } wasapi;
    struct
    {
        ma_bool32 noMMap;           /* Disables MMap mode. */
        ma_bool32 noAutoFormat;     /* Opens the ALSA device with SND_PCM_NO_AUTO_FORMAT. */
        ma_bool32 noAutoChannels;   /* Opens the ALSA device with SND_PCM_NO_AUTO_CHANNELS. */
        ma_bool32 noAutoResample;   /* Opens the ALSA device with SND_PCM_NO_AUTO_RESAMPLE. */
    } alsa;
    struct
    {
        const char* pStreamNamePlayback;
        const char* pStreamNameCapture;
    } pulse;
    
    ...;
    
} ma_device_config;


typedef struct
{
    ma_thread_priority threadPriority;
    void* pUserData;
    struct
    {
        ma_bool32 useVerboseDeviceEnumeration;
    } alsa;
    struct
    {
        const char* pApplicationName;
        const char* pServerName;
        ma_bool32 tryAutoSpawn; /* Enables autospawning of the PulseAudio daemon if necessary. */
    } pulse;
    struct
    {
        const char* pClientName;
        ma_bool32 tryStartServer;
    } jack;
    ...;
} ma_context_config;


typedef struct
{
    ma_format format;      /* Set to 0 or ma_format_unknown to use the stream's internal format. */
    ma_uint32 channels;    /* Set to 0 to use the stream's internal channels. */
    ma_uint32 sampleRate;  /* Set to 0 to use the stream's internal sample rate. */
    ma_encoding_format encodingFormat;
    ma_channel_mix_mode channelMixMode;
    ma_dither_mode ditherMode;
    ...;
} ma_decoder_config;


struct ma_decoder
{
    ma_decoder_read_proc onRead;
    ma_decoder_seek_proc onSeek;
    void* pUserData;
    ma_format  outputFormat;
    ma_uint32  outputChannels;
    ma_uint32  outputSampleRate;
    ...;
};


typedef struct
{
    ma_format formatIn;
    ma_format formatOut;
    ma_uint32 channelsIn;
    ma_uint32 channelsOut;
    ma_uint32 sampleRateIn;
    ma_uint32 sampleRateOut;
    ma_channel* pChannelMapIn;
    ma_channel* pChannelMapOut;
    ma_dither_mode ditherMode;
    ma_channel_mix_mode channelMixMode;
    float** ppChannelWeights;  /* [in][out]. Only used when mixingMode is set to ma_channel_mix_mode_custom_weights. */
    ma_bool32 allowDynamicSampleRate;
    ...;
} ma_data_converter_config;


typedef struct
{
    ma_format formatIn;
    ma_format formatOut;
    ma_uint32 channelsIn;
    ma_uint32 channelsOut;
    ma_uint32 sampleRateIn;
    ma_uint32 sampleRateOut;
    ma_dither_mode ditherMode;
    ...;
} ma_data_converter;


typedef struct
{
    ...;
} ma_allocation_callbacks;




typedef ma_bool32 (* ma_enum_devices_callback_proc)(ma_context* pContext, ma_device_type deviceType, const ma_device_info* pInfo, void* pUserData);


    /**** allocation / initialization / device control ****/
    ma_result ma_context_init(const ma_backend backends[], ma_uint32 backendCount, const ma_context_config* pConfig, ma_context* pContext);
    ma_result ma_context_uninit(ma_context* pContext);
    ma_result ma_context_enumerate_devices(ma_context* pContext, ma_enum_devices_callback_proc callback, void* pUserData);
    ma_result ma_context_get_devices(ma_context* pContext, ma_device_info** ppPlaybackDeviceInfos, ma_uint32* pPlaybackDeviceCount, ma_device_info** ppCaptureDeviceInfos, ma_uint32* pCaptureDeviceCount);
    ma_result ma_context_get_device_info(ma_context* pContext, ma_device_type deviceType, const ma_device_id* pDeviceID, ma_device_info* pDeviceInfo);
    ma_result ma_device_init(ma_context* pContext, const ma_device_config* pConfig, ma_device* pDevice);
    ma_result ma_device_init_ex(const ma_backend backends[], ma_uint32 backendCount, const ma_context_config* pContextConfig, const ma_device_config* pConfig, ma_device* pDevice);
    void ma_device_uninit(ma_device* pDevice);
    ma_result ma_device_start(ma_device* pDevice);
    ma_result ma_device_stop(ma_device* pDevice);
    ma_bool32 ma_device_is_started(ma_device* pDevice);
    ma_context_config ma_context_config_init(void);
    ma_device_config ma_device_config_init(ma_device_type deviceType);
    ma_decoder_config ma_decoder_config_init(ma_format outputFormat, ma_uint32 outputChannels, ma_uint32 outputSampleRate);

    /**** decoding ****/
    ma_result ma_decoder_init(ma_decoder_read_proc onRead, ma_decoder_seek_proc onSeek, void* pUserData, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_memory(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);

    ma_result ma_decoder_uninit(ma_decoder* pDecoder);
    ma_result ma_decoder_read_pcm_frames(ma_decoder* pDecoder, void* pFramesOut, ma_uint64 frameCount, ma_uint64* pFramesRead);
    ma_result ma_decoder_seek_to_pcm_frame(ma_decoder* pDecoder, ma_uint64 frameIndex);
    ma_result ma_decode_file(const char* pFilePath, ma_decoder_config* pConfig, ma_uint64* pFrameCountOut, void** ppDataOut);
    ma_result ma_decode_memory(const void* pData, size_t dataSize, ma_decoder_config* pConfig, ma_uint64* pFrameCountOut, void** ppDataOut);

    /**** format conversion ****/
    void ma_pcm_convert(void* pOut, ma_format formatOut, const void* pIn, ma_format formatIn, ma_uint64 sampleCount, ma_dither_mode ditherMode);

    ma_uint64 ma_convert_frames(void* pOut, ma_uint64 frameCountOut, ma_format formatOut, ma_uint32 channelsOut, ma_uint32 sampleRateOut, const void* pIn, ma_uint64 frameCountIn, ma_format formatIn, ma_uint32 channelsIn, ma_uint32 sampleRateIn);
    ma_uint64 ma_calculate_frame_count_after_resampling(ma_uint32 sampleRateOut, ma_uint32 sampleRateIn, ma_uint64 frameCountIn);


    /**** misc ****/
    const char* ma_version_string(void);
    ma_bool32 ma_is_backend_enabled(ma_backend backend);
    ma_result ma_get_enabled_backends(ma_backend* pBackends, size_t backendCap, size_t* pBackendCount);
    ma_bool32 ma_is_loopback_supported(ma_backend backend);
    
    const char* ma_get_backend_name(ma_backend backend);
    const char* ma_get_format_name(ma_format format);
    void ma_free(void* p, const ma_allocation_callbacks* pAllocationCallbacks);

    void init_miniaudio(void);
    void *malloc(size_t size);
    void free(void *ptr);

    /**** callbacks ****/
    extern "Python" void _internal_data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
    extern "Python" void _internal_stop_callback(ma_device* pDevice);
    
    /* decoder read and seek callbacks */
    extern "Python" ma_result _internal_decoder_read_callback(ma_decoder* pDecoder, void* pBufferOut, size_t bytesToRead, size_t* pBytesRead);
    extern "Python" ma_result _internal_decoder_seek_callback(ma_decoder* pDecoder, ma_int64 byteOffset, ma_seek_origin origin);
"""

# TODO: expose and support filter API,  expose and support waveform and noise generation APIs.


ffibuilder = FFI()
ffibuilder.cdef(vorbis_defs + miniaudio_defs)

compiler_args = []
libraries = []


def check_linker_need_libatomic():
    """
    Test if linker on system needs libatomic.
    This has been copied from https://github.com/grpc/grpc/blob/master/setup.py#L205
    """
    code_test = (b'#include <atomic>\n' +
                 b'int main() { return std::atomic<int64_t>{}; }')
    cxx = shlex.split(os.environ.get('CXX', 'c++'))
    cpp_test = subprocess.Popen(cxx + ['-x', 'c++', '-std=c++14', '-'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    cpp_test.communicate(input=code_test)
    if cpp_test.returncode == 0:
        return False
    # Double-check to see if -latomic actually can solve the problem.
    # https://github.com/grpc/grpc/issues/22491
    cpp_test = subprocess.Popen(cxx +
                                ['-x', 'c++', '-std=c++14', '-', '-latomic'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    cpp_test.communicate(input=code_test)
    return cpp_test.returncode == 0


if os.name == "posix":
    compiler_args = ["-g1", "-O3", "-ffast-math"]
    libraries = ["m", "pthread", "dl"]
    if check_linker_need_libatomic():
        libraries.append("atomic")
    if "PYMINIAUDIO_EXTRA_CFLAGS" in os.environ:
        compiler_args += shlex.split(os.environ.get("PYMINIAUDIO_EXTRA_CFLAGS", ""))

ffibuilder.set_source("_miniaudio", """
    #include <stdint.h>
    #include <stdlib.h>

    #define DR_FLAC_NO_OGG
    #define STB_VORBIS_HEADER_ONLY
    #include "miniaudio/stb_vorbis.c"

    #define MINIAUDIO_IMPLEMENTATION
    #include "miniaudio/miniaudio.h"

    /* low-level initialization */
    void init_miniaudio(void);

""",
                      sources=["miniaudio.c"],
                      include_dirs=[miniaudio_include_dir],
                      libraries=libraries,
                      extra_compile_args=compiler_args,
                      define_macros=[
                          ("MA_NO_GENERATION", "1"),        # waveform generation
                          ("MA_NO_ENCODING", "1"),          # audio encoding
                          ("MA_NO_RESOURCE_MANAGER", "1"),  # high level api
                          ("MA_NO_NODE_GRAPH", "1"),        # high level api
                          ("MA_NO_ENGINE", "1")             # high level api
                      ]
                    )


if __name__ == "__main__":
    print("NEED LIBATOMIC?", check_linker_need_libatomic())
    ffibuilder.compile(verbose=True)
