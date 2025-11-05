#include "sample.h"

#ifdef ENABLE_AUDIO
sample::sample(const std::string &path, int volume)
    : chunk(Mix_LoadWAV(path.c_str()), Mix_FreeChunk) {
    if (!chunk.get()) {
        // LOG("Couldn't load audio sample: ", path);
    }

    Mix_VolumeChunk(chunk.get(), volume);
}

// -1 here means we let SDL_mixer pick the first channel that is free
// If no channel is free it'll return an err code.
void sample::play() {
    Mix_PlayChannel(-1, chunk.get(), 0);
}

void sample::play(int times) {
    Mix_PlayChannel(-1, chunk.get(), times - 1);
}

void sample::set_volume(int volume) {
    Mix_VolumeChunk(chunk.get(), volume);
}
#else
// Stub implementations when audio is disabled
sample::sample(const std::string &path, int volume) {
    // No-op
}

void sample::play() {
    // No-op
}

void sample::play(int times) {
    // No-op
}

void sample::set_volume(int volume) {
    // No-op
}
#endif
