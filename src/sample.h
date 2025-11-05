#ifndef SAMPLE_H
#define SAMPLE_H

// https://stackoverflow.com/questions/50240497/sdl-how-to-play-audio-asynchronously-in-c-without-stopping-code-execution

#include <string>
#include <memory>

#ifdef ENABLE_AUDIO
#include <SDL2/SDL_mixer.h>
#endif

class sample {
public:
    sample(const std::string &path, int volume);

    void play();

    void play(int times);

    void set_volume(int volume);

private:
#ifdef ENABLE_AUDIO
    std::unique_ptr<Mix_Chunk, void (*)(Mix_Chunk *)> chunk;
#endif
};

#endif //SAMPLE_H
