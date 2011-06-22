#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
 this is a "file-blogging" platform copyright adam mathes
 begun 7/26/2010
 bits adapted from endless inkwell unreleased retroblogging platform

 ---
 10/12/2010 picked this up again
 added support for extended attributes from the filesystem (spotlight comments)
 cleaned up templates
 checked into git
'''

import ConfigParser
import sys, os, glob, re, datetime, math, json, Foundation
from Foundation import *
from optparse import OptionParser

deps = ['jinja2', 'markdown2', 'mutagen', 'bleach', 'xattr']
def missing_dependencies():
    missing = False
    for dep in deps:
        try:
            __import__(dep)
        except:
            missing = True
            print 'system is missing the module %s' % (dep)
    return missing


def install_dependencies():
    for dep in deps:
        try:
            __import__(dep)
        except:
            print 'trying to install %s now...' % (dep)
            command = 'sudo easy_install %s' % (dep)
            print(command)
            os.system(command)


class Settings:
    def __init__(self, config_file='settings.cfg', section='eio'):
        self.CONFIG_FILE = os.path.join(os.path.dirname(__file__), config_file)
        self.read_config(section)

    def read_config(self, section='eio'):
        
        self.config = ConfigParser.ConfigParser()
        config = self.config
        config.read(self.CONFIG_FILE)

        self.BASE_DIR = os.path.abspath(os.path.dirname(__file__))

        try:
            self.DESTINATION =  config.get(section, 'destination')
        except:
            self.DESTINATION = ''
        self.URL =  config.get(section, 'url')
        self.INPUT_DIR =  os.path.join(self.BASE_DIR, config.get(section, 'input'))        
        self.OUTPUT_DIR =  os.path.join(self.BASE_DIR, config.get(section, 'output'))
        self.THEME_DIR =  os.path.join(self.BASE_DIR, config.get(section, 'themes'))
        self.LIST_TEMPLATE_DIR = os.path.join(self.THEME_DIR, 'list')

        # set up templates
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader([self.THEME_DIR, self.LIST_TEMPLATE_DIR], encoding='utf-8'))

        self.DEFAULT_TEMPLATE = self.env.get_template('default.tpl')

        try:
            self.TITLE = config.get(section, 'title')
        except:
            self.TITLE = 'endless i/o'

        try:
            self.DESCRIPTION = config.get(section, 'description')
        except:
            self.DESCRIPTION = ''

        
            

class PostRegistry:
    def __init__(self):
        self.post_types = dict()

    def register(self, extensions, post_type):
        for extension in extensions:
            self.post_types[extension] = post_type
post_registry = PostRegistry()

class Post:
    extensions = []
    
    def __init__(self, fp, site):
        self.site = site
        self.rp = os.path.relpath(fp, self.site.settings.INPUT_DIR).decode('utf-8')
        self.filename = os.path.basename(fp).decode('utf-8')
        self.directory = os.path.dirname(self.rp)        
        self.permafile = self.rp + '.html'
        self.filepath = fp
        self.url = ("%s/%s" % ('files', self.rp))
        self.timestamp = os.path.getmtime(self.filepath)
        self.datetime = datetime.datetime.fromtimestamp(self.timestamp)
        self.prettydate = self.datetime.strftime("%B %e, %Y")
        self.prettytime = self.datetime.strftime("%l:%M %p")
        self.template = self.site.settings.DEFAULT_TEMPLATE
        self.type = 'default'
        self.__init_xattr__()

    def __init_xattr__(self):
        self.attribs = xattr.xattr(self.filepath)
        
        self.source_url = self.get_x_attr('com.apple.metadata:kMDItemWhereFroms')
        if self.source_url:
            self.source_url = self.source_url.replace('(', '')
            self.source_url = self.source_url.replace(')', '')
            self.source_url = self.source_url.replace('"', '')
            self.source_url = self.source_url.replace(' ', '')

        self.finder_comment = self.get_x_attr('com.apple.metadata:kMDItemFinderComment')
        if self.finder_comment:
            bl = Bleach()
            self.finder_comment = bl.linkify(self.finder_comment, nofollow=False)

    def get_x_attr(self, name):
        if name in self.attribs:
            plstr = self.attribs.get(name)
            pldata = NSData.dataWithBytes_length_(plstr, len(plstr))
            plist, format, error = NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(pldata, NSPropertyListImmutable, None, None)
            return unicode(plist)
        else:
            return ''

    def render(self):
        posts = []
        posts.append(self)
        return(self.template.render(posts=posts, site=self.site, base=self.site.base_url(self.directory), directory=self.directory))

    def toast(self):
        out = self.render()
        outfile = os.path.join(self.site.settings.OUTPUT_DIR, self.rp + '.html')
        write_file(outfile, out)


class TextPost(Post):
    extensions = ['text']
    def __init__(self, fp, site):
        Post.__init__(self, fp, site)
        self.type = 'text'
        f = open(self.filepath)
        self.text = f.read()
        f.close()
post_registry.register(TextPost.extensions, TextPost)


class MarkdownPost(TextPost):
    extensions = ['md', 'txt']
    
    def __init__(self, fp, site):
        TextPost.__init__(self, fp, site)
        self.type = 'text'

        # TODO: this ASCII encoding hack is *not* OK, man! NOT OK
        self.markdown_text = markdown2.markdown(self.text).encode('ascii', 'ignore')
        bl = Bleach()
        self.markdown_text = bl.linkify(self.markdown_text, nofollow=False)
post_registry.register(MarkdownPost.extensions, MarkdownPost)


class ImagePost(Post):
    extensions = ['png', 'jpg', 'gif', 'jpeg', 'bmp', 'tiff']
    sizes = [100, 500, 800]
    
    def __init__(self, fp, site):
        Post.__init__(self, fp, site)
        self.type = 'image'
        self.resize()
        self.small = "%s/%s/%s" % ('img', '100', self.rp)
        self.medium = "%s/%s/%s" % ('img', '500', self.rp)
        self.large = "%s/%s/%s" % ('img', '800', self.rp)
    
    def resize(self):
        for size in self.sizes:
            outfile = os.path.join(self.site.settings.OUTPUT_DIR, 'img', str(size), self.rp)
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            infile = os.path.join(self.site.settings.INPUT_DIR, self.rp)

            if(os.path.isfile(outfile)):
                pass
            else:
                try:
                    if size == 100:
                        cmd =  "sips --resampleHeight %d '%s' --out '%s'" % (size, infile, outfile)
                    else:
                        cmd = "sips --resampleWidth %d '%s' --out '%s'" % (size, infile, outfile)
                    os.system(cmd)

                except:
                    print 'uhoh, could not sips resize!'
post_registry.register(ImagePost.extensions, ImagePost)


class WeblocPost(TextPost):
    extensions = ['webloc']

    def __init__(self, fp, site):
        TextPost.__init__(self, fp, site)
        self.type = 'webloc'
        # uh... this is not an ideal way to parse resource forks but i was too lazy to do this properly
        # it almost certainly will not work in some cases. Oops!
        try:
            self.target_url = re.search("(?P<url>https?://[^\s]+)", self.text).group("url").encode('ascii', 'ignore')
        except:
            self.target_url = ''
post_registry.register(WeblocPost.extensions, WeblocPost)


class AudioPost(Post):
    extensions = ['mp3']

    # TODO - flash player instead of relying on HTML5 audio
    def __init__(self, fp, site):
        Post.__init__(self, fp, site)
        self.type = 'audio'

        a = EasyID3(os.path.join(self.site.settings.INPUT_DIR, self.rp))
        try:
            self.audio_title = a["title"][0]
        except:
            self.audio_title = ''
        try:
            self.audio_artist = a["artist"][0]
        except:
            self.audio_artist = ''
        try:
            self.audio_album = a["album"][0]
        except:
            self.audio_album = ''            
post_registry.register(AudioPost.extensions, AudioPost)


class VideoPost(Post):
    extensions = ['mp4', 'mpeg']
    
    def __init__(self, fp, site):
        Post.__init__(self, fp, site)
        self.type = 'video'

post_registry.register(VideoPost.extensions, VideoPost)


class Archive:
    """

    Archive is a reperesentation of a list of posts The simplest
    archive outputs a single file based on a single template with
    access to the Site object

    """
    def __init__(self, template=None, output_filename=None, site=None):
        self.site = site
        self.template = self.site.settings.env.get_template(template)
        self.output_filename = output_filename

    def render(self, directory=''):
        return(self.template.render(site=self.site, posts=self.site.posts_in_directory(directory), directory=directory,
                                    base=self.site.base_url(directory)))
    
    def toast(self, directory=''):
        outfile = os.path.join(self.site.settings.OUTPUT_DIR, directory, self.output_filename)
        output = self.render(directory)
        write_file(outfile, output)


class PageArchive(Archive):
    """

    PageArchive is a reperesentation of a list of documents in bunches of
    n, or pages. Basically, the arcchive is like the front page of a
    blog that just keeps going on and on. Page 1 is the most recent N
    entries, page 2 is older, etc.

    """

    def render(self, posts, page, last_page, directory=''):
        if directory in self.site.overrides:
            try:
                theme = self.site.overrides[directory].get('overrides', 'theme')
                template = self.site.settings.env.get_template(theme)
            except:
                template = self.template
        else:
            template = self.template

        return(template.render(site=self.site, posts=posts, page=page, last_page=last_page,
                                    directory=directory, base=self.site.base_url(directory)))

    def toast(self, directory=''):
        # TODO: allow this page size to be overriden
        per_page = 15
        if directory in self.site.overrides:
            try:
                per_page = int(self.site.overrides[directory].get('overrides', 'per_page'))
            except:
                pass
            
        filtered_posts = self.site.posts_in_directory(directory)
        last_page =  int(math.floor(len(filtered_posts)/per_page) + 1)

        for i in range(1, last_page+1):
            outfile = os.path.join(self.site.settings.OUTPUT_DIR, directory, '%d.html' % i)
            page = i
            posts = filtered_posts[(i-1)*per_page:i*per_page]            
            output = self.render(posts, page, last_page, directory)
            write_file(outfile, output)            
            if i == 1:
                outfile = os.path.join(self.site.settings.OUTPUT_DIR, directory, 'index.html')
                write_file(outfile, output)            


class Site:
    BLACKLIST_FILES = ['settings.cfg', 'Interim Note-Changes', '.DS_Store', 'Notes & Settings']


    def __init__(self, site_name='eio'):
        self.settings = Settings(section=site_name)
        self.url = self.settings.URL
        base = os.path.abspath(os.path.dirname(__file__))

        if not os.path.exists(self.settings.INPUT_DIR):
            os.makedirs(self.settings.INPUT_DIR)

        if not os.path.exists(self.settings.OUTPUT_DIR):
            os.makedirs(self.settings.OUTPUT_DIR)

        static = os.path.join(base, 'static')
        if not os.path.exists(os.path.join(self.settings.OUTPUT_DIR, 'static')):
            os.symlink(static, os.path.join(self.settings.OUTPUT_DIR, 'static'))

        if not os.path.exists(os.path.join(self.settings.OUTPUT_DIR, 'files')):
            os.symlink(self.settings.INPUT_DIR, os.path.join(self.settings.OUTPUT_DIR, 'files'))

        self.directories = []
        self.posts = []
        self.overrides = dict()


    def read_files(self, base_dir):
        files = os.listdir(base_dir)
        for f in files:
            fp = os.path.join(base_dir, f)
            rp = os.path.relpath(fp, self.settings.INPUT_DIR)
            if os.path.isdir(fp):                
                self.directories.append(rp)
                self.read_files(fp)
            else:
                self.add_file(fp)

        self.posts.sort(key=lambda post: os.path.getmtime(post.filepath))
        self.posts.reverse()


    def add_file(self, fp):
        if os.path.basename(fp) in self.BLACKLIST_FILES:
            return
        
        extension = os.path.splitext(fp)[1]
        extension = extension.lower()
        extension = extension.replace('.', '')
        if extension in post_registry.post_types:
            p = post_registry.post_types[extension](fp=fp, site=self)
        else:
            p = Post(fp=fp, site=self)
        self.posts.append(p)


    def posts_in_directory(self, directory=None, recursive=False):
        # if directory == None or directory == '':
        #     return self.posts
        # else:
        filtered_posts = []
        for post in self.posts:
            if recursive and post.directory.startswith(directory):
                filtered_posts.append(post)
                
            if not recursive and post.directory == directory:
                filtered_posts.append(post)
                    
        return filtered_posts


    def read_overrides(self):
        for directory in self.directories:
            override = os.path.join(self.settings.INPUT_DIR, directory, 'settings.cfg')
            if os.path.exists(override):
                config = ConfigParser.ConfigParser()
                config.read(override)
                self.overrides[directory] = config


    def generate(self):
        self.read_files(self.settings.INPUT_DIR)
        self.read_overrides()
        self.read_archives()
        self.generate_posts()
        self.generate_archives()


    def generate_posts(self):
        for p in self.posts:
            p.toast()


    def generate_archives(self):
        for a in self.archives:
            a.toast()
        for directory in self.directories:
            for a in self.archives:
                a.toast(directory)


    def read_archives(self):
        self.archives = []
        list_archive_templates = os.listdir(self.settings.LIST_TEMPLATE_DIR)
        for list_archive_template in list_archive_templates:
            output_filename = re.sub('.tpl', '', list_archive_template)
            template = os.path.join(self.settings.LIST_TEMPLATE_DIR, list_archive_template)
            archive = Archive(output_filename=output_filename, template=list_archive_template, site=self)
            self.archives.append(archive)
        pageArchive = PageArchive(output_filename='x.html', template=self.settings.DEFAULT_TEMPLATE, site=self)
        self.archives.append(pageArchive)


    def base_url(self, directory):
        if directory == '':
            return '.'        
        depth = len(directory.split('/'))
        base = '../' * (depth)
        return base


    def sync(self):
        source = self.settings.OUTPUT_DIR
        destination = self.settings.DESTINATION
        if destination:
            rsync_command = 'rsync -auz -L %s/ %s' % (source, destination)
            print 'executing %s' % rsync_command
            os.system(rsync_command)


def write_file(outfile, output):
    try:
        outdir = os.path.dirname(outfile)
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        f = open(outfile, 'w')
        f.write(output.encode('utf-8', 'ignore'))
        f.close()
    except IOError:
        print 'NO!!! could not write to %s' % outfile

       
def generate():
    site_names = get_site_names()
    for site_name in site_names:
        print 'generating %s' % site_name
        global s
        s = Site(site_name)
        s.generate()


def sync():
    site_names = get_site_names()
    for site_name in site_names:
        print 'generating %s' % site_name
        global s
        s = Site(site_name)
        s.sync()


def auto_launch():
    wd = os.path.abspath(__file__)
    watch_paths = ''
    site_names = get_site_names()
    for site_name in site_names:
        s = Site(site_name)
        files_directory = s.settings.INPUT_DIR
        watch_paths += '<string>%s</string>\n' % files_directory

    plist = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<dict>
        <key>Label</key>
        <string>org.trenchant.eio</string>
        <key>LowPriorityIO</key>
        <true/>
        <key>Program</key>
        <string>%s</string>
        <key>ProgramArguments</key>
        <array>
                <string>eio.py</string>
        </array>
        <key>WatchPaths</key>
        <array>
        %s
        </array>
</dict>
</plist>
''' % (wd, watch_paths)
    outfile = os.path.join(os.path.expanduser('~'), 'Library', 'LaunchAgents', 'org.trenchant.eio')
    write_file(outfile, plist)
    os.system('launchctl load -F %s ' % (outfile))


def stop_auto_launch():
    outfile = os.path.join(os.path.expanduser('~'), 'Library', 'LaunchAgents', 'org.trenchant.eio')
    os.system('launchctl unload %s ' % (outfile))


def get_site_names():
    config_file = os.path.join(os.path.dirname(__file__), 'settings.cfg')
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    site_names = []
    for site_name in config.sections():
        if site_name != 'templates':
            site_names.append(site_name)
    return site_names
    

def main():

    usage ='eio.py [start|stop|generate|sync|bootstrap]'
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()

    try:
        command = args[0]
    except:
        print usage
        command = 'both'
      
        
    if command == 'start':
        print 'starting...'
        auto_launch()        
    elif command == 'stop':
        print 'stopping autolaunch'
        stop_auto_launch()        
    elif command == 'generate':
        print 'generating site...'
        generate()
    elif command == 'sync':
        print 'syncing up...'
        sync()
    elif command == 'bootstrap':
        install_dependencies()
    else:
        print 'generating site...'
        generate()
        print 'syncing up...'
        sync()
        

if __name__ == "__main__":
    if missing_dependencies():
        confirmation = raw_input( 'you are missing required modules. try to install them now? [y/n]')
        if(confirmation == 'y'):
            install_dependencies()       
    else:
        import jinja2
        import markdown2    
        from bleach import Bleach
        from mutagen.easyid3 import EasyID3
        import xattr
        main()
