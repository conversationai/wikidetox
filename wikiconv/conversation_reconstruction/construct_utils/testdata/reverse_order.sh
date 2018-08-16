#!/bin/bash
for filename in page_*.json; do
    tac $filename > reversed_$filename
    echo $filename
done

