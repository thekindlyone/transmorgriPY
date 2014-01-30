import wx,wx.html
from whoosh.index import open_dir
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh import highlight
import whoosh
import zipfile
import os
import sys
import shutil
import urllib

aboutText = """<p>transmorgiPY by Aritra Das. <br>contact: dodo.dodder@gmail.com <br><a href="https://github.com/thekindlyone/transmorgriPY">project github</a></p>"""

def download(url, dest):
    max = 2000
    dlg = wx.ProgressDialog("Download Progress",
                       "Please wait...",
                           maximum=max,
                           style = wx.PD_CAN_ABORT
                            | wx.PD_APP_MODAL
                            | wx.PD_ELAPSED_TIME
                            | wx.PD_ESTIMATED_TIME
                            )
    dlg.Update(0, "Please Wait...")
    fURL = urllib.urlopen(url)
    header = fURL.info()
    size = None    
    outFile = open(dest, 'wb')
    keepGoing = True
    if "Content-Length" in header:
        size = int(header["Content-Length"])
        kBytes = size/1024
        downloadBytes = size/max
        count = 0
        while keepGoing:
            count += 1
            if count >= max:
                count  = max-1
            done=(count*downloadBytes/1024)
            percentage='%.2f' %((done*100.0)/kBytes)
            
            (keepGoing, skip) = dlg.Update(count, "Downloaded "+str(done)+
                                                  " of "+ str(kBytes)+"KB  "+percentage+"% done")
            b = fURL.read(downloadBytes)
            if b:
                outFile.write(b)
            else:
                break
    else:
            while keepGoing:
                (keepGoing, skip) = dlg.UpdatePulse()
                b = fURL.read(1024*8)
                if b:
                    outFile.write(b)
                else:
                    break
    outFile.close()

    dlg.Update(99, "Downloaded "+ str(os.path.getsize(dest)/1024)+"KB")
    dlg.Destroy()
    return keepGoing

class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(600,400)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())

class AboutBox(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, "About transmorgriPy",
            style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME|wx.RESIZE_BORDER|
                wx.TAB_TRAVERSAL)
        hwin = HtmlWindow(self, -1, size=(400,200))
        vers = {}
        vers["python"] = sys.version.split()[0]
        vers["wxpy"] = wx.VERSION_STRING
        hwin.SetPage(aboutText % vers)
        btn = hwin.FindWindowById(wx.ID_OK)
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+10))
        self.SetClientSize(hwin.GetSize())
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()


class database(object):
    def __init__(self):
        self.ix=open_dir("index")
    def search(self,text):
        fetched=[]
        brf = highlight.UppercaseFormatter()
        with self.ix.searcher() as searcher:
            query = QueryParser("content", self.ix.schema).parse(text)
            results = searcher.search(query)
            results.fragmenter=highlight.WholeFragmenter()
            results.formatter = brf
            for result in results:
                fetched.append((result['title'],result.highlights("content")))
        return fetched


class gui(wx.Panel):

    def __init__(self,parent):
        self.parent=parent
        self.directory=os.getcwd()
        self.imageFile=None
        self.td=os.path.join(self.directory,'temp') #temp directory
        self.dbase=database()
        wx.Panel.__init__(self,parent)     
        

        
        vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.lastfile=''
        
        self.field=wx.TextCtrl(self, size=(180, -1),style=wx.TE_PROCESS_ENTER)
        self.field.Bind(wx.EVT_KEY_DOWN, self.onEnter)
        hsizer1.Add(self.field,1,wx.EXPAND)
        button = wx.Button(self,-1,"search")
        self.Bind( wx.EVT_BUTTON,self.button,button)

        hsizer1.Add(button,.1,wx.EXPAND)

        vsizer.Add(hsizer1,.1,wx.EXPAND)

        
        self.listbox = wx.ListBox(self, -1,style=wx.LB_NEEDED_SB|wx.LB_HSCROLL)
        
        self.Bind(wx.EVT_LISTBOX, self.onclick)
        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add(self.listbox,2,wx.EXPAND)
        vsizer.Add(hsizer2,1,wx.EXPAND)

        img = wx.EmptyImage(800,400)
        self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(img))
        
        self.imageCtrl.Hide()
        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer3.Add(self.imageCtrl,2,wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        vsizer.Add(hsizer3,2,wx.EXPAND)
        self.SetSizer(vsizer)
        

    #----------------------------------------------------------------------
    def onEnter(self, event):
        """"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER: 
            self.button(None)
        event.Skip()
        #self.pnl.Layout()

    
    def onclick(self,event):
        sel = self.listbox.GetSelection()
        strip=self.fetched[sel][0]+'.jpg'
        z=zipfile.ZipFile('cnh.cbz')
        z.extract(strip,self.td)
        self.Refresh()
        self.display(strip)
        

    
    def cleartemp(self,strip):
        map(os.remove,(os.path.join(self.td,f) for f in os.listdir(self.td) if f!=strip))
    
    def display(self,strip):
        self.imageFile = os.path.join(self.td,strip)
        jpg1 = wx.Image(self.imageFile, wx.BITMAP_TYPE_ANY)
        self.imageCtrl.SetBitmap(wx.BitmapFromImage(jpg1))
        self.imageCtrl.Show()
        self.Layout()
        self.Refresh()
        self.cleartemp(strip)
    

    
    
    def showresults(self):
        self.listbox.Clear() 
        for entry in self.fetched:
            self.listbox.Append(('--->'.join(entry)))
        self.listbox.SetFocus()
    
    def button(self,event):               
        self.fetched=self.dbase.search(self.field.GetValue())
        if self.fetched:
            self.showresults()
        else :
            print "not found"
            self.listbox.Clear()
    
    def OnAbout(self, event):
        dlg = AboutBox()
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnSave(self, event):
        if self.imageFile:
            saveFileDialog = wx.FileDialog(self, "Save As", self.directory, "", "jpeg files (*.jpg)|*.jpg", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            saveFileDialog.ShowModal()
            location=saveFileDialog.GetPath()
            if location :
                shutil.copyfile(self.imageFile,location)
            saveFileDialog.Destroy()
        


if __name__ == "__main__":
    app = wx.App()
    w,h=wx.DisplaySize()
    frame = wx.Frame(parent=None, id=-1, title="transmorgripy",size=(w/1.2,h/1.2 ))

    def OnClose(event):
        
        if panel.imageFile: os.remove(panel.imageFile)
        frame.Destroy()

    
    frame.Center()
    panel = gui(frame)
    url= 'http://thekindlyone.scribblehead.info/cnh.cbz'
    if not os.path.exists(panel.td):
        os.makedirs(panel.td)
    if not os.path.exists(os.path.join(os.getcwd(),'cnh.cbz')):
        print "Transmorgripy needs cnh.cbz to work. Downloading"
        success=download(url,'cnh.cbz')
        if not success:
            print "You really need the file. Bye Bye."
            os.remove(os.path.join(os.getcwd(),'cnh.cbz'))
            sys.exit()
    frame.Bind(wx.EVT_CLOSE, OnClose)
    menuBar = wx.MenuBar()
    menu = wx.Menu()
    save = menu.Append(wx.ID_EXIT, "&Save strip\tCtrl-S")
    frame.Bind(wx.EVT_MENU, panel.OnSave, save)
    menuBar.Append(menu, "&File")
    menu = wx.Menu()
    about = menu.Append(wx.ID_ABOUT, "&About")
    frame.Bind(wx.EVT_MENU, panel.OnAbout, about)
    menuBar.Append(menu, "&Help")
    frame.SetMenuBar(menuBar)

    frame.Show()
    app.MainLoop()