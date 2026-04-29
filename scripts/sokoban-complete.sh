#!/bin/bash

cmd="python3 scripts/sokoban_level_generator_goal.py"

$cmd scripts/Microban.txt programs/sokoban/microban "Microban | © 2000 David W. Skinner | Level {Number}"
$cmd scripts/levels.txt programs/sokoban/yoshio-murase/ "Automatic Making of Sokoban Levels | © 1996 Yoshio Murase | Level {Number}"
$cmd scripts/Microcosmos.txt programs/sokoban/microcosmos "Microcosmos | © 2000 Aymeric du Peloux | Level {Number}"
$cmd scripts/Sokoban.txt programs/sokoban/original/ "Original 1980 Sōkoban by Hiroyuki Imabayashi | © 1982 Thinking Rabbitt | Level {Number}"


