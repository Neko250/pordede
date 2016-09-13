Pordede download helper
=======================

A little script to download media from pordede.com.  It's a simple choose-an-option based UI, just try it out.

Requirements
------------

* You'll need a pordede active account
* You'll need an uploader account to download files
* Assuming JDownloader with the folderwatch plugin installed, to automatically monitor downloaded .dlc files.

    - Folderwatch is a useful plugin but difficult to setup with the provided info. A quick steps to set it up:
        - On the folder that you choose as 'folderwatch' in the config file, create a file "whatever.crawljob" with the
          following content:

            downloadFolder=/path/to/download/folder
            autoStart=TRUE
            extractAfterDownload=TRUE
            forcedStart=TRUE
            autoConfirm=TRUE

          Just choose the download folder you want. The plugin will read this file, and create a subfolder "added", and move the file
          inside that folder, renamed to "added/whatever.crawljob.1". Inside that folder, a copy of all downloaded .dlc files
          will remain. JDownloaded will automatically start downloading all files defined in the .dlc to the defined downloadFolder.

          At least in osx, you can only choose the name of the folderwatch folder, but not it's location, which is "~/bin/JDownloader x.y"

Features
---------

* Scraps information from pordede.com based on user input
* Follows links up to the final downloads
* Discards broken links between available ones
* For now decides which link to download based on size (assuming more size == more quality)
* Uploader filter, to take into account only links from selected uploaders (currently only defined for uploaded.to.
  To define other uploaders, the correct string must be looked up in the markup of the page where links are shown.)
* All option to download all episodes of a season

Improvements
------------

* Filter by quality, language, subtitles



            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
