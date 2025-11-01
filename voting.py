import customtkinter
import tkinter as tk
from tkinter import messagebox
import mysql.connector
import sys



customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


class VotingApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Voting System")
        self.geometry("900x600")

        self.container = customtkinter.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.login_page = LoginPage(self.container, on_login=self.show_voting_page)
        self.voting_page = VotingPage(self.container)

        pages = (self.login_page, self.voting_page)

        for page in pages:
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page(self.login_page)

    def show_page(self, page):
        page.tkraise()

    def show_voting_page(self, username):
        self.voting_page.load_candidates(username)
        self.show_page(self.voting_page)


class LoginPage(customtkinter.CTkFrame):
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.on_login = on_login

        customtkinter.CTkLabel(self, text="Admin Login", font=("Arial", 24)).pack(pady=20)

        self.username_entry = customtkinter.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = customtkinter.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        customtkinter.CTkButton(self, text="Login", command=self.login).pack(pady=20)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        self.error_label = customtkinter.CTkLabel(self, text="", font=("Arial", 14))
        self.error_label.pack(pady=5)


        if username == "admin" and password == "password":
            self.error_label.configure(text="Login Successful", text_color="green")
            self.update()
            self.after(1000, lambda: self.on_login(username))
        else:
            self.error_label.configure(text="Invalid username or password")


class VotingPage(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.username = None
        self.candidates = []
        self.conn = None
        self.cursor = None
        self.current_usn = None

        customtkinter.CTkLabel(self, text="Voting Page", font=("Arial", 24)).pack(pady=20)

        self.usn_entry = customtkinter.CTkEntry(self, placeholder_text="Enter USN to vote")
        self.usn_entry.pack(pady=10)

        self.submit_usn_btn = customtkinter.CTkButton(self, text="Submit USN", command=self.verify_usn)
        self.submit_usn_btn.pack(pady=10)

        self.candidate_frame = customtkinter.CTkScrollableFrame(self, label_text="Candidates")
        self.candidate_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        self.phtot_refs=[]

    def load_candidates(self, username):
        self.username = username

        self.conn = mysql.connector.connect(
            host="localhost",
            user="hello",
            password="your_password",
            database="voting_app"
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"SELECT name, class, section, imagepath FROM {username}_candidates")
            rows = self.cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch candidates: {e}")
            return

        for widget in self.candidate_frame.winfo_children():
            widget.destroy()
        self.candidates = []

        for row in rows:
            name, cls, sec, img_path = row
            frame = customtkinter.CTkFrame(self.candidate_frame)
            frame.pack(fill="x", pady=5, padx=10)

            try:
                tk_img = tk.PhotoImage(file=img_path)
                w, h = tk_img.width(), tk_img.height()

                target_w, target_h = 60, 60

                if w > target_w or h > target_h:
                    sx = max(1, (w + target_w - 1) // target_w)
                    sy = max(1, (h + target_h - 1) // target_h)
                    tk_img = tk_img.subsample(sx, sy)
                else:
                    zx = max(1, target_w // max(1, w))
                    zy = max(1, target_h // max(1, h))
                    if zx > 1 or zy > 1:
                        tk_img = tk_img.zoom(zx, zy)

                img_label = customtkinter.CTkLabel(frame, image=tk_img, text="")
                img_label.image = tk_img
                self.phtot_refs.append(tk_img)
                img_label.pack(side="left", padx=10)

            except Exception as e:
                print(e)

            customtkinter.CTkLabel(frame, text=f"{name} ({cls}-{sec})").pack(side="left", padx=10)
            vote_btn = customtkinter.CTkButton(frame, text="Vote", command=lambda n=name: self.cast_vote(n))
            vote_btn.pack(side="right", padx=10)
            vote_btn.configure(state="disabled")

            self.candidates.append((name, vote_btn))

    def verify_usn(self):
        usn = self.usn_entry.get().strip()
        if  usn == "":
            messagebox.showwarning("Warning", "Please enter a USN.")
            return

        try:
            self.cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {self.username}_voters "
                f"(usn VARCHAR(50) PRIMARY KEY, vote_status BOOLEAN DEFAULT 0)"
            )
            self.conn.commit()

            self.cursor.execute(
                f"SELECT vote_status FROM {self.username}_voters WHERE usn=%s", (usn,)
            )
            result = self.cursor.fetchone()

            if result == None:
                messagebox.showerror("Error", "USN not found. You are not allowed to vote.")
                for hoho, btn in self.candidates:
                    btn.configure(state="disabled")
                return

            elif result[0] == 1:
                messagebox.showerror("Error", "You have already voted!")
                for _, btn in self.candidates:
                    btn.configure(state="disabled")
                return

            else:
                messagebox.showinfo("Welcome", "You may now vote.")
                self.current_usn = usn
                for _, btn in self.candidates:
                    btn.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {e}")
    

    def cast_vote(self, candidate_name):
        if  self.current_usn is None:
            messagebox.showwarning("Warning", "Please enter your USN first.")
            return

        try:
            self.cursor.execute(
                f"UPDATE {self.username}_voters SET vote_status=1 WHERE usn=%s",
                (self.current_usn,)
            )
            self.conn.commit()

            messagebox.showinfo("Vote Recorded", f"You voted for {candidate_name}")

            self.usn_entry.delete(0, "end")
            self.current_usn = None
            for _, btn in self.candidates:
                btn.configure(state="disabled")

            self.tkraise()

        except Exception as e:
            messagebox.showerror("Error", f"Could not record vote: {e}")


if __name__ == "__main__":
    app = VotingApp()
    app.mainloop()

