import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import pickle


FNAME = "orders.dat"

def load_orders():
    try:
        with open(FNAME, "rb") as f:
            data = pickle.load(f)
        if type(data) is list:
            return data
    except Exception as e:
        print(e)
    return []

def save_orders(orders):
    with open(FNAME, "wb") as f:
        pickle.dump(orders, f)

def append_order(order):
    lst = load_orders()
    lst.append(order)
    save_orders(lst)


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Canteen")
        self.geometry("900x560")

        self.user = None
        self.child = None

        self.menu = [
            ("Idli (2)", 20),
            ("Dosa", 20),
            ("Vada Pav", 15),
            ("Samosa", 10),
            ("Veg Puff", 15),
            ("Tea", 10),
            ("Coffee", 10)
        ]

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.page_login = PageLogin(self.container, on_login=self.goto_scan)
        self.page_scan = PageScan(self.container, on_scanned=self.goto_bill)
        self.page_bill = PageBilling(self.container, self.menu,
                                     get_ids=lambda: (self.user, self.child),
                                     on_back=self.back_to_scan)

        for p in (self.page_login, self.page_scan, self.page_bill):
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show(self.page_login)

    def show(self, page):
        page.tkraise()

    def goto_scan(self, user):
        self.user = user
        self.page_scan.reset()
        self.show(self.page_scan)

    def goto_bill(self, child_id):
        self.child = child_id
        self.page_bill.reset()
        self.page_bill.update_header()
        self.show(self.page_bill)

    def back_to_scan(self):
        self.page_scan.reset()
        self.show(self.page_scan)


class PageLogin(ctk.CTkFrame):
    def __init__(self, parent, on_login):
        super().__init__(parent)
        self.on_login = on_login

        ctk.CTkLabel(self, text="Login", font=("Arial", 24)).pack(pady=20)
        self.username = ctk.CTkEntry(self, placeholder_text="Username")
        self.username.pack(padx=20, pady=8, fill="x")
        self.password= ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password.pack(padx=20, pady=8, fill="x")
        self.msg = ctk.CTkLabel(self, text="", text_color="red")
        self.msg.pack()

        ctk.CTkButton(self, text="Login", command=self.try_login).pack(pady=14)
        ctk.CTkLabel(self, text="Use admin / password").pack()

    def try_login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if u == "admin" and p == "password":
            self.on_login(u)
        else:
            self.msg.configure(text="Invalid username or password")


class PageScan(ctk.CTkFrame):
    def __init__(self, parent, on_scanned):
        super().__init__(parent)
        self.on_scanned = on_scanned

        ctk.CTkLabel(self, text="Scan Child QR (Demo)", font=("Arial", 20)).pack(pady=16)
        ctk.CTkLabel(self, text="Enter/paste Child ID from scanner").pack()

        row = ctk.CTkFrame(self)
        row.pack(pady=12)
        self.child= ctk.CTkEntry(row, placeholder_text="Child ID")
        self.child.pack(side="left", padx=6)
        ctk.CTkButton(row, text="Continue", command=self.use_id).pack(side="left")

        self.msg = ctk.CTkLabel(self, text="", text_color="red")
        self.msg.pack(pady=6)

    def reset(self):
        self.child.delete(0, "end")
        self.msg.configure(text="")

    def use_id(self):
        cid = self.child.get().strip()
        if cid == "":
            self.msg.configure(text="Enter a valid child ID")
            return
        self.on_scanned(cid)


class PageBilling(ctk.CTkFrame):
    def __init__(self, parent, menu, get_ids, on_back):
        super().__init__(parent)
        self.menu = menu
        self.get_ids = get_ids
        self.on_back = on_back

        self.title = ctk.CTkLabel(self, text="Billing", font=("Arial", 20))
        self.title.pack(pady=10)

        ctk.CTkButton(self, text="Back to Scan", command=self.on_back).pack(pady=4)

        self.body = ctk.CTkScrollableFrame(self)
        self.body.pack(fill="both", expand=True, padx=10, pady=10)

        self.qty_entries = []
        for name, price in self.menu:
            row = ctk.CTkFrame(self.body)
            row.pack(fill="x", padx=6, pady=6)
            ctk.CTkLabel(row, text=name).pack(side="left")
            ctk.CTkLabel(row, text="₹" + str(price)).pack(side="left", padx=10)
            ctk.CTkLabel(row, text="Qty").pack(side="left", padx=4)
            e = ctk.CTkEntry(row, width=70)
            e.insert(0, "0")
            e.pack(side="left")
            self.qty_entries.append(e)

        foot = ctk.CTkFrame(self)
        foot.pack(fill="x", padx=10, pady=(0, 10))
        self.total_label = ctk.CTkLabel(foot, text="Total: ₹0")
        self.total_label.pack(side="left")
        ctk.CTkButton(foot, text="Calculate", command=self.calculate).pack(side="left", padx=8)
        ctk.CTkButton(foot, text="Clear", command=self.clear_all).pack(side="left", padx=8)
        ctk.CTkButton(foot, text="Save", command=self.save_details).pack(side="right")

    def update_header(self):
        u, c = self.get_ids()
        if not u:
            u = "admin"
        if not c:
            c = "child"
        self.title.configure(text="Billing User: " + u + "     Child: " + c)

    def reset(self):
        for e in self.qty_entries:
            e.delete(0, "end")
            e.insert(0, "0")
        self.total_label.configure(text="Total: ₹0")

    def clear_all(self):
        self.reset()

    def calculate(self):
        total = 0
        for  (name,price),g in zip(self.menu, self.qty_entries):
            t = g.get().strip()
            if t == "":
                t = "0"
            try:
                q = int(t)
                if q < 0:
                    messagebox.showerror("Error", "Quantity cannot be negative for " + name)
                    return
                total += price * q
            except:
                messagebox.showerror("Error", "Enter integer quantity for " + name)
                return
        self.total_label.configure(text="Total: ₹" + str(total))

    def save_details(self):
        items = []
        total = 0
        for  (name, price),g  in zip(self.menu, self.qty_entries):
            t = g.get().strip()
            if t == "":
                t = "0"
            try:
                q = int(t)
            except:
                messagebox.showerror("Error", "Enter integer quantity for " + name)
                return
            if q < 0:
                messagebox.showerror("Error", "Quantity cannot be negative for " + name)
                return
            if q > 0:
                amount = price * q
                total += amount
                items.append({"name": name, "price": price, "qty": q, "amount": amount})

        if len(items) == 0:
            messagebox.showwarning("Empty", "All quantities are zero")
            return

        u, c = self.get_ids()
        if not u:
            u = "admin"
        if not c:
            c = "child"

        data = {
            "user": u,
            "child": c,
            "total": total,
            "items": items,
            "time": datetime.now().isoformat(timespec="seconds"),
        }
        
        append_order(data)
        
        messagebox.showinfo("Success","Order Saved")
        

        self.reset()
        self.total_label.configure(text="Total: ₹0")



if __name__ == "__main__":
    app = App()
    app.mainloop()

