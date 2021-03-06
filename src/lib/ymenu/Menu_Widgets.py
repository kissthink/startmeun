#!/usr/bin/env python
# -*- coding:utf-8 -*-

import gtk
import cairo
import gobject
import pango
import os
import commands
import Globals
import IconFactory
import time
import gconf
from Popup_Menu import add_menuitem, add_image_menuitem
import gc
import gio
from urllib import unquote, url2pathname
import xdg.DesktopEntry
import xdg.Menu
from execute import *
from user import home
import re
from time import sleep
import threading


try:
    has_gst = False
    #import gst
except:
    has_gst = False

try:
    INSTALL_PREFIX = open("/etc/ymenu/prefix").read()[:-1]
except:
    INSTALL_PREFIX = '/usr'

import gettext

gettext.textdomain('ymenu')
gettext.install('ymenu', INSTALL_PREFIX + '/share/locale')
gettext.bindtextdomain('ymenu', INSTALL_PREFIX + '/share/locale')

def _(s):
    return gettext.gettext(s)

class MenuButton:
    def __init__(self, i, base):
        # base > EventBox > Fixed > All the rest
        self.i = i
        self.backimagearea = None
        self.Button = gtk.EventBox()
        self.Frame = gtk.Fixed()
        if not self.Button.is_composited(): 
            self.supports_alpha = False
        else:
            self.supports_alpha = True
        self.Button.connect("composited-changed", self.composite_changed) 
        self.Frame.connect("expose_event", self.expose)
        self.Button.add(self.Frame)

        if Globals.MenuButtonIcon[i]:
            self.Icon = gtk.Image()
            self.SetIcon(Globals.ImageDirectory + Globals.MenuButtonIcon[i])
		
        self.Image = gtk.Image()

        self.Setimage(Globals.ImageDirectory + Globals.MenuButtonImage[i])
        self.w = Globals.MenuButtonW[i]
        self.h = Globals.MenuButtonH[i]

        # Set the background which is always present
        self.BackgroundImage = gtk.Image()
        if Globals.MenuButtonImageBack[i] != '':
            tmppic = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.MenuButtonImageBack[i] )
            tmppic = tmppic.scale_simple(self.w, self.h, gtk.gdk.INTERP_BILINEAR)
            self.BackgroundImage.set_from_pixbuf (tmppic)
            del tmppic
        else:
            self.BackgroundImage.set_from_pixbuf(None)

        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.SetBackground()

        self.Frame.put(self.BackgroundImage, 0, 0)
        self.Frame.put(self.Image, 0, 0)
        
        self.Label = gtk.Label()
        self.txt = Globals.MenuButtonMarkup[i]
        try:
            self.txt = self.txt.replace(Globals.MenuButtonNames[i], _(Globals.MenuButtonNames[i]))
            self.txt = self.txt.replace('<span','<span size=\"' + Globals.MFontSize + '\"') # 增加字号 
        except:pass
        self.Label.set_markup(self.txt)

        self.Frame.put(self.Label, Globals.MenuButtonNameOffsetX[i], Globals.MenuButtonNameOffsetY[i])
        if self.Label.get_text() == '' or Globals.Settings['Show_Tips']:
            self.Frame.set_tooltip_text(_(Globals.MenuButtonNames[i]))
        base.put(self.Button, Globals.MenuButtonX[i], Globals.MenuButtonY[i])
        #gc.collect()

    def composite_changed(self, widget):
		
        if not self.Button.is_composited():	 
            self.supports_alpha = False
        else:
            self.supports_alpha = True

    def expose (self, widget, event):
        self.ctx = widget.window.cairo_create()
        # set a clip region for the expose event
        color = []
        color = Globals.color_translate(Globals.App_bgcolor)
        if self.supports_alpha == False:
            self.ctx.set_source_rgb(color[0], color[1], color[2])
        else:
            self.ctx.set_source_rgba(color[0], color[1], color[2], 1)
        self.ctx.set_operator (cairo.OPERATOR_SOURCE)
        self.ctx.paint()
        del color
        #cairo_drawing.draw_pixbuf(self.ctx, self.backimagearea)
	  
    def SetIcon(self, filename):
        # If the menu has an icon on top, then add that
        try:
            if Globals.MenuButtonIconSize[self.i] != 0 and os.path.isfile(filename):
                self.ww = Globals.MenuButtonIconSize[self.i]
                self.hh = self.ww
                self.Pic = gtk.gdk.pixbuf_new_from_file(filename)
                self.Pic = self.Pic.scal_simple(self.ww, self.hh, gtk.gdk.INTERP_BILINEAR)
            else:
                self.ww = self.hh =Globals.MenuButtonIconSize[self.i] #24
			
            if Globals.MenuButtonIcon[self.i]:
                self.ico = IconFactory.GetSystemIcon(Globals.MenuButtonIcon[self.i])
                if not self.ico:
                    self.ico = filename
                self.Pic = gtk.gdk.pixbuf_new_from_file_at_size(self.ico, self.ww, self.hh)
            self.Icon.set_from_pixbuf(self.Pic)
        except:print 'error on button seticon'  + filename
				
    def Setimage(self, imagefile):
        # The image is background when it's not displaying the overlay
        self.pic = gtk.gdk.pixbuf_new_from_file(imagefile).scale_simple(Globals.MenuButtonW[self.i], Globals.MenuButtonH[self.i], gtk.gdk.INTERP_NEAREST)
        #self.pic = gtk.gdk.pixbuf_new_from_file(imagefile)
        self.Image.set_from_pixbuf(self.pic)

    def SetBackground(self):
        self.Image.set_from_pixbuf(None)


class MenuImage:
    def __init__(self, i, base, backimage):
        self.backimagearea = None
        self.Frame = gtk.Fixed()
        if not self.Frame.is_composited():
	 
            self.supports_alpha = False
        else:
            self.supports_alpha = True
        self.Frame.connect("composited-changed", self.composite_changed)
        self.Image = gtk.Image()
        self.Pic = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.MenuImage[i])
        self.w = self.Pic.get_width()
        self.h = self.Pic.get_height()
		
        ico = IconFactory.GetSystemIcon(Globals.MenuImage[i])
        if not ico:
            ico = Globals.ImageDirectory + Globals.MenuImage[i]
        self.Pic = gtk.gdk.pixbuf_new_from_file_at_size(ico, self.w, self.h)

        if self.backimagearea is None:
            if Globals.flip == False:
                self.backimagearea = backimage.subpixbuf(Globals.MenuImageX[i], Globals.MenuHeight - Globals.MenuImageY[i] - self.h, self.w, self.h)
                self.backimagearea = self.backimagearea.flip(Globals.flip)
            else:
                self.backimagearea = backimage.subpixbuf(Globals.MenuImageX[i], Globals.MenuImageY[i], self.w, self.h)
        self.Pic.composite(self.backimagearea, 0, 0, self.w, self.h, 0, 0, 1, 1, gtk.gdk.INTERP_BILINEAR, 255)
        # Set the background which is always present
        self.Image.set_from_pixbuf(self.backimagearea)
        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)
        base.put(self.Frame, Globals.MenuImageX[i], Globals.MenuImageY[i])
        #gc.collect()

    def composite_changed(self, widget):
		
        if not self.Frame.is_composited():
	 
            self.supports_alpha = False
        else:
            self.supports_alpha = True


    def expose (self, widget, event):
		
        self.ctx = widget.window.cairo_create()
        # set a clip region for the expose event
        if self.supports_alpha == False:
            self.ctx.set_source_rgb(1, 1, 1)
        else:
            self.ctx.set_source_rgba(1, 1, 1, 0)
        self.ctx.set_operator (cairo.OPERATOR_SOURCE)
        self.ctx.paint()

class GtkSearchBar(gtk.EventBox, gobject.GObject):
    __gsignals__ = {
        'right-clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'searchbar-search': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }
        
    def __init__(self, BackImageFile, W, H, win):
        gtk.EventBox.__init__(self)
        gobject.GObject.__init__(self)

        self.key_state = 0 # 0-初始状态， 1 - 中键曾按下， 2 - 右键曾按下
        self.Frame = gtk.Fixed()
        self.set_visible_window(0)
        self.add(self.Frame)

        self.win = win
        self.entry = gtk.Entry()
        self.entry.set_text(_(u"Search"))
        self.entry.set_inner_border(None)
        self.back = gtk.Image()
        self.entry.set_size_request(W, H)
        self.search_pic = gtk.Image()

        self.search_button = gtk.EventBox()
        self.search_button.set_size_request(22, 22)
        self.search_button.connect("button-release-event", self.searchbar_search_signal)
        self.search_button.set_visible_window(False)
        sel = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.SearchPic).scale_simple(Globals.SearchPicW, Globals.SearchPicH, gtk.gdk.INTERP_BILINEAR)
        self.search_pic.set_from_pixbuf(sel)
        self.search_button.add(self.search_pic)
        del sel

        sel = gtk.gdk.pixbuf_new_from_file(BackImageFile).scale_simple(Globals.SearchBgSize[0], Globals.SearchBgSize[1], gtk.gdk.INTERP_BILINEAR )
        self.back.set_from_pixbuf(sel)
        del sel

        color = []
        color = Globals.color_translate(Globals.App_bgcolor)
        self.entry.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(color[0], color[1], color[2]))
        del color

        self.entry.set_has_frame(False)
        self.entry.set_max_length(20)

        self.entry.connect("button-press-event", self.enter)
        self.entry.connect("focus-in-event", self.enter)
        self.entry.connect("leave-notify-event", self.leave)
        self.entry.connect("focus-out-event", self.leave)

        self.entry.modify_text(gtk.STATE_NORMAL, Globals.NegativeThemeColorCode)
        if Globals.MFontSize == 'small': # or large to change the font size
            pfd = pango.FontDescription("8")
            self.entry.modify_font(pfd)

        self.Frame.put(self.back, 0, 0)
        self.Frame.put(self.entry, int(6 * Globals.width_ratio), int( 6 * Globals.height_ratio))
        self.Frame.put(self.search_button, Globals.SearchPicX, Globals.SearchPicY)

    def enter(self, widget, event):
        self.entry.set_text(u"")
        if event.type == gtk.gdk.BUTTON_PRESS and (event.button == 2 or event.button == 3):
            self.key_state = event.button - 1
            if event.button == 2: # right button
                self.emit('right-clicked')

    def leave(self, widget, event):
        if widget.get_text() == '' and not self.key_state:
            self.win.set_focus(None)
            self.entry.set_text(_(u"Search"))

    def searchbar_search_signal(self, widget, event):
        self.emit('searchbar-search')

class IconManager(gobject.GObject):

    __gsignals__ = {
        "changed": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.icons = {}
        self.count = 0
	self.lock = threading.Lock()

        # Some apps don't put a default icon in the default theme folder, so we will search all themes
        def createTheme(d):
            theme = gtk.IconTheme()
            theme.set_custom_theme(d)
            return theme

        # This takes to much time and there are only a very few applications that use icons from different themes
        #self.themes = map(  createTheme, [ d for d in os.listdir( "/usr/share/icons" ) if os.path.isdir( os.path.join( "/usr/share/icons", d ) ) ] )

        defaultTheme = gtk.icon_theme_get_default()
        defaultKdeTheme = createTheme("kde.default")

        # Themes with the same content as the default them aren't needed
        #self.themes = [ theme for theme in self.themes if  theme.list_icons() != defaultTheme.list_icons() ]

        self.themes = [defaultTheme, defaultKdeTheme]

        self.cache = {} # {iconName: {fileName: <filename>, Size: <size>, Pixbuf: <icon>}, ...}

        # Listen for changes in the themes
        for theme in self.themes:
            theme.connect("changed", self.themeChanged)
	
    def getIcon(self, iconName, iconSize, iconThemeChanged = False):
        if not iconName or iconSize <= 0:
            return None
        try:
            #[ iconWidth, iconHeight ] = self.getIconSize( iconSize )
	    
	    if not iconThemeChanged \
		    and iconName in self.cache \
		    and iconSize == self.cache[iconName]["Size"]:
		if self.cache[iconName]["Pixbuf"]: 
		    return self.cache[iconName]["Pixbuf"]
		iconFileName = self.cache[iconName]["fileName"]
            elif os.path.isabs(iconName):
                iconFileName = iconName
            else:
                if iconName[-4:] in [".png", ".xpm", ".svg", ".gif"]:
                    realIconName = iconName[:-4]
                else:
                    realIconName = iconName
                tmp = None
                for theme in self.themes:
                    if theme.has_icon(realIconName):
                        tmp = theme.lookup_icon(realIconName, iconSize, 0)
                        if tmp:
                            break

                if tmp:
                    iconFileName = tmp.get_filename()
                else:
                    iconFileName = ""


	    if iconThemeChanged \
		    and iconName in self.cache \
		    and iconFileName == self.cache[iconName]["fileName"] \
		    and iconSize == self.cache[iconName]["Size"] \
		    and self.cache[iconName]["Pixbuf"]: # 主要是判断文件路径是否改变
		return self.cache[iconName]["Pixbuf"] 

            if iconFileName and os.path.exists(iconFileName):
                icon = gtk.gdk.pixbuf_new_from_file(iconFileName).scale_simple(iconSize, iconSize, gtk.gdk.INTERP_BILINEAR)
            else:
                icon = None

	    self.lock.acquire() # threading.Lock()
            self.cache[iconName] = {"fileName": iconFileName, "Size": iconSize, "Pixbuf": icon}
	    self.lock.release()

            return icon
        except Exception, e:
            print "Exception " + e.__class__.__name__ + ": " + e.message
            return None

    def themeChanged(self, theme):
	#del self.cache
	#self.cache = {}
        self.emit("changed")

gobject.type_register(IconManager)

class CategoryTab(gtk.EventBox):
    #CategoryTab(i,addedCategories[i]["icon"],Globals.PG_iconsize,addedCategories[i]["name"],addedCategories[i]["tooltip"])
    def __init__(self, name):
        gtk.EventBox.__init__(self)
        
        self.Name = name
        self.connections = []
        self.Frame = gtk.Fixed()
        self.set_visible_window(0)
        self.add(self.Frame)
        
        #Tab背景
        self.Image = gtk.Image()
        #sel = gtk.gdk.pixbuf_get_file_info(Globals.ImageDirectory + Globals.TabBackImage)
	self.w = Globals.tab_back_size[0] #sel[1]
	self.h = Globals.tab_back_size[1] #sel[2]
	#sel = None'''
        self.Image.set_from_pixbuf(None)
        self.Image.set_size_request(self.w, self.h )
        self.Frame.set_size_request(self.w, self.h )
        self.Frame.put(self.Image, 0, 0)
        
        #Tab上的文字
        self.Label = gtk.Label()
        self.txt = "<span size=\"%s\" foreground=\"%s\">%s</span>" % ( Globals.MFontSize, Globals.PG_fgcolor, name.replace("&","") )
        self.Label.set_alignment(0, 0)
        self.Label.set_markup(self.txt)
	self.Frame.put(self.Label, Globals.TabBackNameX, Globals.TabBackNameY)
        
        self.connectSelf("destroy", self.onDestroy)
      
    def connectSelf(self, event, callback):
        self.connections.append(self.connect(event, callback))    
        
    def onDestroy(self, widget):
        #self.buttonImage.clear()
        #iconManager.disconnect(self.themeChangedHandlerId)
        for connection in self.connections:
            self.disconnect(connection)
        del self.connections                
            
    def setSelectedTab(self, tab):
	if tab == False:
            self.Image.set_from_pixbuf(None)
        else:
            self.pic = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.TabBackImage)
            self.pic = self.pic.scale_simple(Globals.tab_back_size[0], Globals.tab_back_size[1], gtk.gdk.INTERP_BILINEAR)
            self.Image.set_from_pixbuf(self.pic)
	    del self.pic
            
#AppButton.__init__( self, self.appIconName, iconSize )
class AppButton(gtk.EventBox):
    
    def __init__(self, iconName, iconSize):
        gtk.EventBox.__init__(self)
       
        self.connections = []
        self.Frame = gtk.Fixed()
        self.set_visible_window(0)
        self.add(self.Frame)
        
        #Button背景
        self.Image = gtk.Image()
        #sel = gtk.gdk.pixbuf_get_file_info(Globals.ImageDirectory + Globals.ButtonBackImage)
	self.w = Globals.button_back_size[0] #sel[1]
	self.h = Globals.button_back_size[1]#sel[2]
        self.Image.set_from_pixbuf(None)
        self.set_size_request(self.w, self.h)
        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)
        
        #Button上的图标
        self.iconName = iconName
        self.iconSize = iconSize
        icon = self.getIcon(self.iconSize)
        self.buttonImage = gtk.Image()
        if icon:
            self.buttonImage.set_from_pixbuf(icon)
            del icon
        else:
            self.buttonImage.set_size_request(self.iconSize, self.iconSize)
        self.Frame.put(self.buttonImage, Globals.ButtonBackIconX, Globals.ButtonBackIconY)
            
        self.connectSelf("destroy", self.onDestroy)
        self.themeChangedHandlerId = iconManager.connect("changed", self.themeChanged)
    
    def connectSelf(self, event, callback):
        self.connections.append(self.connect(event, callback))
    
    def setSelectedTab(self, flag):
        if flag == True:
            self.pic = gtk.gdk.pixbuf_new_from_file_at_size(Globals.ImageDirectory + Globals.ButtonBackImage, Globals.button_back_size[0], Globals.button_back_size[1])
            self.Image.set_from_pixbuf(self.pic)  
	    del self.pic
        else:
            self.Image.set_from_pixbuf(None)
        
    def getIcon (self, iconSize, iconThemeChanged = False):
        #if not self.iconName:
        #    return None

        icon = iconManager.getIcon(self.iconName, iconSize, iconThemeChanged)
        if not icon:
            icon = iconManager.getIcon("application-default-icon", iconSize, iconThemeChanged)
       
        return icon
    
    def setIcon (self, iconName):
        self.iconName = iconName
        self.iconChanged()

    # IconTheme changed, setup new button icons
    def themeChanged(self, theme):
        self.iconChanged(True)

    def iconChanged(self, iconThemeChanged = False):
        icon = self.getIcon(self.iconSize, iconThemeChanged)
        self.buttonImage.clear()
        if icon:
            self.buttonImage.set_from_pixbuf(icon)
            self.buttonImage.set_size_request(-1, -1)
            del icon
        else:
            #[iW, iH ] = iconManager.getIconSize( self.iconSize )
            self.buttonImage.set_size_request(self.iconSize, self.iconSize)

    def setIconSize(self, size):
        self.iconSize = size
        icon = self.getIcon(self.iconSize)
        self.buttonImage.clear()
        if icon:
            self.buttonImage.set_from_pixbuf(icon)
            self.buttonImage.set_size_request(-1, -1)
            del icon
        elif self.iconSize:
            #[ iW, iH ] = iconManager.getIconSize( self.iconSize )
            self.buttonImage.set_size_request(self.iconSize, self.iconSize)
            
    def addLabel(self, text, styles=None):
        self.Label = gtk.Label()
        if "<b>" in text:
            text = "<span size=\"%s\" foreground=\"#FFFF00\">%s</span>" % ( Globals.MFontSize, text )
            text = "<b>%s</b>" % text
        else:
            text = "<span size=\"%s\" foreground=\"%s\">%s</span>" % ( Globals.MFontSize, Globals.App_fgcolor, text )
            
        self.Label.set_markup(text)
        self.Label.set_alignment(0.0, 0.0)
        self.Label.set_width_chars(21)
        self.Label.set_ellipsize(pango.ELLIPSIZE_END)
        self.Label.show()
        self.Frame.put(self.Label, Globals.ButtonBackNameX, Globals.ButtonBackNameY)

    def onDestroy(self, widget):
        self.buttonImage.clear()
        iconManager.disconnect(self.themeChangedHandlerId)
        for connection in self.connections:
            self.disconnect(connection)
        del self.connections


# Search Button
class SearchLauncher(AppButton):
    def __init__(self, iconName, container, text = None):
         #self.app_bt = AppButton(iconName, iconSize)
         AppButton.__init__(self, iconName, Globals.PG_iconsize)
         self.addLabel(text + '<span color="green">' + '<b> ' + Globals.searchitem + '</b>' + '</span>')
         self.connect("enter_notify_event", self.mouse_glide, True)
         self.connect("leave_notify_event", self.mouse_glide)
         container.pack_start(self, False)
         self.show_all()

    def mouse_glide(self, widget, event, Flag = False):
        self.setSelectedTab(Flag)

    def filterText(self, text):# 并没有过滤，利用其更改标签

        labeltext = self.Label.get_text()
        labeltext = labeltext.replace(_("Search Google"), '')
        labeltext = labeltext.replace(_("Search Wikipedia"), '')
        labeltext = labeltext.replace(_("Search 116"), '')
        labeltext = labeltext.replace(_("Search Baidu"), '')
        
        tmpstr = self.Label.get_label()
        tmpstr = tmpstr.replace(labeltext, ' ' + text)
        self.Label.set_markup(tmpstr)
        tmpstr = None
        labeltext = None

        return False

    def filterCategory(self, category):
        #self.destroy()
        pass

#ApplicationLauncher.__init__( self, desktopFile, iconSize )
class ApplicationLauncher(AppButton):

    def __init__(self, desktopFile, iconSize):
        
        if isinstance(desktopFile, xdg.Menu.MenuEntry):
            desktopItem = desktopFile.DesktopEntry
            desktopFile = desktopItem.filename
            self.appDirs = desktop.desktopFile.AppDirs
            
        elif isinstance(desktopFile, xdg.Menu.DesktopEntry):
            desktopItem = desktopFile
            desktopFile = desktopItem.filename
            self.appDirs = [os.path.dirname(desktopItem.filename)]
            
        else:
            desktopItem = xdg.DesktopEntry.DesktopEntry(desktopFile)
            self.appDirs = [os.path.dirname(desktopFile)]

        self.desktopFile = desktopFile
        self.loadDesktopEntry(desktopItem)

        self.drag = True

        AppButton.__init__(self, self.appIconName, iconSize)
        self.setupLabels()
        
        self.connectSelf("drag_data_get", self.dragDataGet)
        self.drag_source_set(gtk.gdk.BUTTON1_MASK, [("text/plain", 0, 100), ("text/uri-list", 0, 101)], gtk.gdk.ACTION_COPY)
        self.connectSelf("drag_begin", self.dragBegin)

    def loadDesktopEntry(self, desktopItem):
        try:
            self.appName = desktopItem.getName()
            self.appGenericName = desktopItem.getGenericName()
            self.appComment = desktopItem.getComment()
            self.appExec = desktopItem.getExec()
            self.appIconName = desktopItem.getIcon()
            self.appCategories = desktopItem.getCategories()
            self.appGnomeDocPath = desktopItem.get("X-GNOME-DocPath") or ""
            self.useTerminal = desktopItem.getTerminal()

            if not self.appGnomeDocPath:
                self.appKdeDocPath      = desktopItem.getDocPath() or ""

            self.appName            = self.appName.strip()
            self.appGenericName     = self.appGenericName.strip()
            self.appComment         = self.appComment.strip()

        except Exception, e:
            #print e
            self.appName            = ""
            self.appGenericName     = ""
            self.appComment         = ""
            self.appExec            = ""
            self.appIconName        = ""
            self.appCategories      = ""
            self.appDocPath         = ""

    def setupLabels(self):
        self.addLabel(self.appName)

    def filterText(self, text):
        keywords = text.lower().split()
        appName = self.appName.lower()
        appGenericName = self.appGenericName.lower()
        appComment = self.appComment.lower()
        appExec = self.appExec.lower()

        for keyword in keywords:
            keyw = keyword
            if keyw != "" and appName.find(keyw) == -1 and appGenericName.find(keyw) == -1 and appComment.find(keyw) == -1 and appExec.find(keyw) == -1:
                self.hide()
                return False

        self.show()
        return True
        
    def getTooltip(self, highlight=None):
               
        tooltip = self.appName
        if self.appComment != "" and self.appComment != self.appName:
            tooltip = self.appComment

        return tooltip

    def dragBegin(self, widget, drag_context):
        self.drag = False
        icon = self.getIcon(self.iconSize)
        if icon:
            self.drag_source_set_icon_pixbuf(icon)
            del icon

    def dragDataGet(self, widget, context, selection, targetType, eventTime):
        if targetType == 100: # text/plain
            selection.set_text("'" + self.desktopFile + "'", -1)
        elif targetType == 101: # text/uri-list
            if self.desktopFile[0:7] == "file://":
                selection.set_uris([self.desktopFile])
            else:
                selection.set_uris(["file://" + self.desktopFile])
                
    def execute(self):
        if self.appExec:
            if self.useTerminal:
                cmd = "x-terminal-emulator -e \"" + self.appExec + "\""
                Execute(self, cmd)
            else:
                Execute(self, self.appExec)

    # IconTheme changed, setup new icons for button and drag 'n drop
    def iconChanged(self, iconThemeChanged = False):
        AppButton.iconChanged(self, iconThemeChanged)

        icon = self.getIcon(Globals.PG_iconsize, iconThemeChanged)
        if icon:
            self.drag_source_set_icon_pixbuf(icon)
            del icon

    def onDestroy(self, widget):
        AppButton.onDestroy(self, widget)

class MenuApplicationLauncher(ApplicationLauncher):

    def __init__(self, desktopFile, iconSize, category, showComment, highlight=False):
        
        self.showComment = showComment
        self.appCategory = category
        self.highlight = highlight
        
        ApplicationLauncher.__init__(self, desktopFile, iconSize)

    def filterCategory(self, category):
        if self.appCategory == category or category == "":
            self.show()
        else:
            self.hide()

    def setupLabels(self):        
        appName = self.appName
        appComment = self.appComment
        if self.highlight: 
            try:
                appName = "<b>%s</b>" % (appName)
                appComment = "<b>%s</b>" % (appComment)
                print appComment
            except Exception, detail:
                print detail
                pass
        self.addLabel(appName)
        
    def execute(self, * args):
        if self.highlight == True:
            self.highlight = False
            self.Label.destroy()
            self.setupLabels()
        return super(MenuApplicationLauncher, self).execute(*args)

class FavApplicationLauncher(ApplicationLauncher):

    def __init__(self, desktopFile, iconSize):
        self.category = _("Favorites")
        self.Name = desktopFile
        ApplicationLauncher.__init__(self, desktopFile, iconSize)

    def setupLabels(self):    
        self.addLabel(self.appName)
        
    def filterCategory(self, category):
        if category == self.category:
            self.show()
        else:
            self.hide()
    def filterText(self, text):
        self.hide()
        return False

class PlaApplicationLauncher(gtk.EventBox):

    def __init__(self, Name, RecentImage, ExceString, Png):
        gtk.EventBox.__init__(self)
        
        self.drag = True
        self.connections = []
        self.category = _("My Computer")
        self.cmd = ExceString
        self.path = Name
        self.png = Png
        
        self.Frame = gtk.Fixed()
        self.set_visible_window(0)
        self.add(self.Frame)

        self.Image = gtk.Image()
        #sel = gtk.gdk.pixbuf_get_file_info(Globals.ImageDirectory + Globals.ButtonBackImage)
	self.w = Globals.button_back_size[0] #sel[1]
	self.h = Globals.button_back_size[1] #sel[2]
        self.Image.set_from_pixbuf(None)
        self.set_size_request(self.w, self.h)
        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)

        self.buttonImage = gtk.Image()
        self.buttonImage.set_from_pixbuf(RecentImage)
        self.Frame.put(self.buttonImage, Globals.ButtonBackIconX, Globals.ButtonBackIconY)

        self.addLabel(os.path.basename(Name))
        
        self.connectSelf("enter_notify_event", self.enter)
        self.connectSelf("leave_notify_event", self.leave)
        
    def execute(self):
        command = self.cmd
        if command == "nautilus-connect-server":
            os.system('%s &' % command)
        else:
            if command == '':
                command = "computer:///"
            os.system("xdg-open '%s' &" % command)
        
    def connectSelf(self, event, callback):
        self.connections.append(self.connect(event, callback))
    
    def setSelectedTab(self, flag):
        if flag == True:
            self.pic = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.ButtonBackImage)
            self.Image.set_from_pixbuf(self.pic)  
	    del self.pic
        else:
            self.Image.set_from_pixbuf(None)
        
    def addLabel(self, text):
        self.Label = gtk.Label()
        
        text = "<span size=\"%s\" foreground=\"#FFFFFF\">%s</span>" % (Globals.MFontSize, text)
        self.Label.set_markup(text)

        self.Label.set_alignment(0.0, 0.0)
        self.Label.set_width_chars(21)
        self.Label.set_ellipsize(pango.ELLIPSIZE_END)
        self.Frame.put(self.Label, Globals.ButtonBackNameX, Globals.ButtonBackNameY)
    
    def enter (self, widget, event):
        self.setSelectedTab(True)

    def leave (self, widget, event):
        self.setSelectedTab(False)  
        
    def filterCategory(self, category):
        if category == self.category:
            self.show_all()
        else:
            self.hide()
            
    def filterText(self, text):
        keywords = text.lower().split()
        appName = (os.path.basename(self.path).lower())
        appGenericName = (self.path.lower())
        appComment = (self.path.lower())
        appExec = (self.cmd.lower())
        for keyword in keywords:
            keyw = (keyword)
            if keyw != "" and appName.find(keyw) == -1 and appGenericName.find(keyw) == -1 and appComment.find(keyw) == -1 and appExec.find(keyw) == -1:
                self.hide()
                return False

        self.show()
        return True

class RecApplicationLauncher(gtk.EventBox):

    def __init__(self, Name, RecentImage, ExceString):
        gtk.EventBox.__init__(self)
        
        self.drag = True
        self.connections = []
        self.category = _("Recent")
        self.cmd = ExceString
        self.path = Name
        
        command = unquote(str(self.cmd))
        if os.path.isfile(self.path) or os.path.isdir(command.replace('file://', '')):
            self.flag = True
        else:self.flag = False
        
        self.Frame = gtk.Fixed()
        self.set_visible_window(0)
        self.add(self.Frame)

        self.Image = gtk.Image()
        #sel = gtk.gdk.pixbuf_get_file_info(Globals.ImageDirectory + Globals.ButtonBackImage)
	self.w = Globals.button_back_size[0] #sel[1]
	self.h = Globals.button_back_size[1] #sel[2]
	sel = None
        self.Image.set_from_pixbuf(sel)
        self.set_size_request(self.w, self.h)
        self.Image.set_size_request(self.w, self.h)
        self.Frame.set_size_request(self.w, self.h)
        self.Frame.put(self.Image, 0, 0)
        
        self.buttonImage = gtk.Image()
        self.buttonImage.set_from_pixbuf(RecentImage)
        self.Frame.put(self.buttonImage, Globals.ButtonBackIconX, Globals.ButtonBackIconY)
        
        self.addLabel(os.path.basename(Name))
        
        self.connectSelf("enter_notify_event", self.enter)
        self.connectSelf("leave_notify_event", self.leave)
        
    def execute(self):
        if self.flag:
            os.system("xdg-open '%s' &" % self.cmd)

    def connectSelf(self, event, callback):
        self.connections.append(self.connect(event, callback))
    
    def setSelectedTab(self, flag):
	self.Search_Flag = False
        if flag == True:
            self.pic = gtk.gdk.pixbuf_new_from_file(Globals.ImageDirectory + Globals.ButtonBackImage)
            self.Image.set_from_pixbuf(self.pic)  
	    del self.pic
        else:
            self.Image.set_from_pixbuf(None)
        
    def addLabel(self, text):
        self.Label = gtk.Label()        
        if self.flag:
            text = "<span size=\"%s\" foreground=\"#FFFFFF\">%s</span>" % (Globals.MFontSize, text )
        else:text = "<span size=\"%s\" foreground=\"#A52A2A\">%s</span>" % (Globals.MFontSize, text )
        self.Label.set_markup(text)

        self.Label.set_alignment(0.0, 0.0)
        self.Label.set_width_chars(21)
        self.Label.set_ellipsize(pango.ELLIPSIZE_END)
        self.Frame.put(self.Label, Globals.ButtonBackNameX, Globals.ButtonBackNameY)
    
    def enter (self, widget, event):
        self.setSelectedTab(True)

    def leave (self, widget, event):
        self.setSelectedTab(False)  
        
    def filterCategory(self, category):
        if category == self.category:
            self.show_all()
        else:
            self.hide()
            
    def filterText(self, text):
        keywords = text.lower().split()
        appName = (os.path.basename(self.path).lower())
        appGenericName = (self.path.lower())
        appComment = (self.path.lower())
        appExec = (self.cmd.lower())
        for keyword in keywords:
            keyw = (keyword)
            if keyw != "" and appName.find(keyw) == -1 and appGenericName.find(keyw) == -1 and appComment.find(keyw) == -1 and appExec.find(keyw) == -1:
                self.hide()
                return False
        self.show()
        return True
    
iconManager = IconManager()

class ProgramClass(gobject.GObject):
    __gsignals__ = {
        'activate': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'menu': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'right-clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'NeedSearch': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'NotNeedSearch':(gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }
    
    def __init__(self, Frame):
        gobject.GObject.__init__ (self)
       
	self.CurcategoryValue = "" # Apps category value
	self.Search_Flag = False
        self.MenuWin = Frame

        # app category list
        self.Category_VBox = gtk.VBox(False)
	self.Category_Scr = gtk.ScrolledWindow()
	self.Category_Scr.set_size_request(Globals.PG_tabframedimensions[0], Globals.PG_tabframedimensions[1])
	self.Category_Scr.set_shadow_type(gtk.SHADOW_NONE)
	self.Category_Scr.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
	
	self.Category_Scr.add_with_viewport(self.Category_VBox)
	self.Category_Scr.get_children()[0].set_shadow_type(gtk.SHADOW_NONE)
	self.Category_Scr.get_children()[0].modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(Globals.PG_bgcolor))
        
        #self.Category_VBox.set_size_request(Globals.PG_tabframedimensions[0], Globals.PG_tabframedimensions[1])
	self.MenuWin.put(self.Category_Scr, Globals.PG_tabframe[0], Globals.PG_tabframe[1])
	
        # app list
        gtk.rc_parse (Globals.ThemeDirectory + "gtk/scrollbar")
        self.App_Scr = gtk.ScrolledWindow()
        self.App_VBox = gtk.VBox(False)
        
	self.App_Scr.set_size_request(Globals.PG_buttonframedimensions[0], Globals.PG_buttonframedimensions[1])
	self.App_Scr.set_shadow_type(gtk.SHADOW_NONE)
	self.App_Scr.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        
        self.App_Scr.add_with_viewport(self.App_VBox)
        self.App_Scr.get_children()[0].set_shadow_type(gtk.SHADOW_NONE)
        self.App_Scr.get_children()[0].modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(Globals.App_bgcolor))
        self.MenuWin.put(self.App_Scr, Globals.PG_buttonframe[0], Globals.PG_buttonframe[1])
                
        self.filterTimer = None
        self.menuChangedTimer = None

        self.prev_selTab = None # 因"软件中心"不参与过滤, 在选择其后恢复前所选项的背景

        self.buildingButtonList = False
        self.stopBuildingButtonList = False

        self.categoryList = []
        self.applicationList = []
        self.suggestions = []
        self.favorites = []
        self.FileList = []
        self.RecentList = []
        self.PlacesList = []
        
        self.rebuildLock = False
        self.activeFilter = (1, "")
	self.cate_button = None
        self.adminMenu = None
        
        self.IconFactory = IconFactory.IconFactory()

        self.user_app = gio.File("/usr/share/applications").monitor_directory()
        self.user_app.connect_after("changed", self.menuChanged)

        self.wine_app = gio.File("%s/.local/share/applications" % Globals.HomeDirectory).monitor_directory(gio.FILE_MONITOR_NONE, None)
        self.wine_app.connect("changed", self.menuChanged)
        
        self.wine = gio.File("/etc/xdg/menus/applications-merged").monitor_directory(gio.FILE_MONITOR_NONE, None)
        self.wine.connect("changed", self.menuChanged, 100)
        
        self.recent_manager = gtk.recent_manager_get_default()
        self.recent_manager.connect("changed", self.buildRecent)

        self.monitor = gio.volume_monitor_get()
        self.monitor.connect("mount-removed", self.buildPlaces)
        self.monitor.connect("mount-added", self.buildPlaces)

    def destroy(self):
        self.App_VBox.destroy()
        self.Category_VBox.destroy()
    
    def Restart(self, data=None):
        pass

    def SetInputFocus(self):
		pass

    def buildPlaces (self, * args, ** kargs):
        self.NameList, self.IconsList, self.PathList, self.PngList = self.getDrive()
        loc = 0
        if self.PlacesList != None:
            for item in self.PlacesList:
                item.destroy() 
        self.PlacesList = []
	for Name in self.NameList:
            if Name != None:
                plaButton = PlaApplicationLauncher(Name, self.IconsList[loc], self.PathList[loc], self.PngList[loc])
                plaButton.connect("button-release-event", self.activateButton)
                if Globals.Settings['Show_Tips']:
                    plaButton.Frame.set_tooltip_text(Name)
                self.App_VBox.pack_start(plaButton, False)
                self.PlacesList.append(plaButton)
            loc = loc + 1
    
    def getDrive(self):
        NameList = []
        IconsList = []
        PathList = []
        PngList = []
        
        NameList.append(_("File System"))
        IconsList.append(self.IconFactory.geticonfile("drive-harddisk"))
        PathList.append("/")
        PngList.append("drive-harddisk")
        
        self.drives = self.monitor.get_connected_drives()
	for drive in self.drives:
            if drive.has_media():
		self.mounts = drive.get_volumes()
		for mount in self.mounts:
                    ico = mount.get_icon()
                    a = self.IconFactory.getgicon(ico)
                    NameList.append(mount.get_name())
                    IconsList.append(self.IconFactory.geticonfile(a))
                    try:
			PathList.append(str(mount.get_mount().get_root().get_uri()))
                    except:
                        PathList.append("")
                    PngList.append(a)

        NameList.append(_('Network'))
        IconsList.append(self.IconFactory.geticonfile("gtk-network"))
        PathList.append('network:///')
        PngList.append("network")

        NameList.append(_('Connect to Server'))
        IconsList.append(self.IconFactory.geticonfile("applications-internet"))
        PathList.append('nautilus-connect-server')
        PngList.append("applications-internet")

        NameList.append(_('Home Folder'))
        IconsList.append(self.IconFactory.geticonfile("user-home"))
        PathList.append(Globals.HomeDirectory)
        PngList.append("user-home")

        if os.path.isfile("%s/.gtk-bookmarks" % Globals.HomeDirectory):
            f = open("%s/.gtk-bookmarks" % Globals.HomeDirectory, "r")
            data = f.readlines(600)
            f.close()
            f = None
            for i in data:		
		self.bm = str(i).replace("\n", "")
		if self.bm.find(' ') != -1:
                    self.folder = url2pathname(self.bm[:self.bm.find(' ')])
                    self.name = url2pathname(self.bm[self.bm.find(' ') + 1:])
		else: 
                    self.folder = self.bm
                    self.name = url2pathname(str(self.bm).split("/").pop()) 
		try:
                    Gfile = gio.File(self.folder)
                    tuble = [Gfile, Gfile.query_info("standard::*"), []]
                    ico = tuble[1].get_icon()
                    NameList.append(self.name)
                    IconsList.append(self.IconFactory.geticonfile(self.IconFactory.getgicon(ico)))
                    PathList.append(self.folder)
                    PngList.append(self.IconFactory.getgicon(ico))
                except:pass

        NameList.append(_('Trash'))
        IconsList.append(self.IconFactory.geticonfile("user-trash"))
        PathList.append('trash:///')
        PngList.append("user-trash")

        return NameList, IconsList, PathList, PngList     
    
    def buildRecent(self, * args, ** kargs):
        self.FileList, self.IconList, self.ExceList = self.getRecent()
	loc = 0
	if self.RecentList != None:
            for item in self.RecentList:
                item.destroy()
     	self.RecentList = []
	for Name in self.FileList:
            if Name != None:
                recButton = RecApplicationLauncher(Name, self.IconList[loc], self.ExceList[loc])
                recButton.connect("button-release-event", self.activateButton, recButton.flag)
                if Globals.Settings['Show_Tips']:
		    if not recButton.flag:
                        txt = _(':The path is invalid')
                        recButton.Frame.set_tooltip_text(Name + txt)
                    else:recButton.Frame.set_tooltip_text(Name)	
                self.App_VBox.pack_start(recButton, False)
                self.RecentList.append(recButton)
		if self.CurcategoryValue == _("Recent"):
		    recButton.show_all()
            loc = loc + 1
        return True 
    
    def getRecent(self):
	FileString = []
	IconString = []
        ExceString = []
	RecentInfo = self.recent_manager.get_items()
	# print RecentInfo[0].get_icon(gtk.ICON_SIZE_MENU)
	count = 0
	MaxEntries = Globals.RI_numberofitems
	for items in RecentInfo:
            FileString.append(items.get_uri_display())
            IconString.append(items.get_icon(Globals.PG_iconsize))
            ExceString.append(items.get_uri())
            count += 1
            if count >= MaxEntries:
		break
	return FileString, IconString, ExceString
    
    def do_recent_applications_file(self):
    
        pass
    def buildFavorites(self):
        try:
            filedir = Globals.Favorites
            addedFavorites = []
            newFavorites = []
            removeFavorites = []
            for filename in os.listdir(filedir):
                newFavorites.append(filedir + filename)
            
            if not self.favorites:
                addedFavorites = newFavorites
            else:
                for filename in newFavorites:
                    found = False
                    for filename2 in self.favorites:
                        if filename == filename2.Name:
                            found = True
                            break
                    if not found:
                        addedFavorites.append(filename)
                        
                key = 0        
                for filename in self.favorites:
                    found = False
                    for filename2 in newFavorites:
                        if filename.Name == filename2:
                            found = True
                            break
                    if not found:
                        print filename.Name
                        removeFavorites.append(key)
                    else:
                        key += 1
            for key in removeFavorites:
            	self.favorites[key].destroy()
                del self.favorites[key]
            
            for filename in addedFavorites:
                favButton = FavApplicationLauncher(filename, Globals.PG_iconsize)
                if favButton.appExec:
                    favButton.connect("enter-notify-event", self.Button_enter, True)
                    favButton.connect("leave-notify-event", self.Button_leave, False)
                    favButton.connect("button-release-event", self.activateButton)
                    favButton.show_all()
                    if Globals.Settings['Show_Tips']:
                        favButton.Frame.set_tooltip_text(favButton.getTooltip())
                    self.favorites.append(favButton)    
                    self.App_VBox.pack_start(favButton, False)
        except Exception, e:
            print u"File in favorites not found: '", e
    
    def buildButtonList(self, hide_method):
        self.hide_method = hide_method
        if self.buildingButtonList:
            self.stopBuildingButtonList = True
            gobject.timeout_add(100, self.buildButtonList)
            return

        self.stopBuildingButtonList = False

        self.updateBoxes(False)
    
    def menuChanged(self, monitor=None, Gfile=None, data=None, event=None, timer=2000):
        file = Gfile.get_path()
        if file.endswith("desktop"):
            i = 0
            while event == gio.FILE_MONITOR_EVENT_CREATED and i <= 180:
                if os.path.isfile(file):
                    break
                time.sleep(1)
                print i
                i += 1

        if self.menuChangedTimer:
            gobject.source_remove(self.menuChangedTimer)

        self.menuChangedTimer = gobject.timeout_add(timer, self.updateBoxes, True)		
        
    def ExecCommand(self, widget, event, item):
        if item["name"] == _("Software Center"):
            os.system("%s &" % Globals.CategoryCommands['Y Center'])
            if self.prev_selTab: 
                widget.setSelectedTab(False)
                self.prev_selTab.setSelectedTab(True)
        elif item["name"] == _("Control Panel"):
            os.system("%s &" % Globals.CategoryCommands['Control Panel'])


    def updateBoxes(self, menu_has_changed):
        # FIXME: This is really bad!
        if self.rebuildLock:            
            return

        self.rebuildLock = True

        self.menuChangedTimer = None
        
        self.loadMenuFiles()

        # Find added and removed categories than update the category list
        newCategoryList = self.buildCategoryList()
        addedCategories = []
        removedCategories = []
        
        if not self.categoryList:
            addedCategories = newCategoryList          
        else:
            for item in newCategoryList:
                found = False
                for item2 in self.categoryList:
                    if item["name"] == item2["name"] and item["tooltip"] == item2["tooltip"] and item["index"] == item2["index"]:
                        found = True
                        break
                if not found:
                    addedCategories.append(item)
            
            key = 0
            for item in self.categoryList:
                found = False
                for item2 in newCategoryList:
                    if item["name"] == item2["name"] and item["tooltip"] == item2["tooltip"] and item["index"] == item2["index"]:
                        found = True
                        break
                if not found:
                    print key
                    removedCategories.append(key)
                else:
                    key += 1
        del newCategoryList		   

        for key in removedCategories:
            print self.activeFilter[1], self.categoryList[key]["name"]
            if self.activeFilter[1] == self.categoryList[key]["name"]:
                self.Select_install("")
                self.categoryList[0]["button"].setSelectedTab(True)
                
            self.categoryList[key]["button"].destroy()
            del self.categoryList[key]
          
        if addedCategories:
            sortedCategoryList = []
            for item in self.categoryList[0:-5]:
                self.Category_VBox.remove(item["button"])
                sortedCategoryList.append((item["name"], item["button"]))
            
            for item in addedCategories:
                item["button"] = CategoryTab(item["name"])
                
                if Globals.Settings['Show_Tips']:
                    item["button"].Frame.set_tooltip_text(item["tooltip"])
                    
                if Globals.Settings['TabHover']:
		    if item["name"] == _("Software Center") or item["name"] == _("Control Panel"): 
                        needfilter = item["name"] == _("Control Panel") 
                        item["button"].connect("enter-notify-event", self.StartFilter, item["filter"], needfilter) 
			item["button"].connect("button-release-event", self.ExecCommand, item) 
		    else: 
			item["button"].connect("enter-notify-event", self.StartFilter, item["filter"]) 

		    item["button"].connect("leave-notify-event", self.StopFilter) 

		elif item["name"] == _("Software Center"):
	             item["button"].connect("button-release-event", self.ExecCommand, item) 
		else: 
                    item["button"].connect("button-release-event", self.Filter, item["filter"], True)

                item["button"].show_all()
                
                if item["filter"] == "" and not menu_has_changed:
                    self.all_app = item["button"]
                    item["button"].setSelectedTab(True)
		elif menu_has_changed:
                    for id in self.categoryList:
                        id["button"].setSelectedTab(False)
                    item["button"].setSelectedTab(True)
                    
                self.categoryList.append(item)
                sortedCategoryList.append((item["name"], item["button"]))
            del addedCategories
	    
            if has_gst:
		self.StartEngine()
   
            if menu_has_changed == True:
                for item in sortedCategoryList:
                    self.Category_VBox.pack_start(item[1], False)
            
            else:
                for item in sortedCategoryList[0:-5]:
                    self.Category_VBox.pack_start(item[1], False)
                for item in sortedCategoryList[-5:]:
                    self.Category_VBox.pack_end(item[1], False)
            del sortedCategoryList            
            
        # Find added and removed applications add update the application list
        newApplicationList = self.buildApplicationList()
        addedApplications = []
        removedApplications = []
        
        if not self.applicationList:
            addedApplications = newApplicationList         
        else:
            for item in newApplicationList:
                found = False
                for item2 in self.applicationList:
                    if item["entry"].DesktopEntry.getFileName() == item2["entry"].DesktopEntry.getFileName() and item["category"] == item2["category"] \
                    and item["entry"].DesktopEntry.getName() == item2["entry"].DesktopEntry.getName() \
                    and item["entry"].DesktopEntry.getIcon() == item2["entry"].DesktopEntry.getIcon() \
                    and item["entry"].DesktopEntry.getComment() == item2["entry"].DesktopEntry.getComment():
                        found = True
                        break
                if not found:
                    print "item[entry]==", item["entry"].DesktopEntry.getFileName()
                    addedApplications.append(item)

            key = 0
            for item in self.applicationList:
                found = False
                for item2 in newApplicationList:
                    if item["entry"].DesktopEntry.getFileName() == item2["entry"].DesktopEntry.getFileName() and item["category"] == item2["category"] \
                    and item["entry"].DesktopEntry.getName() == item2["entry"].DesktopEntry.getName() \
                    and item["entry"].DesktopEntry.getIcon() == item2["entry"].DesktopEntry.getIcon() \
                    and item["entry"].DesktopEntry.getComment() == item2["entry"].DesktopEntry.getComment():
                        found = True
                        break
                if not found:
                    print key
                    removedApplications.append(key)
                else:
                    key += 1
        del newApplicationList
	
        for key in removedApplications:
            self.applicationList[key]["button"].destroy()
            del self.applicationList[key] 
          
        if addedApplications:
            self.sortedApplicationList = []
            for item in self.applicationList:
                self.App_VBox.remove(item["button"])
                self.sortedApplicationList.append((item["button"].appName, item["button"]))
                
	    lock = threading.Lock()
	    threadlist = []
            for item in addedApplications:
	        t = threading.Thread(target = self.CreateAppLauncher, args=(lock, item, menu_has_changed))
		t.daemon = True
		t.start()
		threadlist.append(t)

	    for t in threadlist:
	    	t.join()
            del addedApplications     
	    
            self.sortedApplicationList.sort()
            for item in self.sortedApplicationList:     
                self.App_VBox.pack_start(item[1], False)
            del self.sortedApplicationList
            if menu_has_changed:
                for id in self.categoryList:
                    if id["filter"] == self.categoryid: 
                        id["button"].setSelectedTab(True)
                    else:id["button"].setSelectedTab(False)
                self.Select_install(self.categoryid)
		self.prev_selTab = None
                     
        self.rebuildLock = False
        gc.collect()

    def CreateAppLauncher(self, lock, item, menu_has_changed):
	item["button"] = MenuApplicationLauncher(item["entry"].DesktopEntry.getFileName(), Globals.PG_iconsize, item["category"], True, highlight=(True and menu_has_changed))
	if item["button"].appExec:
	    if Globals.Settings['Show_Tips']:
		item["button"].Frame.set_tooltip_text(item["button"].getTooltip())
	    item["button"].connect("enter-notify-event", self.Button_enter, True)
	    item["button"].connect("leave-notify-event", self.Button_leave, False)
	    if menu_has_changed:
		item["button"].setSelectedTab(True)
		self.categoryid = item["category"]
	    item["button"].connect("button-release-event", self.activateButton)
	    item["button"].show_all()

	    lock.acquire()
	    self.sortedApplicationList.append((item["button"].appName.upper(), item["button"]))
	    self.applicationList.append(item)
	    lock.release()
	else:
	    item["button"].destroy() 
	    
    def activateButton(self, widget, event, date=True):
        if event.type == gtk.gdk.KEY_PRESS:event_button = 1
	elif event.type == gtk.gdk.BUTTON_PRESS:event_button = event.button
	elif event.type == gtk.gdk.BUTTON_RELEASE:event_button = event.button

        if event_button == 1 and widget.drag and date == True:
            self.hide_method()
            widget.execute()
        widget.drag = True
 
        if event_button == 3:
            mouse = widget.get_pointer()
            x = 0
            y = 0
 
            w = x + widget.get_allocation().width
            h = y + widget.get_allocation().height

            if mouse[0] > x and mouse[0] < w and mouse[1] > y and mouse[1] < h:
                self.emit('right-clicked')
                self.emit('menu')
                self.menuPopup(widget, event)
            
    def menuPopup(self, widget, event):
        mTree = gtk.Menu() 
           
        if isinstance(widget, RecApplicationLauncher):
            f = widget.path
            if os.path.isfile(f):
                openwith = add_image_menuitem(mTree, gtk.STOCK_OPEN, _("Open with"))
                Gfile = gio.File(f)
                tuble = [Gfile, Gfile.query_info("standard::*"), []]
                                                
                apps = gio.app_info_get_all_for_type(tuble[1].get_content_type())
                if apps != []:
                    submenu = gtk.Menu()
                    openwith.set_submenu(submenu)
                    add_menuitem(mTree, "-")
                for app in apps:
                    add_menuitem(submenu, app.get_name(), self.custom_launch, "'" + f + "'", app.get_executable())
            add_image_menuitem(mTree, gtk.STOCK_CLEAR, _("Clear recent documents"), self.del_to_rec, widget)
            
        elif isinstance(widget, PlaApplicationLauncher):
            f = widget.cmd.replace('file://', '')
            f = unquote(str(f))
            name = widget.path
            def searchfolder(folder, me):
                dirs = os.listdir(folder)
		dirs.sort(key=str.upper)
                                                
		for item in dirs:
                    if not item.startswith('.'):
                        if os.path.isdir(os.path.abspath(folder) + '/' + item):
                            add_image_menuitem(me, gtk.STOCK_DIRECTORY, item, self.launch_item, os.path.abspath(folder.replace('file://', '')) + '/' + item)
			else:   
                            submenu_item = gtk.MenuItem(item, use_underline=False)
                            me.append(submenu_item)
                            submenu_item.connect("button-press-event", self.launch_item, os.path.abspath(folder) + '/' + item)
                            submenu_item.show()
            
            if os.path.isdir(f):
                submenu = gtk.Menu()
                thismenu = add_image_menuitem(mTree, gtk.STOCK_REDO, name, None, None)
		if os.listdir(f) != []:
                    thismenu.set_submenu(submenu)
                    searchfolder(f, submenu)
                add_menuitem(mTree, "-")
            add_image_menuitem(mTree, gtk.STOCK_HOME, _("Create Desktop Shortcut"), self.add_to_desktop, widget)
                    
        else:    
	    if not os.path.isdir(Globals.PanelLauncher):
		print "Dir: %s is not exist, create it\n" % Globals.PanelLauncher
                try:
                    os.makedirs(Globals.PanelLauncher, 0700)
                except OSError:
                    pass
            if (os.path.basename(widget.desktopFile)) in os.listdir(Globals.PanelLauncher): 
                add_image_menuitem(mTree, gtk.STOCK_REMOVE, _("Remove from Panel"), self.del_to_panel, widget)
            else:
                add_image_menuitem(mTree, gtk.STOCK_ADD, _("Add to Panel"), self.add_to_panel, widget)
            add_image_menuitem(mTree, gtk.STOCK_HOME, _("Create Desktop Shortcut"), self.add_to_desktop, widget)
            add_menuitem(mTree, "-")    
        
            if (os.path.basename(widget.desktopFile)) in os.listdir(Globals.Favorites):
                add_image_menuitem(mTree, gtk.STOCK_REMOVE, _("Remove from Favorites"), self.del_to_fav, widget)
            else:
                add_image_menuitem(mTree, gtk.STOCK_ADD, _("Add to Favorites"), self.add_to_fav, widget)
            
            if not os.path.isdir(Globals.AutoStartDirectory):
                os.system('mkdir %s' % Globals.AutoStartDirectory)
            if (os.path.basename(widget.desktopFile)) in os.listdir(Globals.AutoStartDirectory):
                add_image_menuitem(mTree, gtk.STOCK_REMOVE, _("Remove from System Startup"), self.remove_autostarter, widget)
            else:
		add_image_menuitem(mTree, gtk.STOCK_ADD, _("Add to System Startup"), self.create_autostarter, widget)
            add_menuitem(mTree, "-")

            add_image_menuitem(mTree, gtk.STOCK_DIALOG_AUTHENTICATION, _("Open as Administrator"), self.runasadmin, widget)
        mTree.popup(None, None, None, event.button, event.time)

    def create_autostarter (self, widget, event, desktopEntry):
	if not os.path.isdir(Globals.AutoStartDirectory):
            os.system('mkdir %s' % Globals.AutoStartDirectory)
        os.system("cp \"%s\" \"%s\"" % (desktopEntry.desktopFile, Globals.AutoStartDirectory))

    def remove_autostarter (self, widget, event, desktopEntry):
	os.system('rm "%s%s"' % (Globals.AutoStartDirectory, os.path.basename(desktopEntry.desktopFile)))

    def runasadmin(self, widget, event, desktopEntry):
	os.system('%s "%s" &' % (Globals.Settings['AdminRun'], desktopEntry.appExec))

    def del_to_rec(self, widget, event, desktopEntry):
        self.recent_manager.purge_items()

    def custom_launch(self, widget, event, uri, app):
        os.system('%s %s &' % (app, uri))
        self.hide_method()
        
    def launch_item(self, button, event, uri):
        os.system('xdg-open %s &' % uri)
        self.hide_method()		
	
    def del_to_fav(self, widget, event, desktopEntry):
        os.system("rm %s%s" % (Globals.Favorites, os.path.basename(desktopEntry.desktopFile)))

    def add_to_fav(self, widget, event, desktopEntry):
        os.system("cp \"%s\" \"%s\"" % (desktopEntry.desktopFile, Globals.Favorites))  

    def add_to_desktop(self, widget, event, desktopEntry):
        if isinstance(desktopEntry, PlaApplicationLauncher):
            path = desktopEntry.path
            icon = desktopEntry.png
            cmd = desktopEntry.cmd
            import utils
            tmpdesktopDir = utils.xdg_dir("XDG_DESKTOP_DIR")
            print tmpdesktopDir
            starter = '%s/%s.desktop' % (tmpdesktopDir, path)
            code = ['#!/usr/bin/env xdg-open', '[Desktop Entry]']
            code.append('Name=%s' % path)
            code.append('StartupNotify=true')
            code.append('Terminal=false')
            code.append('Version=1.0')
            code.append('Icon=%s' % icon)
            code.append('Type=Application')
		
            code.append('Exec= xdg-open %s' % cmd)
            code.append('X-GNOME-Autostart-enabled=true')
		
            f = open(starter, 'w')
            if f:
                for l in code:
                    f.write(l + '\n')
		f.close()
                
            os.system("chmod a+rx \'%s\'" % starter)
        
        else:    
            # Determine where the Desktop folder is (could be localized)
            from configobj import ConfigObj
            config = ConfigObj(home + "/.config/user-dirs.dirs")
            desktopDir = home + "/Desktop"
            tmpdesktopDir = config['XDG_DESKTOP_DIR']
            tmpdesktopDir = commands.getoutput("echo " + tmpdesktopDir)
            if os.path.exists(tmpdesktopDir):
                desktopDir = tmpdesktopDir
            # Copy the desktop file to the desktop
            os.system("cp \"%s\" \"%s/\"" % (desktopEntry.desktopFile, desktopDir))
            os.system("chmod a+rx %s/*.desktop" % (desktopDir))
            
    
    def add_to_panel (self, widget, event, desktopEntry):
        """Add Panel"""
        import random
        object_name = "object_" + ''.join([random.choice('0123456789') for x in xrange(2)])
        object_dir = "/apps/panel/objects/"
                
        object_client = gconf.client_get_default()
        appletidlist = object_client.get_list("/apps/panel/general/applet_id_list", "string")
        for applet in appletidlist:
            applet_id = object_client.get_string("/apps/panel/applets/" + applet + "/applet_iid")
            if applet_id == "OAFIID:GNOME_YMenu":
                self.panel = object_client.get_string("/apps/panel/applets/" + applet + "/toplevel_id")
                self.panel_position = object_client.get_int("/apps/panel/applets/" + applet + "/position") + 4
        if not os.path.isdir(Globals.PanelLauncher):
            os.system('mkdir %s' % Globals.PanelLauncher)
    
        os.system("cp \"%s\" \"%s/\"" % (desktopEntry.desktopFile, Globals.PanelLauncher))
        panel_file = Globals.PanelLauncher + "/" + os.path.basename(desktopEntry.desktopFile)
        os.system("chmod a+rx %s" % (panel_file))        
            
        object_client.set_string(object_dir + object_name + "/" + "menu_path", "applications:/")
        object_client.set_bool(object_dir + object_name + "/" + "locked", False)
        object_client.set_int(object_dir + object_name + "/" + "position", self.panel_position)
        object_client.set_string(object_dir + object_name + "/" + "object_type", "launcher-object")
        object_client.set_bool(object_dir + object_name + "/" + "panel_right_stick", False)
        object_client.set_bool(object_dir + object_name + "/" + "use_menu_path", False)
        object_client.set_string(object_dir + object_name + "/" + "launcher_location", panel_file)
        object_client.set_string(object_dir + object_name + "/" + "custom_icon", "")
        object_client.set_string(object_dir + object_name + "/" + "tooltip", "")
        object_client.set_string(object_dir + object_name + "/" + "action_type", "lock")
        object_client.set_bool(object_dir + object_name + "/" + "use_custom_icon", False)
        object_client.set_string(object_dir + object_name + "/" + "attached_toplevel_id", "")
        object_client.set_string(object_dir + object_name + "/" + "applet_iid", "")
        object_client.set_string(object_dir + object_name + "/" + "toplevel_id", self.panel)

        launchers_list = object_client.get_list("/apps/panel/general/object_id_list", "string")
        launchers_list.append(object_name)
        object_client.set_list("/apps/panel/general/object_id_list", gconf.VALUE_STRING, launchers_list)
        
    
    def del_to_panel(self, widget, event, desktopEntry):
        object_client = gconf.client_get_default()
        launchers_list = object_client.get_list("/apps/panel/general/object_id_list", "string")
        for object in launchers_list:
            object_id = object_client.get_string("/apps/panel/objects/" + object + "/launcher_location")
            if object_id == "%s/%s" % (Globals.PanelLauncher, os.path.basename(desktopEntry.desktopFile)):
                launchers_list.remove(object)
                object_client.set_list("/apps/panel/general/object_id_list", gconf.VALUE_STRING, launchers_list)

    def Button_enter(self, widget, event, flag):
        widget.setSelectedTab(flag)
        
    def Button_leave(self, widget, event, flag):
        widget.setSelectedTab(flag)
    def CallSpecialMenu(self, command, data=None, searchbar_widget=None):
    	if self.cate_button != None:
            self.cate_button.setSelectedTab(False)
        self.all_app.setSelectedTab(True)
    	
        if command == 6:
            if Globals.searchitem == '' and searchbar_widget:                
                Globals.searchitem = searchbar_widget.entry.get_text()
            fulltext = "gnome-search-tool --named=\"%s\" &" % Globals.searchitem
            fulltext.replace('\n','')
            fulltext.replace('\r','')
            os.system(fulltext)
        else:
            netSearch = False
            for i in self.App_VBox.get_children():
                netSearch |= i.filterText(data)
            if not netSearch:
		self.Search_Flag = True
                self.emit('NeedSearch')
            else:
                self.emit('NotNeedSearch')
    def ReFilter(self):
	if (self.prev_selTab): 
	    self.prev_selTab.emit('enter_notify_event', None)
	    

    def StartFilter(self, widget, event, category, needfilter = True):

        if self.filterTimer:
            gobject.source_remove(self.filterTimer)
        self.filterTimer = gobject.timeout_add(80, self.Filter, widget, event, category, needfilter)
	self.Search_Flag = False

    def StopFilter(self, widget, event):
        if self.filterTimer:
            gobject.source_remove(self.filterTimer)
            self.filterTimer = None

    def Filter(self, widget, event, category, needfilter):
        
        #self.UpdateUserImage(widget, event, icon)
        self.CurcategoryValue = category
        self.emit('NotNeedSearch')
        for item in self.categoryList:
            item["button"].setSelectedTab(False)
        if needfilter:
            self.prev_selTab = widget # 用于在选择"软件中心"后返回标签用
        widget.setSelectedTab(True)
        self.activeFilter = (1, category)
        self.cate_button = widget
	if needfilter: 
	    for i in self.App_VBox.get_children():
		i.filterCategory(category)
        self.PlaySound(3)

    def Select_install(self, category=""):
        for i in self.App_VBox.get_children():
            i.filterCategory(category)
        
    def StartEngine(self):
	self.player = gst.element_factory_make("playbin", "player")
	fakesink = gst.element_factory_make('fakesink', "my-fakesink")
	self.player.set_property("video-sink", fakesink)
	self.player_bus = self.player.get_bus()
	self.player_bus.add_signal_watch()
	self.player_bus.connect('message', self.on_message)
     
    def on_message(self, bus, message):
	t = message.type
	if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
  
	elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL) 
     
    def PlaySound(self, sound):
        sound_client = gconf.client_get_default()
        sound_id = sound_client.get_bool("/desktop/gnome/sound/event_sounds")
	if Globals.Settings['Sound_Theme'] != 'None' and sound_id:
            if sound == 0:
            	uri = 'file://%s/share/ymenu/Themes/Sound/%s/show-menu.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
            elif sound == 1:
		uri = 'file://%s/share/ymenu/Themes/Sound/%s/hide-menu.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
            elif sound == 2:
		uri = 'file://%s/share/ymenu/Themes/Sound/%s/button-pressed.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])
            elif sound == 3:
		uri = 'file://%s/share/ymenu/Themes/Sound/%s/tab-pressed.ogg' % (INSTALL_PREFIX, Globals.Settings['Sound_Theme'])

            if has_gst:
                self.player.set_state(gst.STATE_NULL)
                self.player.set_property('uri', uri)
                self.player.set_state(gst.STATE_PLAYING)
            else:
                os.system('mplayer %s &' % uri)

    def loadMenuFiles(self):
        tree = xdg.Menu.parse("applications.menu")
        self.directory = tree.getEntries()
        del tree

        gnomecc_tree = xdg.Menu.parse("settings.menu")
        self.gnomecc_dir  = gnomecc_tree.getEntries()
        del gnomecc_tree

        self.menu_dir = []
        self.menu_dir.append({'dir' : self.gnomecc_dir, 'category' : u'gnomecc'})
        self.menu_dir.append({'dir' : self.directory,   'category' : u''})

    def buildCategoryList(self):
        newCategoryList = [{"name": _("All Applications"), "tooltip": _("Show all applications"), "filter":"", "index": 0}]
        
        num = 1

        for child in self.directory:#.get_contents():
            if isinstance(child, xdg.Menu.Menu):
                newCategoryList.append({"name": child.getName(), "tooltip": child.getComment(), "filter": child.getName(), "index": num})
        num += 1

        newCategoryList.append({"name": _("Software Center"), "tooltip": _("Software Center"), "filter":None, "index": num})
        newCategoryList.append({"name": _("Control Panel"), "tooltip": _("Control Panel"), "filter":"gnomecc" , "index": num + 1})
        newCategoryList.append({"name": _("My Computer"), "tooltip": _("Show all Places"), "filter": _("My Computer"), "index": num + 2})
        newCategoryList.append({"name": _("Recent"), "tooltip": _("Recent Documents"), "filter": _("Recent"), "index": num + 3})
        newCategoryList.append({"name": _("Favorites"), "tooltip": _("Show all Favorites"), "filter": _("Favorites"), "index": num + 4})
        return newCategoryList

    # Build a list containing the DesktopEntry object and the category of each application in the menu
    def buildApplicationList(self):

        newApplicationsList = []
        self.menu_dir[1]['dir'] = xdg.Menu.parse("applications.menu").getEntries()
        
        def find_applications_recursively(app_list, directory, catName):
            for item in directory.getEntries():
                if isinstance(item, xdg.Menu.MenuEntry):
                    app_list.append({"entry": item, "category": catName})
                elif isinstance(item, xdg.Menu.Menu):
                    find_applications_recursively(app_list, item, catName)
        
        for menu_dict in self.menu_dir:
            for entry in menu_dict['dir']:#.get_contents():
                if isinstance(entry, xdg.Menu.Menu):
                    for item in entry.getEntries():
                        entry_category = menu_dict["category"] and "gnomecc" or entry.getName()
                        if isinstance(item, xdg.Menu.Menu):
                            find_applications_recursively(newApplicationsList, item, entry_category)
                        elif isinstance(item, xdg.Menu.MenuEntry):
                            newApplicationsList.append({"entry": item, "category": entry_category})

        return newApplicationsList        
