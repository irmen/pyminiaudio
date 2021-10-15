"""
Python interface to the miniaudio library (https://github.com/dr-soft/miniaudio)

This module uses CFFI to create the glue code but also to actually compile the decoders in one go!

Sound formats supported: wav, mp3, flac, ogg vorbis

Author: Irmen de Jong (irmen@razorvine.net)
Software license: "MIT software license". See http://opensource.org/licenses/MIT
"""


import os
import platform
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
int stb_vorbis_get_samples_float_interleaved(stb_vorbis *f, int channels, float *buffer, int num_floats);
int stb_vorbis_get_samples_short_interleaved(stb_vorbis *f, int channels, short *buffer, int num_shorts);


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




typedef int ma_result;
/* General errors. */
#define MA_SUCCESS                                      0
#define MA_ERROR                                       -1   /* A generic error. */
#define MA_INVALID_ARGS                                -2
#define MA_INVALID_OPERATION                           -3
#define MA_OUT_OF_MEMORY                               -4
#define MA_OUT_OF_RANGE                                -5
#define MA_ACCESS_DENIED                               -6
#define MA_DOES_NOT_EXIST                              -7
#define MA_ALREADY_EXISTS                              -8
#define MA_TOO_MANY_OPEN_FILES                         -9
#define MA_INVALID_FILE                                -10
#define MA_TOO_BIG                                     -11
#define MA_PATH_TOO_LONG                               -12
#define MA_NAME_TOO_LONG                               -13
#define MA_NOT_DIRECTORY                               -14
#define MA_IS_DIRECTORY                                -15
#define MA_DIRECTORY_NOT_EMPTY                         -16
#define MA_AT_END                                      -17
#define MA_NO_SPACE                                    -18
#define MA_BUSY                                        -19
#define MA_IO_ERROR                                    -20
#define MA_INTERRUPT                                   -21
#define MA_UNAVAILABLE                                 -22
#define MA_ALREADY_IN_USE                              -23
#define MA_BAD_ADDRESS                                 -24
#define MA_BAD_SEEK                                    -25
#define MA_BAD_PIPE                                    -26
#define MA_DEADLOCK                                    -27
#define MA_TOO_MANY_LINKS                              -28
#define MA_NOT_IMPLEMENTED                             -29
#define MA_NO_MESSAGE                                  -30
#define MA_BAD_MESSAGE                                 -31
#define MA_NO_DATA_AVAILABLE                           -32
#define MA_INVALID_DATA                                -33
#define MA_TIMEOUT                                     -34
#define MA_NO_NETWORK                                  -35
#define MA_NOT_UNIQUE                                  -36
#define MA_NOT_SOCKET                                  -37
#define MA_NO_ADDRESS                                  -38
#define MA_BAD_PROTOCOL                                -39
#define MA_PROTOCOL_UNAVAILABLE                        -40
#define MA_PROTOCOL_NOT_SUPPORTED                      -41
#define MA_PROTOCOL_FAMILY_NOT_SUPPORTED               -42
#define MA_ADDRESS_FAMILY_NOT_SUPPORTED                -43
#define MA_SOCKET_NOT_SUPPORTED                        -44
#define MA_CONNECTION_RESET                            -45
#define MA_ALREADY_CONNECTED                           -46
#define MA_NOT_CONNECTED                               -47
#define MA_CONNECTION_REFUSED                          -48
#define MA_NO_HOST                                     -49
#define MA_IN_PROGRESS                                 -50
#define MA_CANCELLED                                   -51
#define MA_MEMORY_ALREADY_MAPPED                       -52

/* General miniaudio-specific errors. */
#define MA_FORMAT_NOT_SUPPORTED                        -100
#define MA_DEVICE_TYPE_NOT_SUPPORTED                   -101
#define MA_SHARE_MODE_NOT_SUPPORTED                    -102
#define MA_NO_BACKEND                                  -103
#define MA_NO_DEVICE                                   -104
#define MA_API_NOT_FOUND                               -105
#define MA_INVALID_DEVICE_CONFIG                       -106
#define MA_LOOP                                        -107

/* State errors. */
#define MA_DEVICE_NOT_INITIALIZED                      -200
#define MA_DEVICE_ALREADY_INITIALIZED                  -201
#define MA_DEVICE_NOT_STARTED                          -202
#define MA_DEVICE_NOT_STOPPED                          -203

/* Operation errors. */
#define MA_FAILED_TO_INIT_BACKEND                      -300
#define MA_FAILED_TO_OPEN_BACKEND_DEVICE               -301
#define MA_FAILED_TO_START_BACKEND_DEVICE              -302
#define MA_FAILED_TO_STOP_BACKEND_DEVICE               -303


#define MA_MIN_CHANNELS                                1
#define MA_MAX_CHANNELS                                32
#define MA_MIN_SAMPLE_RATE                             8000
#define MA_MAX_SAMPLE_RATE                             384000


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
    ma_backend_custom,
    ma_backend_null    /* <-- Must always be the last item. Lowest priority, and used as the terminator for backend enumeration. */
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
    ma_format_unknown = 0,
    ma_format_u8      = 1,
    ma_format_s16     = 2,
    ma_format_s24     = 3,
    ma_format_s32     = 4,
    ma_format_f32     = 5,
    ma_format_count
} ma_format;


typedef enum
{
    ma_channel_mix_mode_rectangular = 0,   /* Simple averaging based on the plane(s) the channel is sitting on. */
    ma_channel_mix_mode_simple,            /* Drop excess channels; zeroed out extra channels. */
    ma_channel_mix_mode_custom_weights,    /* Use custom weights specified in ma_channel_router_config. */
    ma_channel_mix_mode_planar_blend = ma_channel_mix_mode_rectangular,
    ma_channel_mix_mode_default = ma_channel_mix_mode_planar_blend
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
    ma_share_mode_shared = 0,
    ma_share_mode_exclusive
} ma_share_mode;


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

typedef ma_uint8 ma_channel;
typedef struct ma_device ma_device;
typedef struct ma_decoder ma_decoder;

typedef void (* ma_device_callback_proc)(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
typedef void (* ma_stop_proc)(ma_device* pDevice);
typedef void (* ma_log_proc)(ma_context* pContext, ma_device* pDevice, ma_uint32 logLevel, const char* message);
typedef size_t    (* ma_decoder_read_proc) (ma_decoder* pDecoder, void* pBufferOut, size_t bytesToRead); /* Returns the number of bytes read. */
typedef ma_bool32 (* ma_decoder_seek_proc) (ma_decoder* pDecoder, ma_int64 byteOffset, ma_seek_origin origin);


struct ma_device {

    ma_context* pContext;
    ma_device_type type;
    ma_uint32 sampleRate;
    volatile ma_uint32 state;               /* The state of the device is variable and can change at any time on any thread, so tell the compiler as such with `volatile`. */
    ma_device_callback_proc onData;         /* Set once at initialization time and should not be changed after. */
    ma_stop_proc onStop;                    /* Set once at initialization time and should not be changed after. */
    void* pUserData;                        /* Application defined data. */
    volatile float masterVolumeFactor;      /* Volatile so we can use some thread safety when applying volume to periods. */
    ...;
    
};


typedef struct
{
    ma_device_id id;
    char name[256];
    ma_bool32 isDefault;
    ma_uint32 formatCount;
    ma_format formats[ma_format_count];
    ma_uint32 minChannels;
    ma_uint32 maxChannels;
    ma_uint32 minSampleRate;
    ma_uint32 maxSampleRate;

    ...;
} ma_device_info;



typedef struct
{
    ma_device_type deviceType;
    ma_uint32 sampleRate;
    ma_uint32 periodSizeInFrames;
    ma_uint32 periodSizeInMilliseconds;
    ma_uint32 periods;
    ma_bool8 noPreZeroedOutputBuffer;   /* When set to true, the contents of the output buffer passed into the data callback will be left undefined rather than initialized to zero. */
    ma_bool8 noClip;                    /* When set to true, the contents of the output buffer passed into the data callback will be clipped after returning. Only applies when the playback sample format is f32. */
    ma_device_callback_proc dataCallback;
    ma_stop_proc stopCallback;
    void* pUserData;
    struct
    {
        const ma_device_id* pDeviceID;
        ma_format format;
        ma_uint32 channels;
        ma_channel channelMap[MA_MAX_CHANNELS];
        ma_channel_mix_mode channelMixMode;
        ma_share_mode shareMode;
    } playback;
    struct
    {
        const ma_device_id* pDeviceID;
        ma_format format;
        ma_uint32 channels;
        ma_channel channelMap[MA_MAX_CHANNELS];
        ma_channel_mix_mode channelMixMode;
        ma_share_mode shareMode;
    } capture;

    struct
    {
        ma_bool8 noAutoConvertSRC;     /* When set to true, disables the use of AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM. */
        ma_bool8 noDefaultQualitySRC;  /* When set to true, disables the use of AUDCLNT_STREAMFLAGS_SRC_DEFAULT_QUALITY. */
        ma_bool8 noAutoStreamRouting;  /* Disables automatic stream routing. */
        ma_bool8 noHardwareOffloading; /* Disables WASAPI's hardware offloading feature. */
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
    ma_channel channelMapIn[MA_MAX_CHANNELS];
    ma_channel channelMapOut[MA_MAX_CHANNELS];
    ma_dither_mode ditherMode;
    ma_channel_mix_mode channelMixMode;
    float channelWeights[MA_MAX_CHANNELS][MA_MAX_CHANNELS];  /* [in][out]. Only used when channelMixMode is set to ma_channel_mix_mode_custom_weights. */
    
    ...;
} ma_data_converter_config;


typedef struct
{
    ma_data_converter_config config;
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
    ma_result ma_context_get_device_info(ma_context* pContext, ma_device_type deviceType, const ma_device_id* pDeviceID, ma_share_mode shareMode, ma_device_info* pDeviceInfo);
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
    ma_result ma_decoder_init_wav(ma_decoder_read_proc onRead, ma_decoder_seek_proc onSeek, void* pUserData, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_flac(ma_decoder_read_proc onRead, ma_decoder_seek_proc onSeek, void* pUserData, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_vorbis(ma_decoder_read_proc onRead, ma_decoder_seek_proc onSeek, void* pUserData, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_mp3(ma_decoder_read_proc onRead, ma_decoder_seek_proc onSeek, void* pUserData, const ma_decoder_config* pConfig, ma_decoder* pDecoder);

    ma_result ma_decoder_init_memory(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_memory_wav(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_memory_flac(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_memory_vorbis(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_memory_mp3(const void* pData, size_t dataSize, const ma_decoder_config* pConfig, ma_decoder* pDecoder);

    ma_result ma_decoder_init_file(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_wav(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_flac(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_vorbis(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_mp3(const char* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);

    ma_result ma_decoder_init_file_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_wav_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_flac_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_vorbis_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);
    ma_result ma_decoder_init_file_mp3_w(const wchar_t* pFilePath, const ma_decoder_config* pConfig, ma_decoder* pDecoder);

    ma_result ma_decoder_uninit(ma_decoder* pDecoder);
    ma_uint64 ma_decoder_get_length_in_pcm_frames(ma_decoder* pDecoder);
    ma_result ma_decoder_get_available_frames(ma_decoder* pDecoder, ma_uint64* pAvailableFrames);
    ma_uint64 ma_decoder_read_pcm_frames(ma_decoder* pDecoder, void* pFramesOut, ma_uint64 frameCount);
    ma_result ma_decoder_seek_to_pcm_frame(ma_decoder* pDecoder, ma_uint64 frameIndex);
    ma_result ma_decode_file(const char* pFilePath, ma_decoder_config* pConfig, ma_uint64* pFrameCountOut, void** ppDataOut);
    ma_result ma_decode_memory(const void* pData, size_t dataSize, ma_decoder_config* pConfig, ma_uint64* pFrameCountOut, void** ppDataOut);

    /**** format conversion ****/
    void ma_pcm_convert(void* pOut, ma_format formatOut, const void* pIn, ma_format formatIn, ma_uint64 sampleCount, ma_dither_mode ditherMode);
    void ma_deinterleave_pcm_frames(ma_format format, ma_uint32 channels, ma_uint64 frameCount, const void* pInterleavedPCMFrames, void** ppDeinterleavedPCMFrames);
    void ma_interleave_pcm_frames(ma_format format, ma_uint32 channels, ma_uint64 frameCount, const void** ppDeinterleavedPCMFrames, void* pInterleavedPCMFrames);

    ma_uint64 ma_convert_frames(void* pOut, ma_uint64 frameCountOut, ma_format formatOut, ma_uint32 channelsOut, ma_uint32 sampleRateOut, const void* pIn, ma_uint64 frameCountIn, ma_format formatIn, ma_uint32 channelsIn, ma_uint32 sampleRateIn);
    ma_uint64 ma_convert_frames_ex(void* pOut, ma_uint64 frameCountOut, const void* pIn, ma_uint64 frameCountIn, const ma_data_converter_config* pConfig);
    ma_uint64 ma_calculate_frame_count_after_resampling(ma_uint32 sampleRateOut, ma_uint32 sampleRateIn, ma_uint64 frameCountIn);


    /*** channel maps ***/
    void ma_get_standard_channel_map(ma_standard_channel_map standardChannelMap, ma_uint32 channels, ma_channel channelMap[MA_MAX_CHANNELS]);
    void ma_channel_map_copy(ma_channel* pOut, const ma_channel* pIn, ma_uint32 channels);
    ma_bool32 ma_channel_map_valid(ma_uint32 channels, const ma_channel channelMap[MA_MAX_CHANNELS]);
    ma_bool32 ma_channel_map_equal(ma_uint32 channels, const ma_channel channelMapA[MA_MAX_CHANNELS], const ma_channel channelMapB[MA_MAX_CHANNELS]);
    ma_bool32 ma_channel_map_blank(ma_uint32 channels, const ma_channel channelMap[MA_MAX_CHANNELS]);
    ma_bool32 ma_channel_map_contains_channel_position(ma_uint32 channels, const ma_channel channelMap[MA_MAX_CHANNELS], ma_channel channelPosition);

    /*** streaming sound conversion ***/
    ma_data_converter_config ma_data_converter_config_init_default(void);
    ma_data_converter_config ma_data_converter_config_init(ma_format formatIn, ma_format formatOut, ma_uint32 channelsIn, ma_uint32 channelsOut, ma_uint32 sampleRateIn, ma_uint32 sampleRateOut);
    ma_result ma_data_converter_init(const ma_data_converter_config* pConfig, ma_data_converter* pConverter);
    void ma_data_converter_uninit(ma_data_converter* pConverter);
    ma_result ma_data_converter_process_pcm_frames(ma_data_converter* pConverter, const void* pFramesIn, ma_uint64* pFrameCountIn, void* pFramesOut, ma_uint64* pFrameCountOut);
    ma_result ma_data_converter_set_rate(ma_data_converter* pConverter, ma_uint32 sampleRateIn, ma_uint32 sampleRateOut);
    ma_result ma_data_converter_set_rate_ratio(ma_data_converter* pConverter, float ratioInOut);
    ma_uint64 ma_data_converter_get_required_input_frame_count(ma_data_converter* pConverter, ma_uint64 outputFrameCount);
    ma_uint64 ma_data_converter_get_expected_output_frame_count(ma_data_converter* pConverter, ma_uint64 inputFrameCount);
    ma_uint64 ma_data_converter_get_input_latency(ma_data_converter* pConverter);
    ma_uint64 ma_data_converter_get_output_latency(ma_data_converter* pConverter);


    /**** misc ****/
    const char* ma_version_string(void);
    ma_bool32 ma_is_backend_enabled(ma_backend backend);
    ma_result ma_get_enabled_backends(ma_backend* pBackends, size_t backendCap, size_t* pBackendCount);
    ma_bool32 ma_is_loopback_supported(ma_backend backend);
    
    const char* ma_get_backend_name(ma_backend backend);
    const char* ma_get_format_name(ma_format format);
    void ma_zero_pcm_frames(void* p, ma_uint32 frameCount, ma_format format, ma_uint32 channels);
    void ma_free(void* p, const ma_allocation_callbacks* pAllocationCallbacks);

    void init_miniaudio(void);
    void *malloc(size_t size);
    void free(void *ptr);

    /**** callbacks ****/
    extern "Python" void _internal_data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
    extern "Python" void _internal_stop_callback(ma_device* pDevice);
    
    /* decoder read and seek callbacks */
    extern "Python" size_t _internal_decoder_read_callback(ma_decoder* pDecoder, void* pBufferOut, size_t bytesToRead);
    extern "Python" ma_bool32 _internal_decoder_seek_callback(ma_decoder* pDecoder, ma_int64 byteOffset, ma_seek_origin origin);
"""

# TODO: expose and support filter API,  expose and support waveform and noise generation APIs.


ffibuilder = FFI()
ffibuilder.cdef(vorbis_defs + miniaudio_defs)

compiler_args = []
libraries = []

if os.name == "posix":
    compiler_args = ["-g1", "-O3", "-ffast-math"]
    libraries = ["m", "pthread", "dl"]

    # determine appropriate compiler tuning options
    if platform.system() == "Darwin":
        compiler_args += []         # apple compiler doesn't seem to like any tune/cpu options
    elif "ppc64" in platform.system():
        compiler_args += ["-mcpu=native"]
    else:
        compiler_args += ["-mtune=native", "-march=native"]


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
                          ("MA_NO_GENERATION", "1"),
                          ("MA_NO_ENCODING", "1")
                      ]
                    )


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
