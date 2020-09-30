import tkinter as tk
import threading
from tkinter.filedialog import askopenfilename
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
import log
from _main import main, pathlib, reformat
from itertools import tee

"""
No Need Logger In GUI
Only Log In Process
"""


# logger = log.getLogger(__name__)
# logger.addHandler(log.queue_handler)

# GUI Option


class ConsoleUI:

    def __init__(self, frame, log_queue):
        """

        :param frame: Frame to pack Console UI
        :param log_queue: queue Instance to pull all log
        """
        self.frame = frame
        self.console = ScrolledText(frame, state='disabled', height=20, width=80)
        self.console.configure(font='TkFixedFont')

        # Enable Platform Highlight for Copying
        self.console.bind("<1>", lambda event: self.console.focus_set())
        self.console.tag_config('INFO', foreground='black')
        self.console.tag_config('DEBUG', foreground='gray')
        self.console.tag_config('WARNING', foreground='orange')
        self.console.tag_config('ERROR', foreground='red')
        self.console.tag_config('CRITICAL', foreground='red', underline=1)
        self.console.pack()
        self.log_queue = log_queue
        self.frame.after(10, self.pull_log_queue)

    def display(self, msg, level):
        self.console.config(state='normal')
        self.console.insert(tk.END, msg + '\n', level)
        self.console.configure(state='disabled')
        # Autoscroll to the bottom
        self.console.yview(tk.END)

    def pull_log_queue(self):
        # Check every 100ms if there is a new message in the log_queue to display
        while not self.log_queue.empty():
            msg = self.log_queue.get(block=False)
            self.display(msg[0], msg[1])
        self.frame.after(10, self.pull_log_queue)


class App:

    def __init__(self):
        self.window = tk.Tk()
        self.mapping_file_entry = None
        self.target_file_box = None
        self.excel_sheet_name = None
        self.button = None
        self.skip_rows = None
        # self.app_queue = queue.Queue()
        self.real_target_file = None
        self.output_path = None
        self.recursive = tk.BooleanVar()
        self.progress_bar = None
        self.reformat_frame = None

    def __main_window(self):
        self.window.title('Large Replace With Mapping Excel')

    def __button_build(self):
        # Starting Button Here
        button_frame = tk.Frame(self.window)
        button_frame.pack(side=tk.TOP)
        self.button = tk.Button(button_frame, text='Start Replace', command=self.__start)
        self.button.pack()

    def __search_file(self):
        desc_frame = tk.Frame(self.window)
        desc_frame.pack(side=tk.TOP)
        tk.Label(desc_frame, text='Choose Mapping File (Note ! If Excel is choose'
                                  ' Make Sure Sheet Name is Correct !)').pack()
        tk.Label(desc_frame, text='CAREFUL of skip rows ! Headers is Default Row 1 '
                                  'IF SKIP ROWS is 1 THEN Headers will be Row 2', foreground='red').pack()
        file_frame = tk.Frame(self.window)
        file_frame.pack(side=tk.TOP)
        self.mapping_file_entry = tk.Entry(file_frame, width=60)
        self.mapping_file_entry.pack(side=tk.LEFT)

        # Default
        self.mapping_file_entry.insert(tk.END, '< MAPPING FILE > Type or Browsing')

        def select_all(event=None):

            if event is None:
                return

            self.mapping_file_entry.focus()

            self.mapping_file_entry.selection_range(0, tk.END)

            return 'break'

        # self.mapping_file_entry.bind('<Control-a>', select_all)
        self.mapping_file_entry.bind('<Control-A>', select_all)

        # MacOS
        # self.mapping_file_entry.bind('<Command-a>', select_all)
        self.mapping_file_entry.bind('<Command-A>', select_all)

        # Make File Browsing
        file_browse = tk.Button(file_frame, text='Browse', font=40, command=self.__browsing_file)
        file_browse.pack(side=tk.LEFT)
        sheet = tk.Label(file_frame, text='Sheet Name')
        sheet.pack(side=tk.LEFT)

        self.excel_sheet_name = tk.Entry(file_frame, width=10)
        self.excel_sheet_name.insert(tk.END, 'Mapping')
        self.excel_sheet_name.pack(side=tk.LEFT)
        self.skip_rows = tk.Entry(file_frame, width=2)
        self.skip_rows.insert(tk.END, 1)
        tk.Label(file_frame, text='Skip Rows').pack(side=tk.LEFT)
        self.skip_rows.pack(side=tk.LEFT)

    def __browsing_file(self):
        filename = askopenfilename(filetypes=(('Excel target_file', '*.xlsx *.xls'),
                                              ('CSV Files', '*.csv')))
        self.mapping_file_entry.delete(0, tk.END)
        self.mapping_file_entry.insert(tk.END, filename)

    def __target_file(self):
        target_frame = tk.Frame(self.window)
        target_frame.pack()
        tk.Label(target_frame, text='Target To be Replaced , <FOLDER / SINGLE FILE / MULTIPLE FILES>').pack(side=tk.TOP)
        self.target_file_box = tk.Listbox(target_frame, width=80, height=10)
        self.target_file_box.pack(side=tk.TOP)

        button = tk.Button(target_frame, text='SELECT FILES', command=self.__browsing_multi_target)
        button.pack(side=tk.LEFT)
        button2 = tk.Button(target_frame, text='SELECT FOLDER', command=self.__browsing_folder)
        button2.pack(side=tk.RIGHT)
        tk.Checkbutton(target_frame, text='Recursive', variable=self.recursive).pack(side=tk.RIGHT)

    def __output_file(self):
        output_file_frame = tk.Frame(self.window)
        output_file_frame.pack()
        default_path = pathlib.Path.cwd()

        # Description
        tk.Label(output_file_frame, text='Setting Output Path for Modified Summary !').pack()
        tk.Label(output_file_frame, text='Default : {}'.format(default_path)).pack()

        self.output_path = tk.Entry(output_file_frame, width=60)
        self.output_path.pack(side=tk.TOP)
        self.output_path.insert(tk.END, default_path)

    def __reformat(self):
        p = threading.Thread(target=reformat, kwargs=dict(file_path=self.output_path.get()))

        self.reformat_frame.after(10, p.start())

    def __reformat_button(self):
        self.reformat_frame = tk.Frame(self.window)
        self.reformat_frame.pack()

        button = tk.Button(self.reformat_frame, text='Reformat Summary',
                           command=self.__reformat)

        button.pack()

    def __browsing_multi_target(self):
        target = tk.filedialog.askopenfilenames()
        self.target_file_box.delete(0, tk.END)
        for t in target:
            self.target_file_box.insert(tk.END, t)

        # Always Keep Target File as List
        self.real_target_file = [f for f in target]

    def __browsing_folder(self):
        target_folder = tk.filedialog.askdirectory()
        target_folder = pathlib.Path(target_folder)
        self.target_file_box.delete(0, tk.END)
        if self.recursive.get():
            target_file, target_file_bk = tee(target_folder.glob('**/*'))
            for t in target_file:
                if t.is_file():
                    self.target_file_box.insert(tk.END, t)
        else:
            target_file, target_file_bk = tee(target_folder.glob('*'))
            for t in target_file:
                if t.is_file():
                    self.target_file_box.insert(tk.END, t)

        # Always Keep Target File as List
        # Only Need File not Dir
        self.real_target_file = [f for f in target_file_bk if f.is_file()]

    def __start(self):
        # Starting Button Function

        # self.window.after(0, Main(self.mapping_file_entry.get(), jdbc=self.jdbc_entry.get(),
        #                           sheet=self.excel_sheet_name.get()).start())
        p = threading.Thread(target=main, kwargs=dict(mapping_file=self.mapping_file_entry.get(),
                                                      target=self.real_target_file,
                                                      sheetname=self.excel_sheet_name.get(),
                                                      output_path=self.output_path.get(),
                                                      skip_rows=self.skip_rows.get(),
                                                      button=self.button,
                                                      p_bar=self.progress_bar
                                                      ))
        self.window.after(10, p.start())

    def __wrap_log(self):
        log_frame = tk.Frame(self.window)
        log_frame.pack(side=tk.TOP)

        ConsoleUI(log_frame, log.queue_handler.log_queue)

    def __p_bar(self):
        pbar_frame = tk.Frame(self.window)
        pbar_frame.pack(side=tk.TOP)
        tk.Label(pbar_frame, text='Processing : ').pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(pbar_frame, orient='horizontal', length=400, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT)

    def build_window(self):
        # GUI Interface Build Control
        self.__main_window()
        self.__search_file()

        self.__target_file()
        self.__output_file()
        self.__wrap_log()

        self.__button_build()
        self.__p_bar()

        self.__reformat_button()

        return self.window


if __name__ == '__main__':
    window = App()
    window.build_window().mainloop()
    # pbar = {
    #     'maximum': 0,
    #     'value' : 0
    # }
    # main(mapping_file='/Users/fiammahsu/Workplace/netpro/FET/ONE_PLATFORM/KeyWordMapping.xlsx',
    #      sheetname='Mapping', skip_rows=1,
    #      target=['/Users/fiammahsu/Workplace/netpro/FET/ONE_PLATFORM/00000_TD 2800 修改/TD6750/\
    #      CIM_PROD EXPORT_CAMPAIGN SR174788_TRM_UDV_TRANSFER_QTY_INTERNAL_CALL STEP0101_TRANSFORM sqlExecutor.txt'],
    #      output_path='/Users/fiammahsu/Workplace/python/micro/MappingReplace',
    #      p_bar=pbar)
