Kate FuzzyOpen plugin
---------------------
This plugin implements a fuzzy-style open dialog. The plugin can be invoked from the **Files > Fuzzy Open** menu action or via the **Meta+T** shortcut (Meta is usually the Windows key).

.. image:: https://lh4.googleusercontent.com/-zfLtqjJH2TI/TyVhx3dnFAI/AAAAAAAAEF0/KslF6PZAAU0/s900/kate-plugin-fuzzyopen.png

How it works
''''''''''''
When you activate the **Fuzzy Open** window, you are presented with a list of documents and the cursor if already focused on a filter bar so that you can type right away.
The list of documents is composed of the current open documents and all the files that are in the same directory (non recursively) of the document which has the focus in Kate.

This list if automatically filtered to exclude all the files that are known not to be text files. The first item in the list is automatically focused so that you can press *Enter* to open it. This focus can be moved using the *up/down* arrow keys.

For the plugin to present this list of documents in the fastest way possible, the document scan is performed only once per directory and on all subsequent usages the list will be read from an in-memory cache. To refresh this cache, a *reload* button is provided right next to the filter bar.

Additionally you can configure **project paths** using the *settings* button. If the currently selected document in kate is in one of the project paths then the plugin will scan this directory recursively.

Also in the setting dialog are the global include/exclude filters. This filters are regular expressions and are applied to the full document path.

Installation
''''''''''''
Copy or link the fuzzyopen directory under *~/.kde4/share/apps/kate/pate/* to install it only for the current user, or do the same in */usr/share/apps/kate/pate/* to do it globally.

Requirements
''''''''''''
This plugin is developed in python and requires the `Pâté plugin system <https://github.com/mtorromeo/pate>`_ for Kate to be installed.
Note that this is a fork of the original project which contains some modifications that are required for the plugin to work.

LICENSE
'''''''
Copyright (c) 2011-2012 Massimiliano Torromeo

Free software released under the terms of the BSD license.

Contacts
''''''''

* Massimiliano Torromeo <massimiliano.torromeo@gmail.com>
