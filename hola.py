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

        self.user = "admin"
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

        self.page_detail = PageDetail(self.container, on_detailed=self.goto_bill)
        self.page_bill = PageBilling(self.container, self.menu,
                                     get_ids=lambda: (self.user, self.child),
                                     on_back=self.back_to_detail)

        for p in (self.page_detail, self.page_bill):
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show(self.page_detail)

    def show(self, page):
        page.tkraise()

    def goto_bill(self, child_id):
        self.child = child_id
        self.page_bill.reset()
        self.page_bill.update_header()
        self.show(self.page_bill)

    def back_to_detail(self):
        self.page_detail.reset()
        self.show(self.page_detail)


class PageDetail(ctk.CTkFrame):
    def __init__(self, parent, on_detailed):
        super().__init__(parent)
        self.on_detailed = on_detailed

        ctk.CTkLabel(self, text="Child ID").pack()

        row = ctk.CTkFrame(self)
        row.pack(pady=12)
        self.child = ctk.CTkEntry(row, placeholder_text="Child ID")
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
        self.on_detailed(cid)


class PageBilling(ctk.CTkFrame):
    def __init__(self, parent, menu, get_ids, on_back):
        super().__init__(parent)
        self.menu = menu
        self.get_ids = get_ids
        self.on_back = on_back

        self.title = ctk.CTkLabel(self, text="Billing", font=("Arial", 20))
        self.title.pack(pady=10)

        ctk.CTkButton(self, text="Back to Detail", command=self.on_back).pack(pady=4)

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
        for (name, price), g in zip(self.menu, self.qty_entries):
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
        for (name, price), g in zip(self.menu, self.qty_entries):
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

        data = {
            "user": u,
            "child": c,
            "total": total,
            "items": items,
            "time": datetime.now().isoformat(timespec="seconds"),
        }

        append_order(data)
        messagebox.showinfo("Success", "Order Saved")

        self.reset()
        self.total_label.configure(text="Total: ₹0")


if __name__ == "__main__":
    app = App()
    app.mainloop()

