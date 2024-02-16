# from "Python Coobook 2nd Edition", section 11.9, page 439.
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

#import os
from os import path
import time
import threading
import random
import queue
from typing import Tuple, Any
# local files
import law_review_source_pull


class GuiPart(object):
    def __init__(self, root, queue, start_command, end_command) -> None:
        self.root = root
        self.queue = queue
        self.start_command = start_command

        # login field defaults
        self.username: str = '' # for reuse based on multiple documents before closing program
        self.password: str = ''
        self.show_text_fields = tk.BooleanVar()
        self.show_text_fields.set(False)

        self.root.title("Source Pull Generator")
        self.menu()

    def menu(self) -> None:
        self._show_new_screen()

        menu_frame = tk.Frame(self.root)
        self._create_file_upload_group(0, "Author's Word Document", menu_frame)
        
        # westlaw checkbox 
        self.checkbox = tk.Checkbutton(menu_frame, text="Get Westlaw Links", variable=self.show_text_fields, command=self.toggle_text_fields)
        self.checkbox.grid(row=4, column=0, columnspan=4, pady=(20,0), padx=5, sticky=tk.W)

        # login info
        self.username_label = tk.Label(menu_frame, text="Westlaw Username:")
        self.username_text_entry = tk.Entry(menu_frame)
        self.username_text_entry.insert(0, self.username)
        self.password_label = tk.Label(menu_frame, text="Westlaw Password:")
        self.password_text_entry = tk.Entry(menu_frame)
        self.password_text_entry.insert(0, self.password)

        # submit button to run file processing
        self.finish_button = tk.Button(menu_frame, text="Generate Excel", command=self.finish, state=tk.DISABLED)
        self.finish_button.grid(row=9, column=0, columnspan=4, pady=(30,0))

        if self.show_text_fields.get():
            self.toggle_text_fields()

    def loading_screen(self, total_items: int) -> None:
        self._show_new_screen()

        self.loading_frame = tk.Frame(self.root)
        self.loading_frame.pack(padx=100, pady=80)
        # https://pythonassets.com/posts/progress-bar-in-tk-tkinter/
        self.progressbar = ttk.Progressbar(maximum=total_items) if total_items else ttk.Progressbar()
        self.progressbar.place(x=30, y=60, width=200)
        self.loading_label = tk.Label(self.loading_frame, text="Loading...")
        self.loading_label.grid(row=8, column=0, columnspan=4, pady=10, padx=10, sticky=tk.W)
        self.loading_label.pack()

    def _create_file_upload_group(self, row, label_text, group_frame) -> None:
        # Add some space between each group
        group_frame.grid(row=row, column=0, columnspan=4, pady=5, padx=5, sticky=tk.N)
        group_frame.bind("<Button-1>", lambda event, r=row: self.upload_file(r))

        label = tk.Label(group_frame, text=label_text, anchor="w")
        label.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        #
        #image_path = "path_to_your_image.png"  # Replace with the path to your image
        # https://pyinstaller.org/en/stable/runtime-information.html
        image_path = path.abspath(path.join(path.dirname(__file__), 'upload_icon.png'))

        img = Image.open(image_path)
        img = img.resize((43, 50), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(img)

        image_label = tk.Label(group_frame, image=img)
        image_label.image = img
        image_label.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        filename_entry = tk.Entry(group_frame, state='disabled', width=30)
        filename_entry.grid(row=2, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        upload_button = tk.Button(group_frame, text="Upload", command=lambda r=row: self.upload_file(row, filename_entry))
        upload_button.grid(row=3, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)
        group_frame.focus_set()

    # https://stackoverflow.com/questions/69079608/how-to-make-multiple-pages-in-tkinter-gui-app
    def _show_new_screen(self,) -> None:
        for item in self.root.winfo_children():
            item.destroy()

    def upload_file(self, file_upload_num, filename_entry) -> None:
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            filename_entry.config(state='normal')
            filename_entry.delete(0, tk.END)
            filename_entry.insert(0, self.file_path)
            filename_entry.config(state='disabled')

            if file_upload_num == 0:
                self.finish_button.config(state=tk.NORMAL)
    
    def toggle_text_fields(self) -> None:
        if self.show_text_fields.get():
            self.username_label.grid(row=6, column=0, pady=5, padx=5, sticky=tk.W)
            self.username_text_entry.grid(row=6, column=1, pady=5, padx=5, sticky=tk.W)
            self.password_label.grid(row=7, column=0, pady=5, padx=5, sticky=tk.W)
            self.password_text_entry.grid(row=7, column=1, pady=5, padx=5, sticky=tk.W)
        else:
            self.username_label.grid_remove()
            self.username_text_entry.grid_remove()
            self.password_label.grid_remove()
            self.password_text_entry.grid_remove()

    def finish(self) -> None:
        # get values 
        if self.show_text_fields.get():
            self.username = self.username_text_entry.get()
            self.password = self.password_text_entry.get()
            self.show_text_fields.set(True)
        else: 
            self.username = ''
            self.password = ''

        if self.show_text_fields.get() and (self.username.strip() == '' or self.password.strip() == ''):
            tk.messagebox.showwarning("Warning", "Please fill in your Westlaw login details.")
        else:
            self.total = None
            if path.isfile(self.file_path):
                self.total: int = len(law_review_source_pull.get_footnotes(self.file_path))
            
            self.loading_screen(self.total)
            self.root.update_idletasks()
            try:
                self.start_command((self.file_path, self.username, self.password, self.queue))
            except Exception as e:
                self.error(e)

    def success(self) -> None:
        tk.messagebox.showinfo("Success", "Output has been downloaded to your downloads folder")
        self.menu()

    def error(self, message: str) -> None:
        tk.messagebox.showerror("Error", message)
        self.menu()


    def processIncoming(self):
        """ Handle all messages currently in the queue, if any. """
        while self.queue.qsize():
            try:
                msg = self.queue.get_nowait()
                # Check contents of message and do whatever is needed. As a
                # simple example, let's print it (in real life, you would
                # suitably update the GUI's display in a richer fashion).
                print(msg)
                self.progressbar.step(msg)
            except queue.Empty:
                # just on general principles, although we don't expect this
                # branch to be taken in this case, ignore this exception!
                pass
            except tk.TclError as e: # when self.progressbar is thrown an error from inside the thread (most likely westlaw_links)
                self.error(e)
            
            # https://stackoverflow.com/questions/55760066/stop-a-progress-bar-at-max-value-tkinter
            if self.progressbar['value'] == (self.total - 1):
                # stop queue -- move to next page
                print('moving to finish page')
                print(self.queue.qsize())
                self.success()


# https://stackoverflow.com/questions/53696888/freezing-hanging-tkinter-gui-in-waiting-for-the-thread-to-complete
class ThreadedClient(object):
    """
    Launch the main part of the GUI and the worker thread. periodic_call()
    and end_application() could reside in the GUI part, but putting them
    here means that you have all the thread controls in a single place.
    """
    def __init__(self, root) -> None:
        """
        Start the GUI and the asynchronous threads.  We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well.  We spawn a new thread for the worker (I/O).
        """
        self.root = root
        self.queue = queue.Queue()
        self.gui = GuiPart(root, self.queue, self.start_application, self.end_application)

    def periodic_call(self) -> None:
        """ Check every 200 ms if there is something new in the queue. """
        self.root.after(200, self.periodic_call)
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system.  You may want to do
            # some cleanup before actually shutting it down.
            self.root.destroy()

    def worker_thread1(self, file_path: str, username: str, password: str, queue) -> None:
        """
        This is where we handle the asynchronous I/O.  For example, it may be
        a 'select()'.  One important thing to remember is that the thread has
        to yield control pretty regularly, be it by select or otherwise.
        """
        law_review_source_pull.main(file_path, username, password, queue)
        #self.end_application()

    def start_application(self, args: Tuple[str, str, str, Any]) -> None:
        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = True
        self.thread1 = threading.Thread(target=self.worker_thread1, args=args)
        self.thread1.start()

        # Start the periodic call in the GUI to check the queue
        self.periodic_call()

        try:
            self.thread1.join()
        except Exception as e:
            raise Exception(e)

    def end_application(self):
        self.running = False  # Stops worker_thread1 (invoked by "Done" button).

if __name__ == '__main__':
    root = tk.Tk()
    client = ThreadedClient(root)
    root.mainloop()
 