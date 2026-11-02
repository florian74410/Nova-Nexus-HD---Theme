"""NOVA Terminal manager: tabs, persistent shells, pane formats and text controls."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from PySide6 import QtCore as C, QtGui as G, QtWidgets as W
from healthbar.config import data_dir
from .chrome_v3 import make_window,make_dialog
from .terminal import TerminalSession,TerminalView

FORMATS={
    'single':('Terminal unique',1), 'columns':('2 colonnes',2),
    'rows':('2 lignes',2), 'grid':('2 + 2',4),
    'top_pair':('2 en haut + 1 en bas',3),
    'left_column':('1 colonne à gauche + 2 à droite',3),
}
DEFAULT_TEXT={'font':'DejaVu Sans Mono','size':11,'foreground':'#E9F6FF','background':'#06131F'}


class TerminalPane(W.QWidget):
    def __init__(self,owner,number,*,start,cwd=None):
        super().__init__(owner);self.owner=owner;self.number=number
        layout=W.QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(0)
        header=W.QWidget();header.setObjectName('paneHeader');row=W.QHBoxLayout(header);row.setContentsMargins(10,4,6,4)
        self.title=W.QLabel(f'◈  SESSION {number:02d}');self.title.setStyleSheet('color:#69E8F7;font:bold 10px Arial;');row.addWidget(self.title,1)
        self.state=W.QLabel(('ConPTY' if sys.platform=='win32' else 'SHELL / PTY') if start else 'APERÇU');self.state.setStyleSheet('color:#A6BFCD;font:9px Arial;');row.addWidget(self.state)
        close=W.QPushButton('×');close.setFixedSize(22,20);close.setStyleSheet('QPushButton{color:#FF647C;border:1px solid #248DA5;padding:0;font:bold 15px Arial;}');close.clicked.connect(lambda:owner.close_pane(self));row.addWidget(close)
        header.setStyleSheet('QWidget#paneHeader{background:#133345;border:1px solid #26738C;}');layout.addWidget(header)
        self.session=TerminalSession(self,cwd=cwd);self.view=TerminalView(self.session);self.view.installEventFilter(self)
        self.session.finished.connect(lambda code:self.state.setText('TERMINÉ · '+str(code)))
        layout.addWidget(self.view,1)
        if start:self.session.start()

    def eventFilter(self,watched,event):
        if event.type()==C.QEvent.FocusIn:
            self.owner.active=self
            self.owner.manager.update_status()
        return False

    def close_session(self):self.session.close()


class TerminalWorkspace(W.QWidget):
    def __init__(self,manager,*,start,cwd=None):
        super().__init__();self.manager=manager;self.start=start;self.cwd=cwd
        self.panes=[];self.active=None;self.splitter=None;self.format='single'
        self.root=W.QVBoxLayout(self);self.root.setContentsMargins(0,0,0,0)
        self.set_format('single')

    def set_format(self,format):
        count=FORMATS[format][1]
        while len(self.panes)<count:
            pane=TerminalPane(self,len(self.panes)+1,start=self.start,cwd=self.cwd)
            self.panes.append(pane);self.manager.apply_text(pane.view)
        for pane in self.panes:pane.setParent(self);pane.hide()
        if self.splitter:
            self.root.removeWidget(self.splitter);self.splitter.deleteLater()
        def split(orientation,*widgets):
            frame=W.QSplitter(orientation);frame.setChildrenCollapsible(False);frame.setHandleWidth(7)
            for widget in widgets:frame.addWidget(widget)
            frame.setSizes([600]*len(widgets));return frame
        a=self.panes
        if format=='single':self.splitter=split(C.Qt.Horizontal,a[0])
        elif format=='columns':self.splitter=split(C.Qt.Horizontal,*a[:2])
        elif format=='rows':self.splitter=split(C.Qt.Vertical,*a[:2])
        elif format=='grid':self.splitter=split(C.Qt.Vertical,split(C.Qt.Horizontal,*a[:2]),split(C.Qt.Horizontal,*a[2:4]))
        elif format=='top_pair':self.splitter=split(C.Qt.Vertical,split(C.Qt.Horizontal,*a[:2]),a[2])
        else:self.splitter=split(C.Qt.Horizontal,a[0],split(C.Qt.Vertical,*a[1:3]))
        self.root.addWidget(self.splitter,1);self.format=format
        for pane in a[:count]:pane.show()
        self.active=a[0];self.active.view.setFocus();self.manager.update_status()

    def close_pane(self,pane):
        pane.close_session();self.panes.remove(pane);pane.setParent(None);pane.deleteLater()
        count=len(self.panes)
        self.set_format({0:'single',1:'single',2:'columns',3:'top_pair'}.get(count,'grid'))

    def close_sessions(self):
        for pane in self.panes:pane.close_session()


class TerminalManager(C.QObject):
    def __init__(self,*,start=True,cwd=None):
        super().__init__();self.start=start;self.cwd=cwd;self.text=DEFAULT_TEXT.copy()
        try:
            saved=json.loads((data_dir()/'nova-terminal.json').read_text())
            for key in self.text:
                if key in saved:self.text[key]=saved[key]
            if not isinstance(self.text['font'],str) or not isinstance(self.text['size'],int) or not 8<=self.text['size']<=30:raise ValueError('Invalid text settings')
            if not all(G.QColor(self.text[key]).isValid() for key in ('foreground','background')):raise ValueError('Invalid colors')
        except (OSError,ValueError,TypeError):self.text=DEFAULT_TEXT.copy()
        content=W.QWidget();root=W.QVBoxLayout(content);root.setContentsMargins(0,0,0,0);root.setSpacing(7)
        self.menu=W.QMenuBar();root.addWidget(self.menu)
        self.tabs=W.QTabWidget();self.tabs.setTabsClosable(True);self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab);self.tabs.currentChanged.connect(self.update_status);root.addWidget(self.tabs,1)
        self.search_bar=W.QWidget();search_layout=W.QHBoxLayout(self.search_bar);search_layout.setContentsMargins(0,0,0,0)
        self.search=W.QLineEdit();self.search.setPlaceholderText('Rechercher dans le terminal actif…');search_layout.addWidget(self.search,1)
        self.search.returnPressed.connect(self.find_next)
        next_button=W.QPushButton('SUIVANT');next_button.clicked.connect(self.find_next);search_layout.addWidget(next_button)
        close=W.QPushButton('×');close.clicked.connect(self.search_bar.hide);search_layout.addWidget(close)
        root.addWidget(self.search_bar);self.search_bar.hide()
        footer=W.QHBoxLayout();self.status=W.QLabel();self.status.setStyleSheet('color:#A6BFCD;font:10px Arial;');footer.addWidget(self.status,1)
        self.format_button=W.QPushButton('◫  FORMATS');self.format_button.clicked.connect(self.open_formats);footer.addWidget(self.format_button)
        root.addLayout(footer)
        self.window=make_window('NOVA NEXUS  /  TERMINAL MANAGER',content)
        self.window.manager=self
        self.window.resize(1100,700);self.window.setMinimumSize(720,420)
        self.window.installEventFilter(self)
        self.window.setStyleSheet(self.window.styleSheet()+'''
            QMenuBar{background:#112C3D;color:#ECF8FF;border:1px solid #246980;padding:4px;}
            QMenuBar::item{padding:5px 14px;}QMenuBar::item:selected{background:#1A5871;color:#A8F6FF;}
            QMenu{background:#0E2636;color:#EBF8FF;border:1px solid #00CBEF;padding:5px;}
            QMenu::item{padding:7px 28px;}QMenu::item:selected{background:#20516A;}
            QTabWidget::pane{border:1px solid #24758E;background:transparent;}
            QTabBar::tab{background:#102F40;color:#A6BFCD;padding:8px 18px;border:1px solid #236077;}
            QTabBar::tab:selected{color:#A3F4FF;background:#19475C;border-top:2px solid #00CBF3;}
            QSplitter::handle{background:#15506A;border:1px solid #26849D;}
            QLineEdit,QFontComboBox,QSpinBox{background:#0A2232;color:#F2F8FF;border:1px solid #26849D;padding:6px;}
        ''')
        self.tabs.setStyleSheet("QTabBar::close-button{image:url("+str(Path(__file__).parent/'assets/nova-close.svg')+");width:20px;height:20px;}")
        self.build_menus();self.new_tab()
        self.window.setAttribute(C.Qt.WA_DeleteOnClose)
        from healthbar.cockpit_style import lookup_icon
        self.window.setWindowIcon(lookup_icon('utilities-terminal'))

    def workspace(self):return self.tabs.currentWidget()
    def active_view(self):
        space=self.workspace()
        return space.active.view if space and space.active else None

    def action(self,menu,label,callback,shortcut=None):
        item=menu.addAction(label);item.triggered.connect(callback)
        if shortcut:item.setShortcut(G.QKeySequence(shortcut))
        return item

    def build_menus(self):
        file=self.file_menu=self.menu.addMenu('Fichier')
        self.action(file,'Nouvel onglet',lambda:self.new_tab(),'Ctrl+Shift+T')
        self.action(file,'Nouvelle fenêtre',lambda:open_manager(start=self.start),'Ctrl+Shift+N')
        self.action(file,'Renommer l’onglet',self.rename_tab)
        self.action(file,'Fermer l’onglet',lambda:self.close_tab(self.tabs.currentIndex()),'Ctrl+Shift+W')
        self.action(file,'Fermer la fenêtre',self.window.close)
        edit=self.edit_menu=self.menu.addMenu('Édition')
        self.action(edit,'Copier',lambda:self.active_view().copy())
        self.action(edit,'Coller',lambda:self.active_view().paste_text())
        self.action(edit,'Rechercher',self.show_search,'Ctrl+Shift+F')
        edit.addSeparator();self.formats=edit.addMenu('Formats')
        self.format_actions={}
        for key,(label,count) in FORMATS.items():
            action=self.action(self.formats,label,lambda checked=False,f=key:self.set_format(f))
            action.setCheckable(True);self.format_actions[key]=action
        self.formats.addSeparator()
        self.action(self.formats,'Agrandir dans la zone disponible',self.toggle_fullscreen,'F11')
        text=self.text_menu=edit.addMenu('Texte')
        self.action(text,'Police, couleur et taille…',self.text_dialog)
        self.action(text,'Agrandir',lambda:self.zoom(1),'Ctrl++')
        self.action(text,'Réduire',lambda:self.zoom(-1),'Ctrl+-')
        self.action(text,'Taille normale',lambda:self.zoom(11-self.text['size']),'Ctrl+0')
        display=self.display_menu=self.menu.addMenu('Affichage')
        self.action(display,'Agrandir dans la zone disponible',self.toggle_fullscreen,'Alt+F11')
        self.action(display,'Onglet suivant',lambda:self.tabs.setCurrentIndex((self.tabs.currentIndex()+1)%self.tabs.count()),'Ctrl+PageDown')
        self.action(display,'Onglet précédent',lambda:self.tabs.setCurrentIndex((self.tabs.currentIndex()-1)%self.tabs.count()),'Ctrl+PageUp')
        help=self.help_menu=self.menu.addMenu('Aide')
        self.action(help,'Raccourcis',self.shortcuts)

    def new_tab(self):
        workspace=TerminalWorkspace(self,start=self.start,cwd=self.cwd)
        index=self.tabs.addTab(workspace,'Terminal '+str(self.tabs.count()+1))
        self.tabs.setCurrentIndex(index);self.update_status()
        return workspace

    def close_tab(self,index):
        workspace=self.tabs.widget(index)
        if workspace is None:return
        workspace.close_sessions();self.tabs.removeTab(index);workspace.deleteLater()
        if not self.tabs.count():self.window.close()

    def set_format(self,key):
        self.workspace().set_format(key)
        # Split layouts maximize into the workarea advertised by the window manager.
        if key!='single':self.window.showMaximized()
        else:self.window.showNormal()
        self.update_status()

    def open_formats(self):self.formats.exec(self.format_button.mapToGlobal(C.QPoint(0,0)))
    def toggle_fullscreen(self):
        self.window.showNormal() if (self.window.isMaximized() or self.window.isFullScreen()) else self.window.showMaximized()
    def update_status(self,*_):
        space=self.workspace()
        if not space:return
        visible=FORMATS[space.format][1]
        self.status.setText(f'{FORMATS[space.format][0].upper()}  /  {visible} visible(s) · {len(space.panes)} session(s)  /  UTF-8 · SHELL INTERACTIF')
        for key,action in getattr(self,'format_actions',{}).items():action.setChecked(key==space.format)

    def show_search(self):self.search_bar.show();self.search.setFocus()
    def find_next(self):
        view=self.active_view()
        if not view or not self.search.text():return
        if not view.find(self.search.text()):
            cursor=view.textCursor();cursor.movePosition(G.QTextCursor.Start);view.setTextCursor(cursor);view.find(self.search.text())

    def rename_tab(self):
        dialog=make_dialog('NOVA / ONGLET','Nom du terminal')
        field=W.QLineEdit(self.tabs.tabText(self.tabs.currentIndex()));dialog.layout().insertWidget(2,field)
        if dialog.exec()==W.QDialog.Accepted:self.tabs.setTabText(self.tabs.currentIndex(),field.text()[:60] or 'Terminal')

    def apply_text(self,view):
        view.setFont(G.QFont(self.text['font'],self.text['size']))
        view.foreground=self.text['foreground']
        color=G.QColor(self.text['background']);color.setAlpha(235)
        view.setStyleSheet('QTextEdit{background:%s;color:%s;border:1px solid #22657F;padding:8px;selection-background-color:#22586F;}'%(color.name(G.QColor.HexArgb),self.text['foreground']))
        view.sync_size();view.request_render()

    def save_text(self):
        target=data_dir()/'nova-terminal.json';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(self.text,indent=2)+'\n')
        for index in range(self.tabs.count()):
            for pane in self.tabs.widget(index).panes:self.apply_text(pane.view)

    def zoom(self,amount):
        self.text['size']=max(8,min(30,self.text['size']+amount));self.save_text()

    def text_dialog(self):
        dialog=make_dialog('NOVA / TEXTE','Personnaliser tous les terminaux')
        dialog.setStyleSheet(self.window.styleSheet())
        form=W.QFormLayout();font=W.QFontComboBox();font.setFontFilters(W.QFontComboBox.MonospacedFonts)
        font.setCurrentFont(G.QFont(self.text['font']));size=W.QSpinBox();size.setRange(8,30);size.setValue(self.text['size'])
        foreground=W.QLineEdit(self.text['foreground']);background=W.QLineEdit(self.text['background'])
        form.addRow('Police',font);form.addRow('Taille',size);form.addRow('Couleur du texte (hex)',foreground);form.addRow('Fond teinté (hex)',background)
        dialog.layout().insertLayout(2,form);dialog.resize(580,390)
        if dialog.exec()==W.QDialog.Accepted:
            if not all(G.QColor(v.text()).isValid() for v in (foreground,background)):
                make_dialog('NOVA / COULEUR','Utilise une couleur valide, par exemple #00CBF3.').exec();return
            self.text.update(font=font.currentFont().family(),size=size.value(),foreground=foreground.text(),background=background.text());self.save_text()

    def shortcuts(self):
        make_dialog('NOVA / RACCOURCIS','Ctrl+Maj+T : onglet · Ctrl+Maj+N : fenêtre\nCtrl+C : copier si sélection, sinon interrompre · Ctrl+V : coller\nCtrl+Maj+F : rechercher · F11 : agrandir / rétablir\nMaj+Page ↑↓ : historique · Ctrl+C : interrompre\nChanger de format conserve les sessions masquées.').exec()

    def eventFilter(self,watched,event):
        if event.type()==C.QEvent.Close:
            for index in range(self.tabs.count()):self.tabs.widget(index).close_sessions()
        return False


_managers=[]
def open_manager(*,start=True,cwd=None):
    manager=TerminalManager(start=start,cwd=cwd)
    _managers.append(manager)
    manager.window.destroyed.connect(lambda *_:_managers.remove(manager) if manager in _managers else None)
    manager.window.show()
    from healthbar.nova_components import mark_application_window
    mark_application_window(manager.window)
    return manager


def run():
    app=W.QApplication.instance() or W.QApplication(sys.argv[:1])
    open_manager()
    return app.exec()
