import os
import subprocess
import shutil

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pijp import util
from pijp_dti import mosaic

ROW_SIZE = 5
COLUMN_SIZE = 5


class Application(tk.Frame):

    def __init__(self, code, b0, auto_mask, final_mask, master):

        tk.Frame.__init__(self, master)
        self.code = code
        self.b0 = b0
        self.auto_mask = auto_mask
        self.final_mask = final_mask

        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        master.configure(bg='black')
        master.protocol("WM_DELETE_WINDOW", self.wm_quit)
        center_window(master, 0.75)

        # Base Frame Settings
        self.config(bg='black')
        self.result = None
        self.comment = ''
        self.code = ''
        self.x = None
        self.y = None
        self.scale = 1
        self.canvas = None

        self.button_quit = tk.Button(master=self.master)
        self.button_save_quit = tk.Button(master=self.master)
        self.button_pass = tk.Button(master=self.master)
        self.button_edit = tk.Button(master=self.master)
        self.button_fail = tk.Button(master=self.master)
        self.entry_comment = tk.Entry(master=self.master)
        self.label_comment = tk.Label(master=self.master)
        self.label_top = tk.Label(master=self.master)
        self.menubar = tk.Menu(master=self.master)
        self.file_menu = tk.Menu(self.menubar)
        self.edit_menu = tk.Menu(self.menubar)
        self.submit_submenu = tk.Menu(self.file_menu)

    def create_widgets(self):

        fg = 'black'
        bg = 'white'
        relief = 'flat'
        v = tk.StringVar()

        # Configuration
        self.master.config(menu=self.menubar)
        self.button_quit.config(text='Exit', bg=bg, fg=fg, relief=relief, command=self._quit)
        self.button_save_quit.config(text='Save and Exit', bg=bg, fg=fg, relief=relief, command=self.submit_and_quit)
        self.button_pass.config(text='Pass', command=self._pass, bg=bg, fg=fg, relief=relief)
        self.button_fail.config(text='Fail', command=self._fail, bg=bg, fg=fg, relief=relief)
        self.button_edit.config(text='Edit', command=self.edit, bg=bg, fg=fg, relief=relief)
        self.entry_comment.config(textvariable=v)
        self.label_comment.config(text="Comment: ", bg='black', fg='white')
        self.label_top.config(text=self.code, bg='black', fg='white', font=16)

        # Griding
        self.grid(rowspan=ROW_SIZE, columnspan=COLUMN_SIZE, stick="news", padx=5, pady=5)
        self.button_pass.grid(column=2, row=4, stick='news', padx=5, pady=2)
        self.button_fail.grid(column=4, row=4, sticky='news', padx=5, pady=2)
        self.button_edit.grid(column=3, row=4, sticky='news', padx=5, pady=2)
        self.entry_comment.grid(column=2, row=3, columnspan=3, sticky='news', padx=5, pady=2)
        self.label_comment.grid(column=1, row=3, sticky='e')
        self.label_top.grid(column=2, row=1, sticky='n', columnspan=4, rowspan=1)

        # Event Bindings
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)
        self.label_top.bind("<ButtonPress-1>", self.start_move)
        self.label_top.bind("<ButtonRelease-1>", self.stop_move)
        self.label_top.bind("<B1-Motion>", self.on_motion)

        # Menu Bar

        self.menubar.add_cascade(label="File", menu=self.file_menu, underline=0)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu, underline=0)
        self.file_menu.config(tearoff=0)
        self.file_menu.add_command(label="Open in FSLView", command=self.open_mask_editor)
        self.file_menu.add_cascade(label='Submit', menu=self.submit_submenu, underline=0, state="disabled")
        self.file_menu.add_command(label="Exit", command=self._quit, underline=1)

        self.submit_submenu.config(tearoff=0)
        self.submit_submenu.add_command(label="Submit and Quit", command=self.submit_and_quit, underline=0)
        self.submit_submenu.add_command(label="Quit without submitting", command=self.quit_without_submitting)

        self.edit_menu.config(tearoff=0)
        self.edit_menu.add_command(label="Reset Mask", command=self.reset_mask)
        self.edit_menu.add_command(label="Clear Result", command=self.clear_result)

        # Miscellaneous Settings
        self.winfo_toplevel().title("QC Tool")
        self.entry_comment.focus_set()
        ttk.Sizegrip(self.master).grid(column=999, row=999, sticky='se')

        for i in range(0, COLUMN_SIZE):
            self.columnconfigure(i, weight=1)
        for j in range(0, ROW_SIZE):
            self.rowconfigure(j, weight=1)

    def create_figure(self, fig, col=0, row=0, span=COLUMN_SIZE):
        canvas = FigureCanvasTkAgg(fig, self.master)
        canvas.show()
        canvas.get_tk_widget().grid(column=col, row=row, columnspan=span, sticky='news', padx=25, pady=25)
        self.canvas = canvas._tkcanvas
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)

    def _quit(self):
        if self.result:
            if messagebox.askokcancel("QC Tool", "Quit without saving?", parent=self.master):
                self.result = "cancelled"
                self.comment = "Exited without saving"
                self.master.quit()
        else:
            self.master.quit()
            self.comment = "Exited without saving"

    def submit_and_quit(self):
        if self.result is None:
            messagebox.showerror("Error", "Result not selected!", parent=self.master)
        else:
            if messagebox.askokcancel("QC Tool", "Are you sure you want to submit?", parent=self.master):
                self.master.quit()

    def quit_without_submitting(self):
        if self.result == 'edit':
            if messagebox.askokcancel("QC Tool", "Are you sure you want to quit?", parent=self.master):
                self.result = 'unfinished'
                if self.comment is None:
                    self.comment = "editing in progress"
                self.master.quit()
        else:
            messagebox.showinfo("QC Tool", "Edit result not selected. Use Exit instead.")

    def wm_quit(self):
        if self.result:
            if messagebox.askyesno("QC Tool", "Save result before exiting?", parent=self.master):
                self.master.quit()
            else:
                self.result = "cancelled"
                self.comment = "Exited without saving"
                self.master.quit()
        else:
            self.result = "cancelled"
            self.comment = "Exited without saving"
            self.master.quit()

    def _pass(self):
        self.button_pass.config(bg='pale green', fg='dark green')
        self.button_fail.config(bg='white', fg='black')
        self.button_edit.config(bg='white', fg='black')
        self.result = 'pass'
        self.file_menu.entryconfig("Submit", state='normal')

    def _fail(self):
        self.button_fail.config(bg='indian red', fg='black')
        self.button_pass.config(bg='white', fg='black')
        self.button_edit.config(bg='white', fg='black')
        self.result = 'fail'
        self.file_menu.entryconfig("Submit", state='normal')

    def edit(self):
        self.button_edit.config(bg='yellow', fg='black')
        self.button_fail.config(bg='white', fg='black')
        self.button_pass.config(bg='white', fg='black')
        self.result = 'edit'
        self.open_mask_editor()
        self.file_menu.entryconfig("Submit", state='normal')

    def clear_result(self):
        self.button_edit.config(bg='white', fg='black')
        self.button_pass.config(bg='white', fg='black')
        self.button_fail.config(bg='white', fg='black')
        self.result = None

    def reset_mask(self):
        if messagebox.askyesno("WARNING", "Are you sure you want to reset the mask? All edits will be lost.",
                               icon="warning", parent=self.master):
            reset_mask(self.auto_mask, self.final_mask)
            self.refresh_fig()

    def open_mask_editor(self):
        open_mask_editor(self.b0, self.final_mask)

    def refresh_fig(self):
        newfig = draw_figure(self.b0, self.final_mask)
        self.canvas.destroy()
        self.create_figure(newfig)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_motion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry("+%s+%s" % (x, y))


def run_qc_interface(code, b0, auto_mask, final_mask):

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.minsize(width=640, height=480)
    app = Application(code, b0, auto_mask, final_mask, root)
    app.edit_cmd = open_mask_editor
    app.reset_mask_cmd = reset_mask
    app.draw_figure_cmd = draw_figure
    app.create_widgets()
    app.create_figure(draw_figure(b0, final_mask))
    app.mainloop()
    result = app.result
    comment = app.comment
    root.destroy()
    return result, comment


def center_window(master, scale):
    master.update_idletasks()
    w = master.winfo_screenwidth()
    h = master.winfo_screenheight()
    x = int(w*scale)
    y = int(h*scale)
    x_off = int(w/2 - x/2)
    y_off = int(h/2 - y/2)
    master.geometry("{:d}x{:d}{:+d}{:+d}".format(x, y, x_off, y_off))


def get_mask_editor():
    mask_editor = util.configuration['fslview']
    if not os.path.exists(mask_editor):
        raise Exception("fslview not found")
    return mask_editor


def open_mask_editor(b0, mask):
        mask_editor = get_mask_editor()
        cmd = "{mask_editor} -m single {img} {overlay} -t 0.5 -l Red".format(mask_editor=mask_editor, img=b0,
                                                                             overlay=mask)
        args = cmd.split()
        subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def reset_mask(auto_mask, final_mask):
    shutil.copyfile(auto_mask, final_mask)


def draw_figure(b0, mask):
    return mosaic.get_mask_mosaic(b0, mask)
