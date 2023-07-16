import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import filedialog, ttk
from pandastable import Table
import os
import sys
from sshtunnel import SSHTunnelForwarder
import stat
class DatabaseGUI:
    def __init__(self, root):
        # Dynamically find the directory where the script (or packaged .exe) is running
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        self.ec2_address = '54.176.243.235'  # Replace with the public IP or DNS of your EC2 instance
        self.ec2_user = 'ubuntu'  # The username on your EC2 instance (usually 'ec2-user' for Amazon Linux instances)
        self.pem_file = os.path.join(application_path, 'demo-lambda.pem')
        self.pem_file = os.path.relpath(self.pem_file)
        # os.chmod(self.pem_file, stat.S_IRUSR)
        os.system(f"ssh -fNT -L 2347:localhost:5432 -i {self.pem_file} ubuntu@54.176.243.235")
        # self.server = SSHTunnelForwarder(
        #     self.ec2_address,
        #     ssh_username=self.ec2_user,
        #     ssh_pkey=self.pem_file,
        #     remote_bind_address=('localhost', 5432)
        # )
        # self.server.start()
        
        self.root = root
        self.forest_path=os.path.join(application_path, 'forest-light.tcl')
        self.forest_path = os.path.relpath(self.forest_path)
        self.root.tk.call('source', self.forest_path)

        # Set the theme with the theme_use method
        ttk.Style(self.root).theme_use('forest-light')
        self.df_dict={}
        self.df_dict['test']=self.get_test_ids()
        self.test_ids=self.df_dict['test']['test_id'].to_list()
        self.root.title("Lab Data Portal")
        self.root.option_add("*tearOff", False) # This is always a good idea

        # Make the app responsive
        self.root.columnconfigure(index=0, weight=1)
        self.root.columnconfigure(index=1, weight=1)
        self.root.columnconfigure(index=2, weight=1)
        self.root.rowconfigure(index=0, weight=1)
        self.root.rowconfigure(index=1, weight=1)
        self.root.rowconfigure(index=2, weight=1)
        
        # Create a Frame for the Data Selection buttons
        data_frame = ttk.LabelFrame(self.root, text="Data Selection", padding=(20, 10))
        data_frame.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="nw",rowspan=4)
        # test_id menu
        self.test_id_var = tk.StringVar(self.root)
        test_id_menu=['','select a test id']+self.test_ids
        self.test_id_var.set(value=test_id_menu[1])  # default value to be the first id
        self.test_id_menu = ttk.OptionMenu(data_frame, self.test_id_var,*test_id_menu)
        self.test_id_menu.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

        # table selection menu
        self.table_var = tk.StringVar(self.root)
        self.tables=['','select data to preview','record','cycle','test']
        self.table_var.set('select data to preview')  # default value to be the record
        self.table_menu = ttk.OptionMenu(data_frame, self.table_var,*self.tables)
        self.table_menu.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        
        self.preview_button = ttk.Button(data_frame, text="Preview Data", command=lambda: self.get_data())
        self.preview_button.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        self.download_button = ttk.Button(data_frame, text="Download CSV", command=lambda: self.download_csv())
        self.download_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        self.columns=[]
        self.fig, self.ax = plt.subplots()
        self.dict_unit={'current':'Current(A)','v':'Voltage(V)','capacity':'Capacity(Ah)','energy':'Energy(Wh)','ch_capacity':'Charge Capacity(Ah)','dis_capacity':'Discharge Capacity(Ah)','ch_energy':'Charge Energy(Wh)','dis_energy':'Discharge Energy(Wh)'}
        self.table_frame = ttk.Frame(root)
        self.table_frame.grid(row=0, column=1, sticky='nsew')
        
        self.canvas = tk.Canvas(root, width=500, height=500)
        self.canvas.grid(row=1, column=1, sticky='nsew')
    def query_db(self,query):
    # Connect to your postgres DB
        conn = psycopg2.connect(database="tsdb", user="postgres", password="postgres", host="localhost", port=2347)
        # Open a cursor to perform database operations
        cur = conn.cursor()

        # execute query
        cur.execute(query)  

        # fetch all rows
        rows = cur.fetchall()

        # get column names
        colnames = [desc[0] for desc in cur.description]

        # close cursor and connection
        cur.close()
        conn.close()

        # create pandas DataFrame
        df = pd.DataFrame(rows, columns=colnames)
        
        return df
    def get_test_ids(self):
        query = "SELECT * FROM test"  
        df = self.query_db(query)
        return df

    def get_data(self):
        type=self.table_var.get()
        if type=='test':
            self.display_file(self.df_dict[type])
        # query data based on type and save to df_dict
        else:
            test_id = self.test_id_var.get()
            # if type=='record':
            query = '''
            SELECT {}.*,test.test_id
            FROM {} 
            INNER JOIN test 
            on {}.test_name=test.test_name
            WHERE test.test_id={};
            '''.format(type,type,type,test_id)  # Replace 'your_table' with your actual table name WHERE test.test_id={} AND v>{} AND v<{};
            self.df_dict[type] = self.query_db(query)
            self.display_file(self.df_dict[type])
        self.columns = [''] + list(self.df_dict[type].columns)

    def download_csv(self):
        type=self.table_var.get()
        filename = filedialog.asksaveasfilename(defaultextension='.csv')
        self.df_dict[type].to_csv(filename, index=False)
        
    def display_file(self, df):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        table = Table(self.table_frame, dataframe=df, showtoolbar=True,showstatusbar=True)
        table.show()

        # Create a Frame for input widgets
        self.widgets_frame = ttk.LabelFrame(self.root, text="Plot Options", padding=(20, 10))
        self.widgets_frame.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="nw", rowspan=4)
        # self.widgets_frame.columnconfigure(index=0, weight=1)
        
        columns = [''] + list(df.columns)
        self.x_var = tk.StringVar(self.widgets_frame)
        self.y1_var = tk.StringVar(self.widgets_frame)
        self.y2_var = tk.StringVar(self.widgets_frame)

        x_dropdown = ttk.OptionMenu(self.widgets_frame, self.x_var,"select x", *columns)
        y1_dropdown = ttk.OptionMenu(self.widgets_frame, self.y1_var, "select y1",*columns)
        y2_dropdown = ttk.OptionMenu(self.widgets_frame, self.y2_var, "select y2 (optional)",*columns)
        
        x_dropdown.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
        y1_dropdown.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        y2_dropdown.grid(row=2, column=0, padx=5, pady=10, sticky="ew")

        # Adding plot button after displaying the file
        self.plot_button = ttk.Button(self.widgets_frame, text='Plot Data', command=lambda:self.plot_data(df))
        self.plot_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")

        # Adding download plot button after displaying the file
        self.download_button = ttk.Button(self.widgets_frame, text='Download Plot', command=self.download_plot)
        self.download_button.grid(row=4, column=0, padx=5, pady=10, sticky="ew")

    def plot_data(self,df):

        x = self.x_var.get()
        y1 = self.y1_var.get()
        y2 = self.y2_var.get()
        type=self.table_var.get()
        if x and y1:  # make sure x and y1 are selected

            self.ax.cla()  # clear previous plot
            if type=='record':
                x_unit,y1_unit,y2_unit=x,y1,y2
                for i in range(1,df['period'].max()):
                    self.ax.plot(df[df['period']==i][x], df[df['period']==i][y1],'.',label=f"cycle {i}")
                    
                    if x in self.dict_unit:
                        x_unit=self.dict_unit[x]
                    plt.xlabel(f'{x_unit}')   
                    if y1 in self.dict_unit:
                        y1_unit=self.dict_unit[y1]             
                    plt.ylabel(f'{y1_unit}')
                    
                    plt.savefig(f'./images/{x}_{y1}_test_{self.test_id_var.get()}.png')
                if y2!="select y2 (optional)" or "":
                    self.ax.plot(df[x], df[y2], '.',label=y2)
                    if y2 in self.dict_unit:
                        y2_unit=self.dict_unit[y1]   
                    
                    plt.ylabel(f'{y2_unit}')
            canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            canvas.draw()
            canvas.get_tk_widget().grid(row=1, column=1,padx=5, pady=10,sticky="nsew")

    def download_plot(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[("PNG Files","*.png"), ("All Files","*.*")])
        if file_path:
            self.fig.savefig(file_path)
    # def __del__(self):
    #     # Close the SSH tunnel when the object is deleted
    #     self.server.stop()        
    
if __name__ == "__main__":
    # if port 2345 is not forwarding to 5432, establish a ssh forwarding
    # os.system(f"ssh -fNT -L 2345:localhost:5432 -i demo-lambda.pem ubuntu@54.176.243.235")
    # if getattr(sys, 'frozen', False):
    #     application_path = sys._MEIPASS
    # else:
    #     application_path = os.path.dirname(os.path.abspath(__file__))
    # print(application_path)
    # ec2_address = '54.176.243.235'  # Replace with the public IP or DNS of your EC2 instance
    # ec2_user = 'ubuntu'  # The username on your EC2 instance (usually 'ec2-user' for Amazon Linux instances)
    # pathlib.Path().resolve()
    # pem_file = os.path.join(application_path, 'demo-lambda.pem')
    # pem_file = os.path.relpath(pem_file)
    # print(pem_file)
    # os.chmod(pem_file, stat.S_IRUSR)
    # os.system(f"chmod 400 ./demo-lambda.pem")
    # os.system('ssh -fNT -L 2345:localhost:5432 -i demo-lambda.pem ubuntu@54.176.243.235')
    root = tk.Tk()
    gui = DatabaseGUI(root)
    root.mainloop()
