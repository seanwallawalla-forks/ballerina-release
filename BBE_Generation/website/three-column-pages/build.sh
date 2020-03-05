#!/bin/sh
#nightly build script
echo ".....Building three column pages....."
if [ $OSTYPE == "msys" ];
    then
        mkdocs build && cp -r site/* $1/
    else
        mkdocs build; rsync -ir site/ $1/;
fi
echo "....Completed building three column pages...."