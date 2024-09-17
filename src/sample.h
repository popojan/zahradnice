#ifndef SAMPLE_H
#define SAMPLE_H

// https://stackoverflow.com/questions/50240497/sdl-how-to-play-audio-asynchronously-in-c-without-stopping-code-execution

#include <string>
#include <memory>
#include <SDL2/SDL_mixer.h>

class sample {
public:
    sample(const std::string &path, int volume);

    void play();

    void play(int times);

    void set_volume(int volume);

private:
    std::unique_ptr<Mix_Chunk, void (*)(Mix_Chunk *)> chunk;
};

#endif //SAMPLE_H
