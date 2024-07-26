# Website Search Tool
A program that crawls a website to produce an inverted index which is used to find the most relevant pages for an entered search phrase.

Compile and execute the programming by running the command below.
```shell
$ python main.py
```

## Commands
- build : builds and saves the index file for the website
- load : load a previously built index file
- display \<word\> : print the inverted index for the specified word in the index file
- find \<first word\> \<second word\> ... : search for pages that contain the specified word(s) ordered by the most relevant pages first
