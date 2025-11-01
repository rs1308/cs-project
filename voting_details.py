import customtkinter
from tkinter import filedialog
import time
import mysql.connector
from mysql.connector import Error
import sys

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


def create_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="hello",
            password="your_password",
            database="voting_app"
        )
        if conn.is_connected():
            print("✅ Connected to MySQL Database")
        return conn
    except Error as e:
        print("❌ MySQL connection failed:", e)
        return None



class MainApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Candidate Entry App")
        self.geometry("900x560")
        self.resizable(True, True)

        
        self.conn = create_connection()
        if self.conn is None:
            raise SystemExit("Database connection failed.")

        
        self.container = customtkinter.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        
        self.login_page = LoginPage(self.container, on_login=self.show_page_one)
        self.page_one = PageOne(self.container, on_next=self.show_page_two)
        self.page_two = PageTwo(self.container, on_back=self.show_page_one, db_conn=self.conn)

        
        for page in (self.login_page, self.page_one, self.page_two):
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        
        self.show_page(self.login_page)

    def show_page(self, page):
        page.tkraise()

    def show_page_one(self, username=None):
        
        if username != "":
            self.username = username
            self.page_two.username = username

            cursor = self.conn.cursor()
            table_name = f"{self.username}_candidates"


            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    class VARCHAR(20),
                    section VARCHAR(20),
                    imagepath VARCHAR(255)
                )
            """)
            self.conn.commit()
            cursor.close()

        self.show_page(self.page_one)

    def show_page_two(self, count=None):
        if count is not None:
            self.page_two.build_candidates(count)
        self.show_page(self.page_two)



class LoginPage(customtkinter.CTkFrame):
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.on_login = on_login

        title = customtkinter.CTkLabel(self, text="Login", font=("Arial", 24))
        title.pack(pady=20)

        self.username_entry = customtkinter.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = customtkinter.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        self.error_label = customtkinter.CTkLabel(self, text="", text_color="red")
        self.error_label.pack()

        login_button = customtkinter.CTkButton(self, text="Login", command=self.login)
        login_button.pack(pady=20)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username == "admin" and password == "password":
            self.error_label.configure(text="Login Successful", text_color="green")
            self.update()
            time.sleep(1.5)
            self.on_login(username)
        else:
            self.error_label.configure(text="Invalid username or password")


class PageOne(customtkinter.CTkFrame):
    def __init__(self, parent, on_next):
        super().__init__(parent)
        self.on_next = on_next

        label = customtkinter.CTkLabel(self, text="Enter number of candidates")
        label.pack(pady=(50, 10))

        self.entry = customtkinter.CTkEntry(self, placeholder_text="e.g. 3")
        self.entry.pack(pady=5)

        self.error_label = customtkinter.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

        next_btn = customtkinter.CTkButton(self, text="Next", command=self.go_next)
        next_btn.pack(pady=20)

    def go_next(self):
        try:
            n = int(self.entry.get())
            if n <= 0:
                raise ValueError
            self.error_label.configure(text="")
            self.on_next(n)
        except ValueError:
            self.error_label.configure(text="Please enter a valid positive number")


# ---------- Page Two ----------
class PageTwo(customtkinter.CTkFrame):
    def __init__(self, parent, on_back, db_conn):
        super().__init__(parent)
        self.on_back = on_back
        self.conn = db_conn
        self.username = None
        self.candidate_entries = []

        top = customtkinter.CTkFrame(self)
        top.pack(fill="x", padx=12, pady=12)

        customtkinter.CTkLabel(top, text="Candidate Details").pack(side="left")
        customtkinter.CTkButton(top, text="Back", command=self.go_back).pack(side="right")

        self.body = customtkinter.CTkScrollableFrame(self, label_text="Candidates")
        self.body.pack(fill="both", expand=True, padx=12, pady=12)

        footer = customtkinter.CTkFrame(self)
        footer.pack(fill="x", padx=12, pady=(0, 12))
        customtkinter.CTkButton(footer, text="Save All", command=self.save_all).pack(side="right")

    def build_candidates(self, count):
        for widget in self.body.winfo_children():
            widget.destroy()
        self.candidate_entries.clear()

        for i in range(count):
            frame = customtkinter.CTkFrame(self.body)
            frame.pack(fill="x", pady=8, padx=8)

            customtkinter.CTkLabel(frame, text=f"Candidate {i+1}").pack(anchor="w")

            name = customtkinter.CTkEntry(frame, placeholder_text="Name")
            name.pack(fill="x", pady=2)
            cls = customtkinter.CTkEntry(frame, placeholder_text="Class")
            cls.pack(fill="x", pady=2)
            sec = customtkinter.CTkEntry(frame, placeholder_text="Section")
            sec.pack(fill="x", pady=2)

            photo_row = customtkinter.CTkFrame(frame)
            photo_row.pack(fill="x", pady=2)
            photo_entry = customtkinter.CTkEntry(photo_row, placeholder_text="Photo path")
            photo_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            browse_btn = customtkinter.CTkButton(photo_row, text="Browse",
                                                 command=lambda e=photo_entry: self.select_photo(e))
            browse_btn.pack(side="right")

            self.candidate_entries.append((name, cls, sec, photo_entry))

    def select_photo(self, entry):
        file_path = filedialog.askopenfilename(
            title="Select Photo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )
        if file_path:
            entry.delete(0, "end")
            entry.insert(0, file_path)

    def go_back(self):
        self.on_back()

    def save_all(self):
        if self.username == "":
            print("⚠️ No username found. Cannot save.")
            return

        table_name = f"{self.username}_candidates"
        cursor = self.conn.cursor()

        for name, cls, sec, photo in self.candidate_entries:
            n, c, s, p = name.get(), cls.get(), sec.get(), photo.get()
            if n and c and s and p:
                cursor.execute(
                    f"INSERT INTO {table_name} (name, class, section, imagepath) VALUES (%s, %s, %s, %s)",
                    (n, c, s, p)
                )

        self.conn.commit()
        cursor.close()
        customtkinter.CTkLabel(self,text =f"✅ Data saved successfully to table '{table_name}'!").pack(pady=10)
        self.after(500, lambda: (self.quit(), sys.exit()))


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()

