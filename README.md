Testing out sphinx generation from dynamically available content

The generator.py script searches assumes the existence of the folder chapters
It will then create a top index.rst containing a toc of all chapters it could find.
And for each chapter create a index.rst for that as well.

This folder can contain any number of folders and with any name.
What sets the ordering and naming of each chapter is the content of the .chapterconf file that exists in each subfolder.
If it exists the folder is treated as a chapter.
It should look like the following

```
[Chapter]
title = <Name of the chapter>
order = <Order, lower number places the chapter higher up>
```

Every .rst or .md file in each folder will be used as content.
Each file should contain

A content_order and a content_title

For a .rst file it should look like the following 
```
:content_order: <Order of the content file in the chapter>
:content_title: <Title of the content>
```

and for a .md file:
```
---
content_order: <Order of the content file in the chapter>
content_title: <Title of the content>
---
```
